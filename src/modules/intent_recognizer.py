# src/modules/intent_recognizer.py

"""
Intent Recognition Module
-------------------------
Classifies what the user is trying to do before we do anything else.
Are they describing symptoms? Looking for a doctor? Asking a general question?

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json

from src.llm_utils import generate_response

# Emergency keywords — trigger immediate EMERGENCY classification
# without even calling the LLM (faster and safer)
EMERGENCY_KEYWORDS = [
    "heart attack",
    "can't breathe",
    "cannot breathe",
    "not breathing",
    "stroke",
    "unconscious",
    "passed out",
    "seizure",
    "uncontrollable bleeding",
    "overdose",
    "suicide",
    "kill myself",
    "chest crushing",
    "throat closing",
    "anaphylaxis",
    "911",
    "dying",
    "going to die",
    "took too many pills",
    "swallowed poison",
    "drank bleach",
]


def classify_intent(user_message):
    """
    Classifies the intent of a user's message.

    Returns:
        dict with keys:
            'intent': the classified intent (string)
            'confidence': how confident we are (0.0 to 1.0)
            'reasoning': brief explanation
    """
    # Fast emergency check — don't even call the LLM
    user_lower = user_message.lower()
    for keyword in EMERGENCY_KEYWORDS:
        if keyword in user_lower:
            return {
                "intent": "EMERGENCY",
                "confidence": 0.99,
                "reasoning": f"Emergency keyword detected: '{keyword}'",
            }

    # Use local Llama to classify all other intents
    prompt = f"""Classify the following health-related message into exactly ONE intent category.

Categories:
- SYMPTOM_CHECK: User is describing symptoms they're experiencing
- FIND_DOCTOR: User wants to find or contact a healthcare provider
- MEDICATION_INFO: User asking about medications, drugs, or supplements
- APPOINTMENT_BOOK: User wants to schedule/change/cancel an appointment
- EMERGENCY: User describes a life-threatening situation
- GENERAL_INFO: User asking general health/medical information
- MENTAL_HEALTH: User describing emotional or mental health concerns
- PREVENTIVE_CARE: User asking about wellness, screenings, vaccinations, or preventive health
- FOLLOW_UP: User following up on a previous medical encounter
- OUT_OF_SCOPE: Message is not related to health

User message: "{user_message}"

Respond with ONLY a JSON object like this:
{{"intent": "CATEGORY_NAME", "confidence": 0.95, "reasoning": "brief explanation"}}"""

    result_text = ""
    try:
        result_text = generate_response(
            system_prompt="You are a medical intent classifier. Respond ONLY with valid JSON.",
            user_message=prompt,
            temperature=0.0,
            max_new_tokens=150,
            json_mode=True,
        )

        # Try to parse JSON from response
        result = json.loads(result_text)
        return result

    except Exception as e:
        # Fallback: try to extract intent from raw text
        result_text_upper = result_text.upper() if isinstance(result_text, str) else ""
        for intent in [
            "EMERGENCY",
            "SYMPTOM_CHECK",
            "FIND_DOCTOR",
            "MEDICATION_INFO",
            "APPOINTMENT_BOOK",
            "GENERAL_INFO",
            "MENTAL_HEALTH",
            "PREVENTIVE_CARE",
            "FOLLOW_UP",
            "OUT_OF_SCOPE",
        ]:
            if intent in result_text_upper:
                return {
                    "intent": intent,
                    "confidence": 0.7,
                    "reasoning": f"Extracted from model output (JSON parse failed: {e})",
                }

        return {
            "intent": "SYMPTOM_CHECK",  # Safe default
            "confidence": 0.5,
            "reasoning": f"Default (error in classification: {e})",
        }


if __name__ == "__main__":
    test_messages = [
        "I have a bad headache and it's getting worse",
        "I need to find a neurologist in my area",
        "What is metformin prescribed for?",
        "I think I'm having a heart attack",
        "I've been feeling anxious and can't sleep",
        "What's 2+2?",
    ]

    for msg in test_messages:
        result = classify_intent(msg)
        print(f"Message: '{msg[:60]}'")
        print(f"  Intent: {result['intent']} (confidence: {result['confidence']})")
        print()
