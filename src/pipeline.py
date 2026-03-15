# src/pipeline.py

"""
Main NeuroHealth Pipeline
--------------------------
Connects ALL modules together into one function.
When a user sends a message, this pipeline:
  1. Checks for emergencies first (safety first!)
  2. Classifies intent
  3. Extracts symptoms
  4. Retrieves relevant medical knowledge
  5. Assesses urgency
  6. Gets appointment recommendation
  7. Generates AI response
  8. Runs safety guardrails
  9. Formats and returns the final response
"""

from src.modules.intent_recognizer import classify_intent
from src.modules.symptom_extractor import extract_symptoms
from src.modules.urgency_assessor import assess_urgency
from src.modules.appointment_recommender import recommend_appointment
from src.modules.safety_guardrails import check_safety
from src.modules.conversation_manager import ConversationManager
from src.modules.response_formatter import format_response
from src.rag.retriever import retrieve_context
from src.rag.generator import generate_response


# Global store of active sessions (in production, use Redis or a database)
active_sessions = {}


def process_message(user_message, session_id=None):
    """
    The main entry point for NeuroHealth.
    Takes a user message and returns a formatted health assistant response.

    Args:
        user_message: What the user typed
        session_id: Session ID for conversation continuity (None = new session)

    Returns:
        dict with response and all intermediate data
    """
    # ── INPUT VALIDATION ─────────────────────────────────
    if not user_message or not user_message.strip():
        return {
            "session_id": session_id or "none",
            "response": {
                "text": "It looks like your message was empty. Could you describe your symptoms or health question?",
                "urgency_level": "N/A",
                "urgency_color": "#888888",
                "metadata": {}
            },
            "intent": {"intent": "INVALID_INPUT", "confidence": 1.0, "reasoning": "Empty input"}
        }

    # Truncate very long input to prevent token overflow / abuse
    MAX_INPUT_LENGTH = 2000
    if len(user_message) > MAX_INPUT_LENGTH:
        user_message = user_message[:MAX_INPUT_LENGTH] + "..."

    user_message = user_message.strip()

    print(f"\n{'='*50}")
    print(f"Processing: '{user_message[:80]}'")
    print('='*50)

    # Get or create session
    if session_id and session_id in active_sessions:
        session = active_sessions[session_id]
    else:
        session = ConversationManager()
        session_id = session.session_id
        active_sessions[session_id] = session

    # Add user message to history
    session.add_user_message(user_message)

    # ── STEP 1: Classify Intent ──────────────────────────────
    print("\n[Step 1] Classifying intent...")
    intent_info = classify_intent(user_message)
    print(f"  Intent: {intent_info['intent']}")

    # ── STEP 2: Handle Out-of-Scope ──────────────────────────
    if intent_info["intent"] == "OUT_OF_SCOPE":
        response_text = (
            "I'm NeuroHealth, a health-focused assistant. "
            "I can help you with health questions, symptom checking, "
            "and finding the right medical care. "
            "Could I help you with a health-related question?"
        )
        formatted = {
            "text": response_text,
            "urgency_level": "N/A",
            "urgency_color": "#888888",
            "metadata": {}
        }
        session.add_assistant_message(response_text)
        return {
            "session_id": session_id,
            "response": formatted,
            "intent": intent_info,
            "debug": {
                "intent": intent_info,
                "symptoms": {},
                "urgency": {"level": "N/A"},
                "appointment": {},
                "safety_issues": []
            }
        }

    # ── STEP 3: Extract Symptoms ─────────────────────────────
    print("\n[Step 3] Extracting symptoms...")
    symptoms = extract_symptoms(user_message)
    print(f"  Found {len(symptoms.get('symptoms', []))} symptoms")

    # Update session context
    session.update_health_context(extracted_symptoms=symptoms)

    # ── STEP 4: Retrieve Medical Context ─────────────────────
    print("\n[Step 4] Retrieving medical context...")
    try:
        medical_context = retrieve_context(user_message)
    except (RuntimeError, Exception) as e:
        print(f"  ⚠️ RAG retrieval failed ({e}), continuing without context")
        medical_context = ""

    # ── STEP 5: Assess Urgency ───────────────────────────────
    print("\n[Step 5] Assessing urgency...")
    urgency = assess_urgency(user_message, symptoms)
    print(f"  Urgency: {urgency['level']}")

    session.update_health_context(urgency_info=urgency)

    # ── STEP 6: Appointment Recommendation ───────────────────
    print("\n[Step 6] Generating appointment recommendation...")
    appointment = recommend_appointment(user_message, urgency, symptoms)

    # ── STEP 7: Generate AI Response ─────────────────────────
    print("\n[Step 7] Generating AI response...")
    conversation_history = session.get_history_as_messages()[:-1]  # Exclude current message
    health_summary = session.get_health_summary()

    contextual_message = user_message
    if health_summary:
        contextual_message = f"{user_message}\n\n[Session context: {health_summary}]"

    raw_response = generate_response(
        user_message=contextual_message,
        context=medical_context,
        conversation_history=conversation_history
    )

    # ── STEP 8: Safety Guardrails ────────────────────────────
    print("\n[Step 8] Running safety check...")
    safety_check = check_safety(raw_response, urgency["level"], user_message)
    final_response_text = safety_check["corrected_response"]

    if not safety_check["is_safe"]:
        print(f"  ⚠️ Safety issues found: {safety_check['issues']}")
    else:
        print("  ✓ Response passed safety check")

    # ── STEP 9: Format Response ──────────────────────────────
    print("\n[Step 9] Formatting response...")
    formatted_response = format_response(
        ai_response=final_response_text,
        urgency_info=urgency,
        appointment_info=appointment,
        user_message=user_message
    )

    # Save response to session
    session.add_assistant_message(final_response_text)

    return {
        "session_id": session_id,
        "response": formatted_response,
        "debug": {
            "intent": intent_info,
            "symptoms": symptoms,
            "urgency": urgency,
            "appointment": appointment,
            "safety_issues": safety_check["issues"]
        }
    }


if __name__ == "__main__":
    # Test the complete pipeline
    test_messages = [
        "I have a headache that won't go away for 2 days",
        "I think I'm having a heart attack",
        "What's the difference between a cold and flu?",
    ]

    for msg in test_messages:
        result = process_message(msg)
        print("\n" + "="*60)
        print("FINAL RESPONSE:")
        print(result["response"]["text"])
