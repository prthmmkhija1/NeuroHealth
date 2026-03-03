# src/modules/symptom_extractor.py

"""
Symptom Extraction Module
--------------------------
Reads the user's message and pulls out all mentioned symptoms
with their properties (location, severity, duration).

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json
from src.llm_utils import generate_response


def extract_symptoms(user_message):
    """
    Extracts structured symptom information from a user's message.

    Returns:
        dict with keys:
            'symptoms': list of symptom objects
            'body_systems': list of affected body systems
            'vital_signs_mentioned': dict
    """
    prompt = f"""Extract all health symptoms from the following user message.
For each symptom, capture all available details.

User message: "{user_message}"

Respond with ONLY a JSON object like this:
{{
  "symptoms": [
    {{
      "name": "symptom name",
      "location": "where on the body (or null)",
      "severity": "mild/moderate/severe/unknown",
      "duration": "how long they've had it (or null)",
      "character": "description like sharp/dull/burning/throbbing (or null)",
      "associated_symptoms": ["any other symptoms mentioned together"]
    }}
  ],
  "body_systems": ["list of affected systems like cardiac, respiratory, neurological"],
  "vital_signs_mentioned": {{
    "temperature": null,
    "heart_rate": null,
    "blood_pressure": null
  }}
}}

If no symptoms are mentioned, return {{"symptoms": [], "body_systems": [], "vital_signs_mentioned": {{}}}}"""

    try:
        result_text = generate_response(
            system_prompt="You are a medical symptom extractor. Respond ONLY with valid JSON.",
            user_message=prompt,
            temperature=0.0,
            max_new_tokens=400,
            json_mode=True,
        )

        result = json.loads(result_text)
        return result

    except (json.JSONDecodeError, Exception) as e:
        return {
            "symptoms": [],
            "body_systems": [],
            "vital_signs_mentioned": {},
            "error": str(e)
        }


if __name__ == "__main__":
    test_messages = [
        "I've had a throbbing headache on the right side for 2 days, and I feel nauseous",
        "My chest feels tight and I'm short of breath. Started about an hour ago.",
        "I have a fever of 102°F and a sore throat since yesterday",
    ]

    for msg in test_messages:
        print(f"Message: '{msg}'")
        result = extract_symptoms(msg)
        print(f"Extracted: {json.dumps(result, indent=2)}")
        print()
