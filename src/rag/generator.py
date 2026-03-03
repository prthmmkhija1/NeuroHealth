# src/rag/generator.py

"""
Response Generator Module
-------------------------
This is where the LLM generates the final response.
We send it:
  1. A system prompt (instructions for how to behave as a health assistant)
  2. The retrieved medical context
  3. The user's message

ADAPTED: Uses local Llama via llm_utils instead of OpenAI/Anthropic APIs.
"""

from src.llm_utils import generate_with_history


# =====================================================
# SYSTEM PROMPT — This defines how NeuroHealth behaves
# Think of this as the "personality and rules" of the AI
# =====================================================
SYSTEM_PROMPT = """You are NeuroHealth, a safe and helpful AI health assistant.

YOUR ROLE:
- Help users understand their symptoms and health concerns
- Provide general health information and guidance
- Recommend appropriate levels of care (emergency, urgent, routine)
- Ask clarifying questions when you need more information

CRITICAL SAFETY RULES (ALWAYS FOLLOW THESE):
1. Always tell users to call 911 or go to the Emergency Room for life-threatening symptoms
2. NEVER diagnose diseases — you can describe possibilities but never give a definitive diagnosis
3. Always recommend seeing a real doctor for any serious concern
4. If you are unsure, say so clearly and recommend professional consultation
5. Never recommend specific prescription medications

LIFE-THREATENING SYMPTOMS — always treat as EMERGENCY:
- Chest pain/pressure (especially with arm pain, sweating, shortness of breath)
- Difficulty breathing / can't catch breath
- Signs of stroke: face drooping, arm weakness, speech difficulty
- Severe allergic reaction: throat swelling, can't breathe
- Uncontrolled severe bleeding
- Loss of consciousness
- Seizures (first time or prolonged)
- Severe burns

HOW TO RESPOND:
- Be warm, clear, and calm
- Use simple language — avoid medical jargon unless you explain it
- Structure your response: acknowledge concern → provide info → recommend action
- If the user's description is vague, ask 1-2 specific clarifying questions
- Keep responses concise but complete

REMEMBER: You are not a replacement for a doctor. You help people navigate healthcare."""


def generate_response(user_message, context, conversation_history=None):
    """
    Generates a health assistant response using the local Llama model.

    Args:
        user_message: What the user typed
        context: Retrieved medical information (from the vector store)
        conversation_history: Previous messages in this conversation

    Returns: The AI's response as a string
    """

    # Build conversation messages
    messages = []

    # Add conversation history if available
    if conversation_history:
        messages.extend(conversation_history)

    # Add the retrieved context + user message
    user_content = f"""
RELEVANT MEDICAL INFORMATION (use this to inform your response):
{context}

---

USER QUESTION:
{user_message}
"""

    messages.append({"role": "user", "content": user_content})

    # Call local Llama via our shared utility
    response = generate_with_history(
        system_prompt=SYSTEM_PROMPT,
        conversation_history=messages,
        max_new_tokens=1024,
        temperature=0.3,
    )

    return response


if __name__ == "__main__":
    from src.rag.retriever import retrieve_context

    user_msg = "I've had a headache for 3 days that won't go away with ibuprofen"
    context = retrieve_context(user_msg)
    response = generate_response(user_msg, context)
    print("NeuroHealth Response:")
    print(response)
