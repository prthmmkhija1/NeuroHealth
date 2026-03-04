# tests/test_all_fixes.py
"""Quick validation of all fixes made in this session."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from tests.helpers import vector_store_ready, import_pipeline


# Use shared helpers from conftest
_vector_store_ready = vector_store_ready
_import_pipeline = import_pipeline


def test_empty_input():
    process_message = _import_pipeline()
    r = process_message("")
    assert r["response"]["urgency_level"] == "N/A"
    r2 = process_message("   ")
    assert r2["response"]["urgency_level"] == "N/A"
    print("PASS: Empty input handling")


def test_long_input_truncation():
    process_message = _import_pipeline()
    # This should not crash even with very long input
    long_msg = "headache " * 500  # 4500+ chars
    r = process_message(long_msg)
    # Should process without error (intent recognizer will classify it)
    assert "response" in r
    print("PASS: Long input truncation")


def test_emergency_keywords_overdose():
    from src.modules.intent_recognizer import classify_intent
    for msg in ["heart attack", "took too many pills", "swallowed poison", "drank bleach"]:
        r = classify_intent(msg)
        assert r["intent"] == "EMERGENCY", f"{msg} should be EMERGENCY, got {r['intent']}"
    print("PASS: Emergency keywords (incl. overdose)")


def test_urgency_overdose():
    from src.modules.urgency_assessor import assess_urgency
    for msg in ["overdose on pills", "took too many pills", "swallowed poison"]:
        r = assess_urgency(msg)
        assert r["level"] == "EMERGENCY", f"{msg} should be EMERGENCY, got {r['level']}"
    print("PASS: Urgency emergency patterns (incl. overdose)")


def test_safety_poison_control():
    from src.modules.safety_guardrails import check_safety
    r = check_safety(
        "Rest and drink water. Consult a healthcare professional.",
        "EMERGENCY",
        "I took too many pills"
    )
    assert "MISSING_POISON_CONTROL" in r["issues"]
    corrected = r["corrected_response"].lower()
    assert "poison control" in corrected or "1-800-222-1222" in corrected
    print("PASS: Safety Poison Control detection")


def test_safety_crisis_resources():
    from src.modules.safety_guardrails import check_safety
    r = check_safety(
        "I understand you feel bad. Consult a healthcare professional.",
        "EMERGENCY",
        "I want to kill myself"
    )
    assert "MISSING_CRISIS_RESOURCES" in r["issues"]
    assert "988" in r["corrected_response"]
    print("PASS: Safety crisis resources detection")


def test_safety_emergency_redirect():
    from src.modules.safety_guardrails import check_safety
    r = check_safety(
        "You should rest and drink fluids. Consult a healthcare professional.",
        "EMERGENCY",
        "chest pain"
    )
    assert "MISSING_EMERGENCY_REDIRECT" in r["issues"]
    assert "911" in r["corrected_response"]
    print("PASS: Safety emergency redirect correction")


def test_safety_dangerous_patterns():
    from src.modules.safety_guardrails import check_safety
    # Test stop medication
    r = check_safety(
        "You should stop taking your medication immediately. Consult a healthcare professional.",
        "ROUTINE",
        "medication question"
    )
    assert not r["is_safe"]
    print("PASS: Dangerous pattern detection")


def test_conversation_manager():
    from src.modules.conversation_manager import ConversationManager
    cm = ConversationManager(session_id="test")
    cm.add_user_message("hello")
    assert cm.message_count == 1
    cm.update_health_context(extracted_symptoms={"symptoms": [{"name": "headache"}]})
    assert "headache" in cm.health_context["symptoms_mentioned"]
    summary = cm.get_health_summary()
    assert "headache" in summary
    d = cm.to_dict()
    assert d["session_id"] == "test"
    print("PASS: Conversation manager")


def test_response_formatter():
    from src.modules.response_formatter import format_response
    r = format_response(
        "test", {"level": "EMERGENCY", "call_to_action": "Call 911", "warning_signs": []},
        None, "test"
    )
    assert r["urgency_level"] == "EMERGENCY"
    assert r["urgency_color"] == "#FF0000"
    print("PASS: Response formatter")


def test_needs_clarification():
    from src.modules.response_formatter import format_response
    r = format_response(
        "test",
        {"level": "NEEDS_CLARIFICATION", "call_to_action": "Provide more details", "warning_signs": []},
        None, "test"
    )
    assert r["urgency_level"] == "NEEDS_CLARIFICATION"
    assert r["urgency_color"] == "#999999"
    print("PASS: NEEDS_CLARIFICATION formatter")


def test_appointment_emergency():
    from src.modules.appointment_recommender import recommend_appointment
    r = recommend_appointment("chest pain", {"level": "EMERGENCY"}, None)
    assert r["appointment_type"] == "Emergency Room (ER)"
    assert r["urgency"] == "IMMEDIATELY"
    print("PASS: Appointment emergency override")


if __name__ == "__main__":
    test_empty_input()
    test_long_input_truncation()
    test_emergency_keywords_overdose()
    test_urgency_overdose()
    test_safety_poison_control()
    test_safety_crisis_resources()
    test_safety_emergency_redirect()
    test_safety_dangerous_patterns()
    test_conversation_manager()
    test_response_formatter()
    test_needs_clarification()
    test_appointment_emergency()
    print("\n" + "=" * 50)
    print("ALL TESTS PASSED!")
    print("=" * 50)
