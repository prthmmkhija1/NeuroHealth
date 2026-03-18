# api/routes.py

"""
API Routes for NeuroHealth
---------------------------
REST endpoints for the NeuroHealth health assistant.

Endpoints:
  POST /chat              — Send a message and receive health guidance
  POST /chat/stream       — SSE streaming version for real-time responses
  GET  /sessions/{id}     — Retrieve conversation history for a session
  GET  /sessions          — List all active session IDs
  DELETE /sessions/{id}   — Delete a session
  POST /feedback          — Submit user satisfaction feedback
  GET  /feedback/summary  — Get aggregated satisfaction metrics
"""

import asyncio
import json
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.pipeline import active_sessions, process_message

router = APIRouter()

# In-memory feedback store (swap for a database in production)
_feedback_store: List[dict] = []


# ── Request / Response Models ──────────────────────────────────────────


class ChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The user's health question or symptom description",
    )
    session_id: Optional[str] = Field(
        None, description="Session ID for multi-turn conversation continuity"
    )


class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    urgency_level: str
    urgency_color: str


class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    message_count: int


class FeedbackRequest(BaseModel):
    session_id: Optional[str] = Field(
        None, description="Session ID the feedback relates to"
    )
    rating: int = Field(..., ge=1, le=5, description="Satisfaction rating 1-5")
    thumbs: Optional[str] = Field(None, description="Quick feedback: 'up' or 'down'")
    comment: Optional[str] = Field(
        None, max_length=2000, description="Optional free-text comment"
    )


# ── Endpoints ──────────────────────────────────────────────────────────


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a message to NeuroHealth and get a health assistant response.
    Include session_id for multi-turn conversations.
    """
    try:
        result = process_message(
            user_message=request.message,
            session_id=request.session_id,
        )

        return ChatResponse(
            session_id=result["session_id"],
            response_text=result["response"]["text"],
            urgency_level=result["response"]["urgency_level"],
            urgency_color=result["response"]["urgency_color"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    SSE (Server-Sent Events) streaming endpoint for real-time responses.
    Sends the response in chunks suitable for mobile/web clients that
    want progressive rendering.

    Content-Type: text/event-stream
    Each SSE event is a JSON object with type: 'token' | 'metadata' | 'done'.
    """

    async def _event_generator():
        try:
            # Run blocking LLM pipeline in a thread to avoid blocking the event loop
            result = await asyncio.to_thread(
                process_message,
                user_message=request.message,
                session_id=request.session_id,
            )

            response_text = result["response"]["text"]
            urgency_level = result["response"]["urgency_level"]
            session_id = result["session_id"]

            # Send metadata first
            meta = {
                "type": "metadata",
                "session_id": session_id,
                "urgency_level": urgency_level,
                "urgency_color": result["response"]["urgency_color"],
            }
            yield f"data: {json.dumps(meta)}\n\n"
            await asyncio.sleep(0)

            # Stream response text in word-sized chunks
            words = response_text.split(" ")
            chunk_size = 4  # words per chunk
            for i in range(0, len(words), chunk_size):
                chunk = " ".join(words[i : i + chunk_size])
                # Add trailing space unless last chunk
                if i + chunk_size < len(words):
                    chunk += " "
                token_event = {"type": "token", "text": chunk}
                yield f"data: {json.dumps(token_event)}\n\n"
                await asyncio.sleep(0.02)  # small delay for realistic streaming

            # Done signal
            done_event = {"type": "done", "session_id": session_id}
            yield f"data: {json.dumps(done_event)}\n\n"

        except Exception as e:
            error_event = {"type": "error", "detail": str(e)[:300]}
            yield f"data: {json.dumps(error_event)}\n\n"

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Retrieve conversation history for a session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    session = active_sessions[session_id]
    return session.to_dict()


@router.get("/sessions", response_model=List[SessionInfo])
def list_sessions():
    """List all active sessions."""
    sessions = []
    for sid, session in active_sessions.items():
        sessions.append(
            SessionInfo(
                session_id=sid,
                created_at=str(session.created_at),
                message_count=session.message_count,
            )
        )
    return sessions


@router.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Delete a conversation session."""
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    del active_sessions[session_id]
    return {"status": "deleted", "session_id": session_id}


# ── Feedback Endpoints ─────────────────────────────────────────────


@router.post("/feedback")
def submit_feedback(request: FeedbackRequest):
    """
    Submit user satisfaction feedback for a conversation.
    Used for CSAT / MOS tracking per OSRE evaluation spec.
    """
    entry = {
        "session_id": request.session_id,
        "rating": request.rating,
        "thumbs": request.thumbs,
        "comment": request.comment,
        "timestamp": datetime.now().isoformat(),
    }
    _feedback_store.append(entry)
    return {"status": "received", "feedback_count": len(_feedback_store)}


@router.get("/feedback/summary")
def feedback_summary():
    """
    Aggregate satisfaction metrics.
    Returns average rating (CSAT), thumbs distribution, and total count.
    """
    if not _feedback_store:
        return {"total": 0, "average_rating": None, "thumbs_up": 0, "thumbs_down": 0}

    ratings = [f["rating"] for f in _feedback_store]
    thumbs_up = sum(1 for f in _feedback_store if f.get("thumbs") == "up")
    thumbs_down = sum(1 for f in _feedback_store if f.get("thumbs") == "down")

    return {
        "total": len(_feedback_store),
        "average_rating": round(sum(ratings) / len(ratings), 2),
        "thumbs_up": thumbs_up,
        "thumbs_down": thumbs_down,
        "csat_score": round(sum(1 for r in ratings if r >= 4) / len(ratings) * 100, 1),
    }
