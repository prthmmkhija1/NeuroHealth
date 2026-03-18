# Knowledge Base Module
# Embedding and vector store for medical knowledge retrieval.

from src.knowledge_base.embedder import embed_all_chunks, get_embedder
from src.knowledge_base.vector_store import (build_vector_store,
                                             get_vector_store,
                                             search_knowledge_base)

__all__ = [
    "get_embedder",
    "embed_all_chunks",
    "build_vector_store",
    "get_vector_store",
    "search_knowledge_base",
]
