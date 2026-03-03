# src/rag/retriever.py

"""
Retriever Module
----------------
When the user sends a message, we don't just send it straight to the AI.
First, we search our medical knowledge base for relevant information.
Then we give both the question AND the retrieved info to the AI.
This way, the AI's answer is based on real medical documents, not guesswork.
"""

from src.knowledge_base.vector_store import search_knowledge_base


def retrieve_context(user_message, n_results=5):
    """
    Given a user message, retrieves relevant medical documents.

    Args:
        user_message: What the user typed (e.g., "I have chest pain")
        n_results: How many documents to retrieve

    Returns: A formatted string of retrieved context
    """
    print(f"Retrieving context for: '{user_message[:100]}...'")

    docs = search_knowledge_base(
        query=user_message,
        n_results=n_results,
    )

    if not docs:
        return "No relevant medical information found in the knowledge base."

    # Format the retrieved docs into a readable context string
    context_parts = []
    for doc in docs:
        part = f"""
--- Source: {doc['title']} ({doc['source']}) ---
{doc['content']}
"""
        context_parts.append(part)

    context = "\n".join(context_parts)
    return context


if __name__ == "__main__":
    context = retrieve_context("I have a headache and stiff neck")
    print(context)
