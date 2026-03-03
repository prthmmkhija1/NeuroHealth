# src/modules/appointment_recommender.py

"""
Appointment Recommendation Module
-----------------------------------
Based on symptoms and urgency, recommends what type of doctor
to see and how to find them.

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json
from src.llm_utils import generate_response


# Mapping of symptoms/body systems to specialists
SPECIALTY_MAP = {
    "cardiac": "Cardiologist (heart doctor)",
    "respiratory": "Pulmonologist (lung doctor) or Allergist",
    "neurological": "Neurologist (brain/nerve doctor)",
    "gastrointestinal": "Gastroenterologist (digestive system doctor)",
    "musculoskeletal": "Orthopedic Surgeon or Rheumatologist",
    "dermatological": "Dermatologist (skin doctor)",
    "mental_health": "Psychiatrist or Psychologist",
    "endocrine": "Endocrinologist (hormones/thyroid doctor)",
    "urological": "Urologist (urinary tract doctor)",
    "general": "General Practitioner (GP) / Primary Care Physician",
    "emergency": "Emergency Room (ER)"
}


def recommend_appointment(user_message, urgency_info, extracted_symptoms=None):
    """
    Recommends appropriate medical appointment based on assessment.

    Returns:
        dict with recommendation details
    """
    urgency_level = urgency_info.get("level", "ROUTINE")

    # Emergency override
    if urgency_level == "EMERGENCY":
        return {
            "appointment_type": "Emergency Room (ER)",
            "urgency": "IMMEDIATELY",
            "specialty": "Emergency Medicine",
            "preparation": "Call 911 — do not drive yourself if severely ill",
            "alternatives": ["Call 911 first", "Have someone drive you to ER"],
            "what_to_bring": ["ID", "Insurance card", "List of medications", "Someone to accompany you"],
            "questions_to_ask_doctor": []
        }

    prompt = f"""You are a medical appointment coordinator.

Based on this user's situation, recommend the most appropriate medical care.

User message: "{user_message}"
Urgency level: {urgency_level}
Body systems affected: {extracted_symptoms.get('body_systems', []) if extracted_symptoms else []}

Recommend the best appointment type.

Respond with ONLY a JSON object:
{{
  "appointment_type": "type of appointment",
  "specialty": "type of doctor",
  "urgency": "when to schedule (e.g., today, within 2 days, within a week)",
  "preparation": "what to do before the appointment",
  "what_to_bring": ["list of things to bring"],
  "questions_to_ask_doctor": ["suggested questions for the doctor visit"],
  "alternatives": ["lower-cost or more accessible alternatives if any"]
}}"""

    try:
        result_text = generate_response(
            system_prompt="You are a medical appointment coordinator. Respond ONLY with valid JSON.",
            user_message=prompt,
            temperature=0.0,
            max_new_tokens=500,
            json_mode=True,
        )

        return json.loads(result_text)

    except (json.JSONDecodeError, Exception) as e:
        return {
            "appointment_type": "Primary Care / General Practitioner",
            "specialty": "General Practice",
            "urgency": "Within 1-2 days",
            "preparation": "Note down your symptoms and when they started",
            "what_to_bring": ["ID", "Insurance card", "List of current medications"],
            "questions_to_ask_doctor": ["What could be causing my symptoms?"],
            "alternatives": []
        }


if __name__ == "__main__":
    test_urgency = {"level": "ROUTINE", "level_number": 4}
    result = recommend_appointment(
        "I've had mild knee pain for a week",
        test_urgency,
        {"body_systems": ["musculoskeletal"]}
    )
    print(json.dumps(result, indent=2))
