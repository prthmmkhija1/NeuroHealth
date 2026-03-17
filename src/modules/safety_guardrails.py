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
5. Missing crisis resources for mental health emergencies
6. Specific prescription dosing or drug recommendations
7. Anti-vaccination / anti-medical-science misinformation

ADAPTED: Uses local Llama via llm_utils instead of OpenAI API.
"""

import json
import re
from src.llm_utils import generate_response


# ── Hard-coded pattern checks (fast, before LLM) ──────────────────────

DANGEROUS_PATTERNS = [
    # Medication interference
    r"stop\s+taking\s+(your\s+)?medication",
    r"don'?t\s+take\s+(your\s+)?medication",
    r"discontinue\s+(your\s+)?medication",
    r"throw\s+away\s+(your\s+)?medication",
    r"you\s+don'?t\s+need\s+(your\s+)?medication",
    # Definitive diagnosis
    r"you\s+(definitely|clearly|certainly|obviously)\s+have",
    r"you\s+are\s+diagnosed\s+with",
    r"i\s+can\s+confirm\s+(that\s+)?you\s+have",
    r"my\s+diagnosis\s+is",
    r"you\s+are\s+suffering\s+from(?!\s+(possible|potential|what\s+may\s+be))",
    # Dismissive reassurance
    r"you\s+don'?t\s+need\s+to\s+see\s+a\s+doctor",
    r"there'?s\s+nothing\s+to\s+worry\s+about",
    r"this\s+is\s+(not|nothing)\s+serious",
    r"you'?re\s+(perfectly\s+)?fine",
    r"nothing\s+is\s+wrong\s+with\s+you",
    r"you\s+are\s+overreacting",
    r"it'?s\s+(just|only)\s+(in\s+your\s+head|anxiety|stress)",
    # Prescription / dosing
    r"take\s+\d+\s*(mg|ml|mcg|units)\s+of\s+\w+",
    r"(prescribe|prescribed)\s+you",
    r"your\s+dose\s+should\s+be",
    r"increase\s+(your\s+)?dose\s+(to|by)",
    # Anti-science / misinformation
    r"vaccines?\s+(cause|are\s+dangerous|are\s+harmful|don'?t\s+work)",
    r"don'?t\s+(get\s+)?vaccinated",
    r"(doctors|medicine)\s+(are|is)\s+(lying|scam|fraud)",
    r"(big\s+pharma|pharmaceutical\s+conspiracy)",
]

REQUIRED_EMERGENCY_PHRASES = [
    "call 911", "go to the emergency room", "call emergency services",
    "go to the er", "seek immediate medical attention", "emergency"
]

# Mental-health crisis keywords in user input that require crisis resources
MENTAL_HEALTH_CRISIS_KEYWORDS = [
    "kill myself", "want to die", "end my life", "suicide",
    "self-harm", "hurt myself", "don't want to be here",
    "ending things", "no reason to live", "better off dead",
]

# Overdose / poisoning keywords that require Poison Control resources
OVERDOSE_KEYWORDS = [
    "took too many pills", "overdose", "overdosed", "swallowed poison",
    "drank bleach", "ingested chemicals", "took too much medication",
    "accidental ingestion", "poison", "poisoning",
]

REQUIRED_POISON_PHRASES = [
    "poison control", "1-800-222-1222", "911", "emergency"
]

REQUIRED_CRISIS_PHRASES = [
    "988", "crisis", "suicide prevention", "crisis hotline",
    "crisis line", "lifeline", "text home to 741741"
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
    user_lower = user_message.lower()

    # ── Check 1: Emergency responses MUST contain emergency language ───
    if urgency_level == "EMERGENCY":
        has_emergency_language = any(
            phrase in response_lower for phrase in REQUIRED_EMERGENCY_PHRASES
        )
        if not has_emergency_language:
            issues.append("MISSING_EMERGENCY_REDIRECT")

    # ── Check 2: Mental-health crisis MUST contain crisis resources ────
    is_mental_health_crisis = any(
        kw in user_lower for kw in MENTAL_HEALTH_CRISIS_KEYWORDS
    )
    if is_mental_health_crisis:
        has_crisis_resource = any(
            phrase in response_lower for phrase in REQUIRED_CRISIS_PHRASES
        )
        if not has_crisis_resource:
            issues.append("MISSING_CRISIS_RESOURCES")

    # ── Check 3: Overdose / poisoning MUST contain Poison Control ───
    is_overdose = any(kw in user_lower for kw in OVERDOSE_KEYWORDS)
    if is_overdose:
        has_poison_resource = any(
            phrase in response_lower for phrase in REQUIRED_POISON_PHRASES
        )
        if not has_poison_resource:
            issues.append("MISSING_POISON_CONTROL")

    # ── Check 4: Dangerous patterns ───────────────────────────────────
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, response_lower):
            issues.append(f"DANGEROUS_PATTERN: {pattern}")

    # ── Check 5: Response must contain disclaimer language ─────────────
    has_disclaimer = any(
        phrase in response_lower for phrase in [
            "not a substitute", "consult a", "healthcare professional",
            "see a doctor", "medical professional", "disclaimer",
            "not medical advice", "seek professional",
        ]
    )
    if not has_disclaimer and urgency_level not in ("N/A",):
        issues.append("MISSING_DISCLAIMER_LANGUAGE")

    # ── Check 6: LLM-based safety review (catches subtle issues) ──────
    # Run LLM check regardless of hard-check results so subtle problems
    # are never masked by simple issues like a missing disclaimer
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
6. Recommending against vaccination or spreading medical misinformation
7. Failing to suggest professional consultation for anything beyond mild self-care
8. Providing unqualified mental health diagnoses

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
        # Fail-open: if the LLM safety check itself errors, don't block the response
        return {"has_issues": False, "issues": []}


def _generate_safe_correction(original_response, issues, urgency_level):
    """Generates a corrected, safer version of the response."""
    corrected = original_response

    # Normalize issues: the LLM check can return dicts instead of strings.
    # Convert everything to strings so all downstream checks work uniformly.
    str_issues = [
        i if isinstance(i, str) else i.get("description", str(i))
        for i in issues
    ]

    # Strip dangerous patterns from the response text
    dangerous_issues = [i for i in str_issues if i.startswith("DANGEROUS_PATTERN:")]
    if dangerous_issues:
        for issue in dangerous_issues:
            pattern = issue.replace("DANGEROUS_PATTERN: ", "")
            corrected = re.sub(pattern, "[removed for safety]", corrected, flags=re.IGNORECASE)
        corrected += (
            "\n\n⚠️ **Safety Note:** Please do NOT change, stop, or adjust any "
            "medication without consulting your doctor first."
        )

    # Prepend emergency redirect if missing
    if "MISSING_EMERGENCY_REDIRECT" in str_issues:
        emergency_note = (
            "⚠️ IMPORTANT: Based on the symptoms described, please call 911 "
            "or go to the nearest Emergency Room immediately.\n\n"
        )
        corrected = emergency_note + corrected

    # Prepend crisis resources if missing
    if "MISSING_CRISIS_RESOURCES" in str_issues:
        crisis_note = (
            "💙 If you or someone you know is in crisis, please reach out now:\n"
            "• **National Suicide Prevention Lifeline:** Call or text **988**\n"
            "• **Crisis Text Line:** Text HOME to **741741**\n"
            "• **Emergency:** Call **911**\n"
            "You are not alone, and help is available.\n\n"
        )
        corrected = crisis_note + corrected

    # Prepend Poison Control if missing
    if "MISSING_POISON_CONTROL" in str_issues:
        poison_note = (
            "☠️ **IMPORTANT — Possible Poisoning/Overdose:**\n"
            "• **Poison Control Center:** Call **1-800-222-1222** (US) — available 24/7\n"
            "• **Emergency:** Call **911** if the person is unconscious, not breathing, or seizing\n"
            "Do NOT wait for symptoms to worsen.\n\n"
        )
        corrected = poison_note + corrected

    # Append disclaimer if missing
    if "MISSING_DISCLAIMER_LANGUAGE" in str_issues:
        corrected += (
            "\n\nℹ️ This information is not a substitute for professional medical "
            "advice. Please consult a qualified healthcare professional."
        )

    return corrected
