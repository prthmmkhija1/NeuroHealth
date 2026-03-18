# src/data_pipeline/chunker.py

"""
Text Chunker Module
-------------------
AI models can only look at a limited amount of text at once (called "context window").
We split long medical articles into small, overlapping pieces (chunks).

"Overlapping" means consecutive chunks share some sentences — so we don't lose
context at the boundary between chunks.

Example:
  Original text: [Sentence 1. Sentence 2. Sentence 3. Sentence 4. Sentence 5.]
  Chunk 1:       [Sentence 1. Sentence 2. Sentence 3.]
  Chunk 2:                    [Sentence 2. Sentence 3. Sentence 4.]  ← overlaps!
  Chunk 3:                                 [Sentence 3. Sentence 4. Sentence 5.]
"""

import hashlib
import json
import sys
from pathlib import Path

PROCESSED_DATA_DIR = Path("data/processed")

# OSRE spec: "overlapping windows 256–512 tokens"
# We approximate tokens ≈ words (avg 1.3 tokens/word for English medical text).
# 512 tokens ≈ ~400 words ≈ ~2400 characters; 256 tokens ≈ ~200 words ≈ ~1200 chars.
# Using character-level slicing with sentence-boundary snapping:
CHUNK_SIZE = 2400  # ~512 tokens per chunk  (spec upper bound)
CHUNK_OVERLAP = 300  # ~50-token overlap to preserve cross-chunk context


def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Splits a long text string into overlapping chunks.

    Args:
        text: The long text to split
        chunk_size: How many characters per chunk (~2400 chars ≈ 512 tokens)
        overlap: How many characters to share between chunks (~300 chars ≈ 50 tokens)

    Returns: list of text strings
    """
    if not text or len(text) <= chunk_size:
        return [text] if text else []

    chunks = []
    start = 0

    while start < len(text):
        end = start + chunk_size

        # Try to end the chunk at a sentence boundary (period, ?, !)
        if end < len(text):
            last_period = max(
                text.rfind(". ", start, end),
                text.rfind("? ", start, end),
                text.rfind("! ", start, end),
            )
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = text[start:end].strip()
        # Only keep chunk if it has meaningful content (avoids tiny overlap tails)
        if len(chunk) >= 20:
            chunks.append(chunk)

        # Move forward, but back up by 'overlap' characters
        start = end - overlap

    return chunks


def chunk_document(doc):
    """
    Takes a document and returns multiple chunk documents.
    Each chunk keeps all the metadata (source, title, etc.) from the original.
    """
    content = doc.get("content", "")
    chunks = split_into_chunks(content)

    chunk_docs = []
    for i, chunk in enumerate(chunks):
        # Build a unique chunk_id: title + source-hash + index
        title_slug = doc.get("title", "unknown").replace(" ", "_")[:60]
        source_hash = hashlib.md5(  # nosec B324 - used for deduplication, not security
            doc.get("source", "").encode(), usedforsecurity=False
        ).hexdigest()[:6]
        chunk_id = f"{title_slug}_{source_hash}_{i}"

        chunk_doc = {
            "chunk_id": chunk_id,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "content": chunk,
            "title": doc.get("title", ""),
            "source": doc.get("source", ""),
            "url": doc.get("url", ""),
            # Support both old and new collector output fields
            "topic": doc.get("topic", ""),
            "urgency": doc.get("urgency", ""),
            "category": doc.get("category", ""),
            "categories": doc.get("categories", []),
            "data_type": doc.get("data_type", ""),
            "also_called": doc.get("also_called", []),
        }
        chunk_docs.append(chunk_doc)

    return chunk_docs


def run_chunking(force=False):
    """Main function — chunks all cleaned documents.

    Args:
        force: If True, re-chunk and overwrite all_chunks.json even if it exists.
               If False (default), skip chunking if all_chunks.json already exists.
    """
    print("=" * 50)
    print("Starting Text Chunking Pipeline")
    if force:
        print("Mode: FORCE — all_chunks.json will be overwritten")
    else:
        print(
            "Mode: INCREMENTAL — skips if all_chunks.json already exists (use --force to re-chunk)"
        )
    print("=" * 50)

    output_path = PROCESSED_DATA_DIR / "all_chunks.json"
    if not force and output_path.exists():
        import json as _json

        with open(output_path, encoding="utf-8") as f:
            existing = _json.load(f)
        print(
            f"\nSkipping — all_chunks.json already exists ({len(existing)} chunks). Use --force to re-chunk."
        )
        return

    cleaned_files = list(PROCESSED_DATA_DIR.glob("cleaned_*.json"))

    if not cleaned_files:
        print("No cleaned data files found. Run cleaner.py first.")
        return

    all_chunks = []

    for cleaned_file in cleaned_files:
        print(f"\nChunking: {cleaned_file.name}")

        with open(cleaned_file, "r", encoding="utf-8") as f:
            documents = json.load(f)

        file_chunks = []
        for doc in documents:
            chunks = chunk_document(doc)
            file_chunks.extend(chunks)

        print(f"  Documents: {len(documents)} → Chunks: {len(file_chunks)}")
        all_chunks.extend(file_chunks)

    # Save all chunks together
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\nTotal chunks created: {len(all_chunks)}")
    print(f"Saved to: {output_path}")
    print("\nChunking complete!")


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    run_chunking(force=force)
