# tests/test_data_pipeline.py

"""
Tests for the data pipeline modules:
- collector.py
- cleaner.py
- chunker.py
"""

import json
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_collector():
    """Test that collector creates raw data files."""
    from src.data_pipeline.collector import collect_data

    collect_data()

    raw_dir = Path("data/raw")
    assert raw_dir.exists(), "data/raw directory should exist after collection"

    files = list(raw_dir.glob("*.json"))
    assert len(files) > 0, "Should have at least one JSON file in data/raw"

    # Check structure of collected data
    for f in files:
        with open(f) as fh:
            data = json.load(fh)
        assert isinstance(data, list), f"{f.name} should contain a list"
        if len(data) > 0:
            assert "question" in data[0] or "title" in data[0], \
                f"{f.name} entries should have 'question' or 'title' field"

    print("✓ Collector test passed")


def test_cleaner():
    """Test that cleaner processes raw data."""
    from src.data_pipeline.cleaner import clean_data

    clean_data()

    cleaned_path = Path("data/processed/cleaned_data.json")
    assert cleaned_path.exists(), "cleaned_data.json should exist after cleaning"

    with open(cleaned_path) as f:
        data = json.load(f)
    assert isinstance(data, list), "Cleaned data should be a list"
    assert len(data) > 0, "Cleaned data should not be empty"

    print("✓ Cleaner test passed")


def test_chunker():
    """Test that chunker creates text chunks."""
    from src.data_pipeline.chunker import chunk_data

    chunk_data()

    chunks_path = Path("data/processed/chunks.json")
    assert chunks_path.exists(), "chunks.json should exist after chunking"

    with open(chunks_path) as f:
        chunks = json.load(f)
    assert isinstance(chunks, list), "Chunks should be a list"
    assert len(chunks) > 0, "Should have at least one chunk"

    # Check chunk structure
    first = chunks[0]
    assert "chunk_id" in first, "Chunks should have chunk_id"
    assert "content" in first, "Chunks should have content"
    assert len(first["content"]) > 0, "Chunk content should not be empty"

    print("✓ Chunker test passed")


if __name__ == "__main__":
    test_collector()
    test_cleaner()
    test_chunker()
    print("\n✅ All data pipeline tests passed!")
