# src/modules/urgency_assessor.py

"""
Urgency Assessment Module
--------------------------
Determines how quickly the user needs medical attention:

  LEVEL 1 - EMERGENCY:  Call 911 or go to ER immediately
  LEVEL 2 - URGENT:     See a doctor within hours (urgent care)
  LEVEL 3 - SOON:       See a doctor within 1-2 days
  LEVEL 4 - ROUTINE:    Schedule a regular appointment
  LEVEL 5 - SELF_CARE:  Can manage at home with guidance

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json
from src.llm_utils import generate_response
from src.data_pipeline.entity_schema import check_urgency_rules, get_red_flags_for_symptoms


# Hard-coded emergency rules (faster and more reliable than LLM)
IMMEDIATE_EMERGENCY_PATTERNS = {
    "cardiac": ["chest pain", "chest pressure", "chest crushing", "heart attack",
                "left arm pain with chest", "jaw pain with chest"],
    "respiratory": ["can't breathe", "cannot breathe", "stopped breathing",
                    "throat closing", "anaphylaxis"],
    "neurological": ["stroke symptoms", "face drooping", "sudden severe headache",
                    "worst headache of my life", "sudden vision loss", "seizure"],
    "trauma": ["uncontrolled bleeding", "major injury", "unconscious"],
    "mental_health_crisis": ["suicide", "kill myself", "want to die",
                              "hurting myself"],
    "overdose_poisoning": ["overdose", "took too many pills", "swallowed poison",
                            "drank bleach", "ingested chemicals", "poisoning"],
}


def assess_urgency(user_message, extracted_symptoms=None):
    """
    Assesses the urgency level for a user's health concern.

    Args:
        user_message: The user's text
        extracted_symptoms: Optional output from symptom_extractor

    Returns:
        dict with urgency level, recommendation, reasoning, etc.
    """
    user_lower = user_message.lower()

    # Check hard emergency patterns first
    for category, patterns in IMMEDIATE_EMERGENCY_PATTERNS.items():
        for pattern in patterns:
            if pattern in user_lower:
                return {
                    "level": "EMERGENCY",
                    "level_number": 1,
                    "recommendation": "Call 911 (emergency services) IMMEDIATELY",
                    "reasoning": f"Potential emergency detected: {category}",
                    "call_to_action": "CALL 911 NOW. Do not wait.",
                    "warning_signs": [],
                    "color_code": "RED"
                }

    # ── Check structured urgency rules from entity schema ────
    symptom_names = []
    if extracted_symptoms and extracted_symptoms.get("symptoms"):
        symptom_names = [s.get("name", "").lower() for s in extracted_symptoms["symptoms"]]
    rule_hit = check_urgency_rules(symptom_names, user_message)
    if rule_hit:
        # rule_hit is now the escalated urgency level string (e.g. "EMERGENCY")
        level = rule_hit if isinstance(rule_hit, str) else "EMERGENCY"
        level_map = {"EMERGENCY": 1, "URGENT": 2, "SOON": 3, "ROUTINE": 4, "SELF_CARE": 5}
        color_map = {"EMERGENCY": "RED", "URGENT": "ORANGE", "SOON": "YELLOW", "ROUTINE": "GREEN", "SELF_CARE": "BLUE"}
        return {
            "level": level,
            "level_number": level_map.get(level, 1),
            "recommendation": f"Urgency rule triggered: {level}",
            "reasoning": f"Urgency rule matched for symptoms: {symptom_names}",
            "call_to_action": "Call 911 NOW" if level == "EMERGENCY" else "Seek medical attention",
            "warning_signs": get_red_flags_for_symptoms(symptom_names),
            "color_code": color_map.get(level, "RED")
        }

    # Use local Llama for nuanced assessment
    symptom_context = ""
    if extracted_symptoms and extracted_symptoms.get("symptoms"):
        symptom_context = f"\nExtracted symptoms: {json.dumps(extracted_symptoms['symptoms'])}"

    prompt = f"""You are an experienced ER triage nurse assessing urgency.

User message: "{user_message}"{symptom_context}

Assess the urgency level using this 5-level scale with EXAMPLES:

1. EMERGENCY: Life-threatening, call 911 immediately
   Examples: chest pain with arm numbness, can't breathe, stroke signs, suicidal ideation, overdose, severe allergic reaction
2. URGENT: Could worsen significantly, urgent care/ER within hours
   Examples: high fever (>103F for 2+ days), severe abdominal pain, deep cuts needing stitches, diabetic blood sugar >300, broken bone
3. SOON: Should see a doctor within 1-2 days
   Examples: persistent fever (101-103F), ear infection symptoms, moderate back pain with numbness, UTI symptoms, worsening rash
4. ROUTINE: Schedule a regular appointment this week
   Examples: mild persistent headaches, seasonal allergies, routine med refill, minor skin conditions, annual checkup questions
5. SELF_CARE: Can be managed at home with OTC remedies
   Examples: common cold with runny nose, small paper cut, mild muscle soreness, minor bug bite, mild occasional headache

IMPORTANT CALIBRATION RULES:
- Common cold, runny nose, mild cough, paper cuts, minor aches = SELF_CARE (NOT ROUTINE or SOON)
- Scheduling questions, general health info, preventive care = ROUTINE (NOT SOON)
- Only use SOON when symptoms are actively worsening or moderately concerning
- When in doubt between adjacent levels, err toward the MORE urgent level

Valid levels: EMERGENCY, URGENT, SOON, ROUTINE, SELF_CARE

Respond with ONLY a JSON object:
{{
  "level": "SOON",
  "level_number": 3,
  "recommendation": "what they should do",
  "reasoning": "why this level",
  "call_to_action": "specific next step sentence",
  "warning_signs": ["list symptoms that would make this more urgent"],
  "color_code": "YELLOW"
}}"""

    try:
        result_text = generate_response(
            system_prompt="You are a medical triage nurse. Respond ONLY with valid JSON.",
            user_message=prompt,
            temperature=0.0,
            max_new_tokens=400,
            json_mode=True,
        )

        return json.loads(result_text)

    except Exception as e:
        # Safe fallback
        return {
            "level": "SOON",
            "level_number": 3,
            "recommendation": "Please consult a healthcare provider",
            "reasoning": f"Could not assess (error: {e})",
            "call_to_action": "Please see a doctor to be safe.",
            "warning_signs": [],
            "color_code": "YELLOW"
        }


if __name__ == "__main__":
    tests = [
        "I have crushing chest pain and my left arm hurts",
        "I've had a sore throat for 3 days now",
        "My blood sugar feels low, I'm shaking slightly",
        "I cut my finger while cooking, small cut",
    ]

    for msg in tests:
        result = assess_urgency(msg)
        print(f"[{result['color_code']}] {result['level']}: {msg[:60]}")
        print(f"  → {result['call_to_action']}")
        print()
