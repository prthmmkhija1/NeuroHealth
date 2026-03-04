# src/knowledge_base/vector_store.py

"""
Vector Store Module
-------------------
Stores all embedded medical knowledge in ChromaDB.
ChromaDB is a database that can search by meaning (semantic search).

After building the vector store, we can ask:
"Find me everything related to chest pain symptoms"
And it returns the most relevant medical chunks — even if the exact words don't match.
"""

import os
import json
import hashlib
from pathlib import Path
import chromadb
from dotenv import load_dotenv

load_dotenv()

PROCESSED_DATA_DIR = Path("data/processed")
VECTOR_DB_PATH = os.getenv("VECTOR_DB_PATH", "./data/vector_db")

# Singleton embedding model for search (avoid reloading on every query)
_search_model = None


def build_vector_store():
    """
    Builds the ChromaDB vector store from embedded chunks.
    This only needs to be run ONCE (or when you add new medical data).
    """
    print("=" * 50)
    print("Building Vector Store")
    print("=" * 50)

    # Load embedded chunks
    embedded_path = PROCESSED_DATA_DIR / "embedded_chunks.json"
    if not embedded_path.exists():
        print("No embedded chunks found. Run embedder.py first.")
        return

    with open(embedded_path, "r") as f:
        chunks = json.load(f)

    # Deduplicate chunk IDs (in case of collisions)
    seen_ids = set()
    deduped_chunks = []
    for chunk in chunks:
        cid = chunk["chunk_id"]
        if cid in seen_ids:
            # Append a hash suffix to make unique
            suffix = hashlib.md5(chunk["content"][:100].encode()).hexdigest()[:8]
            cid = f"{cid}_{suffix}"
            chunk["chunk_id"] = cid
        seen_ids.add(cid)
        deduped_chunks.append(chunk)
    chunks = deduped_chunks

    print(f"Loading {len(chunks)} chunks into ChromaDB...")

    # Create ChromaDB client (persistent — saves to disk)
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)

    # Delete existing collection if it exists (to rebuild fresh)
    try:
        client.delete_collection("medical_knowledge")
        print("Deleted old collection")
    except Exception:
        pass

    # Create a new collection
    collection = client.create_collection(
        name="medical_knowledge",
        metadata={"description": "NeuroHealth medical knowledge base"},
    )

    # Insert chunks in batches
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]

        collection.add(
            ids=[chunk["chunk_id"] for chunk in batch],
            embeddings=[chunk["embedding"] for chunk in batch],
            documents=[chunk["content"] for chunk in batch],
            metadatas=[{
                "title": chunk.get("title", ""),
                "source": chunk.get("source", ""),
                "topic": chunk.get("topic", ""),
                "urgency": chunk.get("urgency", ""),
                "category": chunk.get("category", ""),
                "data_type": chunk.get("data_type", ""),
            } for chunk in batch]
        )

        print(f"Inserted {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    print(f"\nVector store built successfully!")
    print(f"Location: {VECTOR_DB_PATH}")
    print(f"Total chunks: {collection.count()}")


def get_vector_store():
    """
    Loads the existing vector store.
    Call this function whenever you need to search the knowledge base.

    Raises:
        RuntimeError: If the medical_knowledge collection has not been built yet.
    """
    client = chromadb.PersistentClient(path=VECTOR_DB_PATH)
    try:
        collection = client.get_collection("medical_knowledge")
    except Exception as e:
        raise RuntimeError(
            "Vector store not built yet. Run the data pipeline first:\n"
            "  python src/data_pipeline/collector.py\n"
            "  python src/data_pipeline/cleaner.py\n"
            "  python src/data_pipeline/chunker.py\n"
            "  python src/knowledge_base/embedder.py\n"
            "  python src/knowledge_base/vector_store.py"
        ) from e
    return collection


def search_knowledge_base(query, n_results=5):
    """
    Searches the medical knowledge base for documents relevant to the query.

    Args:
        query: The user's question (e.g., "I have chest pain and trouble breathing")
        n_results: How many relevant chunks to return

    Returns: list of relevant text chunks
    """
    collection = get_vector_store()

    # Singleton embedding model—loaded once, reused on every search
    global _search_model
    if _search_model is None:
        from sentence_transformers import SentenceTransformer
        _search_model = SentenceTransformer(
            os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        )

    query_embedding = _search_model.encode([query]).tolist()[0]

    # Search the collection
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )

    # Format results nicely
    retrieved_docs = []
    for i, (doc, metadata) in enumerate(zip(
        results["documents"][0],
        results["metadatas"][0]
    )):
        retrieved_docs.append({
            "rank": i + 1,
            "content": doc,
            "source": metadata.get("source", ""),
            "title": metadata.get("title", ""),
            "category": metadata.get("category", ""),
        })

    return retrieved_docs


if __name__ == "__main__":
    # Build the vector store
    build_vector_store()

    # Test a search
    print("\nTesting search...")
    results = search_knowledge_base("I have a fever and sore throat")
    for r in results:
        print(f"\nResult {r['rank']}: {r['title']} ({r['source']})")
        print(f"  {r['content'][:200]}...")
