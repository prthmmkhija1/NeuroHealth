# tests/conftest.py

"""
Pytest configuration and shared fixtures for NeuroHealth tests.
"""

import json
import sys
from pathlib import Path

import pytest

# Ensure the project root is on the path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Shared Helpers ───────────────────────────────────────────────────


def vector_store_ready() -> bool:
    """Return True only if the medical_knowledge collection exists in ChromaDB."""
    try:
        import chromadb

        client = chromadb.PersistentClient(path=str(Path("data/vector_db")))
        names = [c.name for c in client.list_collections()]
        return "medical_knowledge" in names
    except Exception:
        return False


def hf_token_available() -> bool:
    """Return True only if a real HuggingFace token is configured in the environment."""
    import os

    from dotenv import load_dotenv

    load_dotenv()
    token = os.getenv("HUGGINGFACE_TOKEN", "")
    return bool(token) and not token.startswith("hf_YOUR")


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


# ── Shared Fixtures ──────────────────────────────────────────────────


@pytest.fixture
def sample_user_messages():
    """Common user messages for testing across modules."""
    return {
        "emergency": "I'm having crushing chest pain radiating to my left arm and sweating",
        "urgent": "I have a fever of 103°F that has lasted 3 days",
        "routine": "I have a runny nose and mild headache since yesterday",
        "self_care": "I have a small paper cut on my finger",
        "mental_health": "I've been feeling very depressed and hopeless for weeks",
        "out_of_scope": "What is the capital of France?",
        "empty": "",
        "ambiguous": "My stomach hurts",
    }


@pytest.fixture
def tmp_data_dir(tmp_path):
    """Provides a temporary directory structure mimicking data/."""
    raw = tmp_path / "raw"
    processed = tmp_path / "processed"
    vector_db = tmp_path / "vector_db"
    raw.mkdir()
    processed.mkdir()
    vector_db.mkdir()
    return {
        "root": tmp_path,
        "raw": raw,
        "processed": processed,
        "vector_db": vector_db,
    }


@pytest.fixture
def sample_raw_documents(tmp_data_dir):
    """Creates sample raw documents in the temp data directory."""
    docs = [
        {
            "title": "Headache",
            "content": "A headache is pain or discomfort in the head or face area. "
            "Headaches can be primary (tension, migraine) or secondary "
            "(caused by another condition). Treatment depends on the type.",
            "source": "test_source",
            "url": "https://example.com/headache",
        },
        {
            "title": "Diabetes",
            "content": "Diabetes is a chronic condition that affects how your body "
            "turns food into energy. Type 2 diabetes is the most common form. "
            "Blood sugar monitoring and lifestyle changes are key.",
            "source": "test_source",
            "url": "https://example.com/diabetes",
        },
    ]
    path = tmp_data_dir["raw"] / "test_health_topics.json"
    with open(path, "w") as f:
        json.dump(docs, f)
    return docs


@pytest.fixture
def conversation_manager():
    """Provides a fresh ConversationManager instance."""
    from src.modules.conversation_manager import ConversationManager

    return ConversationManager()
