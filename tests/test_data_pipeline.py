# tests/test_data_pipeline.py

"""
Tests for the data pipeline modules:
- collector.py  →  collect_data() / run_data_collection()
- cleaner.py    →  run_cleaning()
- chunker.py    →  run_chunking()
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
            first = data[0]
            assert "question" in first or "title" in first or "content" in first, \
                f"{f.name} entries should have 'question', 'title', or 'content' field"

    print("✓ Collector test passed")


def test_cleaner():
    """Test that cleaner processes raw data."""
    from src.data_pipeline.cleaner import run_cleaning

    run_cleaning()

    processed_dir = Path("data/processed")
    assert processed_dir.exists(), "data/processed directory should exist after cleaning"

    cleaned_files = list(processed_dir.glob("cleaned_*.json"))
    assert len(cleaned_files) > 0, "Should have at least one cleaned_*.json file"

    for cf in cleaned_files:
        with open(cf) as f:
            data = json.load(f)
        assert isinstance(data, list), f"{cf.name} should contain a list"

    print("✓ Cleaner test passed")


def test_chunker():
    """Test that chunker creates text chunks."""
    from src.data_pipeline.chunker import run_chunking

    run_chunking()

    chunks_path = Path("data/processed/all_chunks.json")
    assert chunks_path.exists(), "all_chunks.json should exist after chunking"

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


def test_clean_text_preserves_medical():
    """Test that cleaning preserves medical characters like °, %, /."""
    from src.data_pipeline.cleaner import clean_text

    assert "°" in clean_text("fever of 103°F"), "Should preserve degree symbol"
    assert "%" in clean_text("95% oxygen saturation"), "Should preserve percent"
    assert "/" in clean_text("blood pressure 120/80"), "Should preserve slash"

    print("✓ Clean text medical preservation test passed")


if __name__ == "__main__":
    test_collector()
    test_cleaner()
    test_chunker()
    test_clean_text_preserves_medical()
    print("\n✅ All data pipeline tests passed!")
