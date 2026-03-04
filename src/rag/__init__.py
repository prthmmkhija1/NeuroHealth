# RAG (Retrieval-Augmented Generation) Module
# Retrieves relevant medical knowledge and generates grounded responses.

from src.rag.retriever import retrieve_context
from src.rag.generator import generate_response

__all__ = ["retrieve_context", "generate_response"]
