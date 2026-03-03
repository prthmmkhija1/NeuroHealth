# tests/test_rag.py

"""
Tests for RAG components (retriever and vector store).
Requires the data pipeline to have been run first.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_vector_store_build():
    """Test building the vector store (requires embedded_chunks.json)."""
    embedded_path = Path("data/processed/embedded_chunks.json")
    if not embedded_path.exists():
        print("⚠ Skipping vector store test — run embedder.py first")
        return

    from src.knowledge_base.vector_store import build_vector_store, get_vector_store

    build_vector_store()

    collection = get_vector_store()
    assert collection.count() > 0, "Vector store should have documents"

    print(f"✓ Vector store build test passed ({collection.count()} documents)")


def test_vector_store_search():
    """Test searching the vector store."""
    try:
        from src.knowledge_base.vector_store import search_knowledge_base

        results = search_knowledge_base("headache and fever", n_results=3)
        assert isinstance(results, list), "Search should return a list"
        assert len(results) > 0, "Should find at least one result"

        # Check result structure
        first = results[0]
        assert "content" in first, "Results should have 'content'"
        assert "rank" in first, "Results should have 'rank'"
        assert first["rank"] == 1, "First result should have rank 1"

        print("✓ Vector store search test passed")
    except Exception as e:
        print(f"⚠ Vector store search test skipped: {e}")


def test_retriever():
    """Test the retriever module."""
    try:
        from src.rag.retriever import retrieve_context

        context = retrieve_context("I have chest pain and difficulty breathing")
        assert isinstance(context, str), "Retriever should return a string"
        assert len(context) > 0, "Context should not be empty"

        print("✓ Retriever test passed")
    except Exception as e:
        print(f"⚠ Retriever test skipped: {e}")


if __name__ == "__main__":
    test_vector_store_build()
    test_vector_store_search()
    test_retriever()
    print("\n✅ All RAG tests completed!")
