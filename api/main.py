# api/main.py

"""
NeuroHealth FastAPI Backend
----------------------------
REST API for NeuroHealth — allows any frontend or mobile app
to call NeuroHealth over HTTP.

To run: uvicorn api.main:app --reload --port 8000
API documentation at: http://localhost:8000/docs
"""

import sys
from pathlib import Path

# Add parent directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router

app = FastAPI(
    title="NeuroHealth API",
    description=(
        "AI-Powered Health Assistant API — provides symptom assessment, "
        "urgency triage, appointment recommendations, and health guidance "
        "powered by RAG and local LLMs.\n\n"
        "**Disclaimer:** NeuroHealth is NOT a substitute for professional medical advice."
    ),
    version="1.0.0",
    license_info={
        "name": "CC BY 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    contact={
        "name": "NeuroHealth (OSRE 2026)",
        "url": "https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/",
    },
)

# Allow cross-origin requests (for web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["NeuroHealth"])


@app.get("/", tags=["Meta"])
def root():
    """Service info and health check."""
    return {
        "name": "NeuroHealth API",
        "version": "1.0.0",
        "status": "running",
        "description": "AI-Powered Health Assistant",
        "docs": "/docs",
        "endpoints": {
            "chat": "/api/v1/chat",
            "chat_stream": "/api/v1/chat/stream",
            "sessions": "/api/v1/sessions",
            "feedback": "/api/v1/feedback",
            "feedback_summary": "/api/v1/feedback/summary",
        },
    }


@app.get("/health", tags=["Meta"])
def health_check():
    """Liveness probe for container orchestration."""
    return {"status": "healthy"}
