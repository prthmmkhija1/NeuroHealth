# tests/test_data_pipeline.py

"""
Tests for the data pipeline modules:
- collector.py  →  collect_data() / run_data_collection()
- cleaner.py    →  run_cleaning()
- chunker.py    →  run_chunking()

Tests use temporary directories to avoid side-effects on real data/.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def test_collector(tmp_path):
    """Test that collector creates raw data files in a temp directory."""
    from src.data_pipeline.collector import collect_data

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()

    with patch("src.data_pipeline.collector.RAW_DATA_DIR", raw_dir):
        collect_data()

    files = list(raw_dir.glob("*.json"))
    assert len(files) > 0, "Should have at least one JSON file in data/raw"

    # Check structure of collected data
    for f in files:
        with open(f, encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, list), f"{f.name} should contain a list"
        if len(data) > 0:
            first = data[0]
            assert "question" in first or "title" in first or "content" in first, \
                f"{f.name} entries should have 'question', 'title', or 'content' field"

    print("✓ Collector test passed")


def test_cleaner(tmp_path):
    """Test that cleaner processes raw data in a temp directory."""
    from src.data_pipeline.cleaner import run_cleaning

    raw_dir = tmp_path / "raw"
    processed_dir = tmp_path / "processed"
    raw_dir.mkdir()
    processed_dir.mkdir()

    # Create sample raw data
    sample = [
        {"title": "Headache", "content": "A <b>headache</b> is pain in the head region. " * 5,
         "source": "test", "url": "https://example.com"},
        {"title": "Fever", "content": "Fever is an elevated body temperature above 100.4°F. " * 5,
         "source": "test", "url": "https://example.com"},
    ]
    with open(raw_dir / "test_topics.json", "w", encoding="utf-8") as f:
        json.dump(sample, f)

    with patch("src.data_pipeline.cleaner.RAW_DATA_DIR", raw_dir), \
         patch("src.data_pipeline.cleaner.PROCESSED_DATA_DIR", processed_dir):
        run_cleaning(force=True)

    cleaned_files = list(processed_dir.glob("cleaned_*.json"))
    assert len(cleaned_files) > 0, "Should have at least one cleaned_*.json file"

    for cf in cleaned_files:
        with open(cf) as f:
            data = json.load(f)
        assert isinstance(data, list), f"{cf.name} should contain a list"

    print("✓ Cleaner test passed")


def test_chunker(tmp_path):
    """Test that chunker creates text chunks from cleaned data."""
    from src.data_pipeline.chunker import run_chunking

    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()

    # Create sample cleaned data
    sample = [
        {"title": "Headache", "content": "A headache is pain in the head. " * 100,
         "source": "test"},
    ]
    with open(processed_dir / "cleaned_test.json", "w", encoding="utf-8") as f:
        json.dump(sample, f)

    with patch("src.data_pipeline.chunker.PROCESSED_DATA_DIR", processed_dir):
        run_chunking(force=True)

    chunks_path = processed_dir / "all_chunks.json"
    assert chunks_path.exists(), "all_chunks.json should exist after chunking"

    with open(chunks_path) as f:
        chunks = json.load(f)
    assert isinstance(chunks, list), "Chunks should be a list"
    assert len(chunks) > 0, "Should have at least one chunk"

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


def test_clean_document_preserves_metadata():
    """Test that clean_document preserves metadata fields verbatim."""
    from src.data_pipeline.cleaner import clean_document

    doc = {
        "title": "<b>Test Title</b>",
        "content": "<p>Some medical content</p>",
        "source": "MedlinePlus",
        "url": "https://medlineplus.gov/ency?art=000123",
        "data_type": "health_topic",
        "category": "cardiac",
    }
    cleaned = clean_document(doc)

    # Metadata fields should be preserved exactly
    assert cleaned["source"] == "MedlinePlus"
    assert cleaned["url"] == "https://medlineplus.gov/ency?art=000123"
    assert cleaned["data_type"] == "health_topic"
    assert cleaned["category"] == "cardiac"
    # Content fields should be cleaned
    assert "<b>" not in cleaned["title"]
    assert "<p>" not in cleaned["content"]

    print("✓ Clean document metadata preservation test passed")


if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        test_collector(tmp / "collector")
        test_cleaner(tmp / "cleaner")
        test_chunker(tmp / "chunker")
    test_clean_text_preserves_medical()
    test_clean_document_preserves_metadata()
    print("\n✅ All data pipeline tests passed!")
