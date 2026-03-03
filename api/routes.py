# api/routes.py

"""
API Routes for NeuroHealth
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from src.pipeline import process_message

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response_text: str
    urgency_level: str
    urgency_color: str


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Send a message to NeuroHealth and get a response.
    Include session_id for multi-turn conversations.
    """
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


@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    """Get conversation history for a session."""
    from src.pipeline import active_sessions

    if session_id not in active_sessions:
        return {"error": "Session not found"}

    session = active_sessions[session_id]
    return session.to_dict()
