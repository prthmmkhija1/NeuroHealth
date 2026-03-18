# src/knowledge_base/embedder.py

"""
Text Embedder Module
--------------------
Converts text into vectors (lists of numbers).
These vectors capture the "meaning" of the text.
Similar meaning = similar vectors = close together in the database.

We use a free local model (sentence-transformers all-MiniLM-L6-v2).
Zero API cost — runs entirely on your machine or the A100 GPU.
"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROCESSED_DATA_DIR = Path("data/processed")


def get_embedder():
    """
    Returns an embedding function using the free local model.
    Uses sentence-transformers (all-MiniLM-L6-v2) — zero API cost.

    On HP-INT (no GPU): Works, slightly slower (CPU).
    On JLAB-GPU (A100): Extremely fast.
    """
    from sentence_transformers import SentenceTransformer

    model_name = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    print(f"Loading local embedding model ({model_name})...")
    model = SentenceTransformer(model_name)

    def embed(texts):
        """Embeds a list of text strings into vectors."""
        embeddings = model.encode(texts, show_progress_bar=True, batch_size=32)
        return embeddings.tolist()

    return embed


def embed_all_chunks():
    """
    Loads all chunks and embeds them.
    Returns: chunks with their embeddings added.
    """
    chunks_path = PROCESSED_DATA_DIR / "all_chunks.json"

    if not chunks_path.exists():
        print("No chunks found. Run chunker.py first.")
        return []

    with open(chunks_path, "r") as f:
        chunks = json.load(f)

    print(f"Embedding {len(chunks)} chunks...")

    # Get embedding function
    embedder = get_embedder()

    # Extract just the text content
    texts = [chunk["content"] for chunk in chunks]

    # Generate embeddings
    embeddings = embedder(texts)

    # Add embeddings to chunks
    for chunk, embedding in zip(chunks, embeddings):
        chunk["embedding"] = embedding

    # Save chunks+embeddings
    output_path = PROCESSED_DATA_DIR / "embedded_chunks.json"
    with open(output_path, "w") as f:
        json.dump(chunks, f)

    print(f"Saved embedded chunks to {output_path}")
    return chunks


if __name__ == "__main__":
    embed_all_chunks()
