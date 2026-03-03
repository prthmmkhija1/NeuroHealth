# api/main.py

"""
NeuroHealth FastAPI Backend
----------------------------
REST API for NeuroHealth — allows any frontend or mobile app
to call NeuroHealth over HTTP.

To run: uvicorn api.main:app --reload --port 8000
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
    description="AI-Powered Health Assistant API",
    version="1.0.0",
)

# Allow cross-origin requests (for web frontends)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "NeuroHealth API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}
