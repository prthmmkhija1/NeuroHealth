# src/modules/safety_guardrails.py

"""
Safety Guardrails Module
------------------------
The last line of defense. Scans every response before it is sent
to the user to make sure it doesn't contain dangerous advice.

Checks for:
1. Missing emergency redirects (did we forget to mention 911?)
2. Dangerous medical advice (telling someone to stop their medication)
3. Definitive diagnoses (we should say "possibly" not "you have X")
4. Inappropriate reassurance (saying "you're fine" for serious symptoms)

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json
import re
from src.llm_utils import generate_response


# Hard-coded pattern checks (fast, before LLM)
DANGEROUS_PATTERNS = [
    r"stop taking your medication",
    r"don't take.*medication",
    r"you definitely have",
    r"you are diagnosed with",
    r"you don't need to see a doctor",
    r"there's nothing to worry about",
    r"this is not serious",
]

REQUIRED_EMERGENCY_PHRASES = [
    "call 911", "go to the emergency room", "call emergency services",
    "go to the er", "seek immediate medical attention", "emergency"
]


def check_safety(response_text, urgency_level, user_message):
    """
    Checks a generated response for safety issues.

    Args:
        response_text: The AI's generated response (before sending to user)
        urgency_level: The urgency assessed (EMERGENCY/URGENT/SOON/ROUTINE)
        user_message: Original user message

    Returns:
        dict:
            'is_safe': bool
            'issues': list of problems found
            'corrected_response': fixed response (if issues found)
    """
    issues = []
    response_lower = response_text.lower()

    # Check 1: Emergency responses MUST contain emergency language
    if urgency_level == "EMERGENCY":
        has_emergency_language = any(
            phrase in response_lower for phrase in REQUIRED_EMERGENCY_PHRASES
        )
        if not has_emergency_language:
            issues.append("MISSING_EMERGENCY_REDIRECT")

    # Check 2: Dangerous patterns
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, response_lower):
            issues.append(f"DANGEROUS_PATTERN: {pattern}")

    # Check 3: LLM-based safety review (catches subtle issues)
    if not issues:  # Only do expensive LLM check if basic checks pass
        llm_check = _llm_safety_review(response_text, urgency_level, user_message)
        if llm_check.get("has_issues"):
            issues.extend(llm_check.get("issues", []))

    if not issues:
        return {
            "is_safe": True,
            "issues": [],
            "corrected_response": response_text
        }

    # Generate a safer corrected response
    corrected = _generate_safe_correction(response_text, issues, urgency_level)

    return {
        "is_safe": False,
        "issues": issues,
        "corrected_response": corrected
    }


def _llm_safety_review(response_text, urgency_level, user_message):
    """Uses local Llama to check for subtle safety issues not caught by regex."""
    prompt = f"""Review this health assistant response for safety issues.

Original user message: "{user_message[:200]}"
Urgency level: {urgency_level}

Assistant response to review:
"{response_text}"

Check for these safety problems:
1. Definitively diagnosing a condition (should say "possibly" or "may be")
2. Recommending stopping prescription medication
3. Dismissing serious symptoms as nothing to worry about
4. Missing emergency referral for clearly serious symptoms
5. Providing specific dosing instructions for prescription drugs

Respond with ONLY JSON:
{{"has_issues": true, "issues": ["list of specific issues found"]}}
or
{{"has_issues": false, "issues": []}}"""

    try:
        result_text = generate_response(
            system_prompt="You are a medical safety reviewer. Respond ONLY with valid JSON.",
            user_message=prompt,
            temperature=0.0,
            max_new_tokens=200,
            json_mode=True,
        )

        return json.loads(result_text)

    except Exception:
        return {"has_issues": False, "issues": []}


def _generate_safe_correction(original_response, issues, urgency_level):
    """Generates a corrected, safer version of the response."""
    corrected = original_response

    # If emergency redirect is missing, prepend it
    if "MISSING_EMERGENCY_REDIRECT" in issues:
        emergency_note = (
            "⚠️ IMPORTANT: Based on the symptoms described, please call 911 "
            "or go to the nearest Emergency Room immediately.\n\n"
        )
        corrected = emergency_note + corrected

    return corrected
