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

import json
from pathlib import Path

PROCESSED_DATA_DIR = Path("data/processed")
CHUNK_SIZE = 512         # Each chunk is roughly 512 characters (about 100 words)
CHUNK_OVERLAP = 50       # Each chunk shares 50 characters with the previous one


def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Splits a long text string into overlapping chunks.

    Args:
        text: The long text to split
        chunk_size: How many characters per chunk
        overlap: How many characters to share between chunks

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
                text.rfind('. ', start, end),
                text.rfind('? ', start, end),
                text.rfind('! ', start, end)
            )
            if last_period > start + chunk_size // 2:
                end = last_period + 1

        chunk = text[start:end].strip()
        if chunk:
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
        chunk_doc = {
            "chunk_id": f"{doc.get('title', 'unknown')}_{i}",
            "chunk_index": i,
            "total_chunks": len(chunks),
            "content": chunk,
            "title": doc.get("title", ""),
            "source": doc.get("source", ""),
            "topic": doc.get("topic", ""),
            "url": doc.get("url", ""),
            "urgency": doc.get("urgency", ""),
            "category": doc.get("category", ""),
        }
        chunk_docs.append(chunk_doc)

    return chunk_docs


def run_chunking():
    """Main function — chunks all cleaned documents."""
    print("=" * 50)
    print("Starting Text Chunking Pipeline")
    print("=" * 50)

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
    output_path = PROCESSED_DATA_DIR / "all_chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\nTotal chunks created: {len(all_chunks)}")
    print(f"Saved to: {output_path}")
    print("\nChunking complete!")


if __name__ == "__main__":
    run_chunking()
