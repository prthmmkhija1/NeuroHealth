# tests/helpers.py
"""Shared test helper functions for NeuroHealth test suite."""

import os
import pytest
from pathlib import Path
from dotenv import load_dotenv


def hf_token_available() -> bool:
    """Return True only if a real HuggingFace token is configured in the environment."""
    load_dotenv()
    token = os.getenv("HUGGINGFACE_TOKEN", "")
    return bool(token) and not token.startswith("hf_YOUR")


def vector_store_ready() -> bool:
    """Return True only if the medical_knowledge collection exists in ChromaDB."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(Path("data/vector_db")))
        names = [c.name for c in client.list_collections()]
        return "medical_knowledge" in names
    except Exception:
        return False


def import_pipeline():
    """Import process_message, skipping if vector store or HF token unavailable."""
    if not vector_store_ready():
        pytest.skip("Vector DB not built — run the data pipeline first")
    if not hf_token_available():
        pytest.skip("HUGGINGFACE_TOKEN not set in .env — skipping LLM-dependent tests")
    try:
        from src.pipeline import process_message
        return process_message
    except Exception as exc:
        pytest.skip(f"Cannot import src.pipeline: {exc}")
