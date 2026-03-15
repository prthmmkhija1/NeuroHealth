# tests/test_modules.py

"""
Tests for individual modules (can run on HP-INT without GPU).
Tests keyword-based logic and pure Python modules only.
LLM-dependent tests are skipped if model is not loaded.
"""

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_intent_emergency_keywords():
    """Test that emergency keywords trigger EMERGENCY intent without LLM."""
    from src.modules.intent_recognizer import classify_intent

    emergency_messages = [
        "I think I'm having a heart attack",
        "I can't breathe at all",
        "Someone has passed out and is unconscious",
        "I think I might kill myself",
        "I took too many pills",
    ]

    for msg in emergency_messages:
        result = classify_intent(msg)
        assert result["intent"] == "EMERGENCY", \
            f"'{msg}' should be EMERGENCY, got {result['intent']}"
        assert result["confidence"] >= 0.9, \
            f"Emergency keyword detection should have high confidence"

    print("✓ Intent emergency keywords test passed")


def test_urgency_emergency_patterns():
    """Test that hard-coded emergency patterns trigger EMERGENCY urgency."""
    from src.modules.urgency_assessor import assess_urgency

    emergency_messages = [
        "I have chest pain and pressure",
        "I can't breathe, throat closing",
        "I want to kill myself",
        "There is uncontrolled bleeding",
        "I overdose on pills",
    ]

    for msg in emergency_messages:
        result = assess_urgency(msg)
        assert result["level"] == "EMERGENCY", \
            f"'{msg}' should be EMERGENCY, got {result['level']}"
        assert result["level_number"] == 1
        assert result["color_code"] == "RED"

    print("✓ Urgency emergency patterns test passed")


def test_conversation_manager():
    """Test ConversationManager (pure Python, no LLM needed)."""
    from src.modules.conversation_manager import ConversationManager

    cm = ConversationManager(session_id="test_session")

    assert cm.session_id == "test_session"
    assert cm.message_count == 0
    assert len(cm.get_history_as_messages()) == 0

    # Add messages
    cm.add_user_message("I have a headache")
    assert cm.message_count == 1

    cm.add_assistant_message("Tell me more about your headache.")
    history = cm.get_history_as_messages()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    # Update health context
    cm.update_health_context(
        extracted_symptoms={"symptoms": [{"name": "headache"}]},
        urgency_info={"level": "ROUTINE"}
    )
    assert "headache" in cm.health_context["symptoms_mentioned"]
    assert len(cm.health_context["urgency_history"]) == 1

    # Health summary
    summary = cm.get_health_summary()
    assert "headache" in summary

    # Serialization
    d = cm.to_dict()
    assert d["session_id"] == "test_session"
    assert d["message_count"] == 1

    print("✓ Conversation manager test passed")


def test_response_formatter():
    """Test response formatting (pure Python, no LLM needed)."""
    from src.modules.response_formatter import format_response

    urgency = {
        "level": "EMERGENCY",
        "call_to_action": "CALL 911 NOW",
        "warning_signs": ["worsening pain"]
    }
    appointment = {
        "specialty": "Emergency Medicine",
        "urgency": "IMMEDIATELY",
        "what_to_bring": ["ID", "Insurance"]
    }

    result = format_response(
        ai_response="This is a test response.",
        urgency_info=urgency,
        appointment_info=appointment,
        user_message="test"
    )

    assert result["urgency_level"] == "EMERGENCY"
    assert result["urgency_color"] == "#FF0000"
    assert "🔴" in result["text"]
    assert "CALL 911 NOW" in result["text"]
    assert "Disclaimer" in result["text"]

    print("✓ Response formatter test passed")


def test_safety_guardrails_patterns():
    """Test regex-based safety checks (no LLM needed)."""
    from src.modules.safety_guardrails import check_safety

    _no_llm_issues = {"has_issues": False, "issues": []}

    with patch("src.modules.safety_guardrails._llm_safety_review", return_value=_no_llm_issues):
        # Test: emergency response missing emergency language
        result = check_safety(
            response_text="You should rest and drink fluids.",
            urgency_level="EMERGENCY",
            user_message="chest pain"
        )
        assert not result["is_safe"], "Should flag missing emergency redirect"
        assert "MISSING_EMERGENCY_REDIRECT" in result["issues"]
        assert "911" in result["corrected_response"]

        # Test: dangerous pattern detection — stop medication
        result = check_safety(
            response_text="You should stop taking your medication immediately.",
            urgency_level="ROUTINE",
            user_message="medication question"
        )
        assert not result["is_safe"], "Should flag dangerous medication advice"

        # Test: definitive diagnosis
        result = check_safety(
            response_text="You definitely have diabetes. Please consult a healthcare professional.",
            urgency_level="ROUTINE",
            user_message="blood sugar"
        )
        assert not result["is_safe"], "Should flag definitive diagnosis"

        # Test: dismissive reassurance
        result = check_safety(
            response_text="There's nothing to worry about, you're fine. Consult a doctor.",
            urgency_level="ROUTINE",
            user_message="chest tightness"
        )
        assert not result["is_safe"], "Should flag dismissive reassurance"

        # Test: mental health crisis missing resources
        result = check_safety(
            response_text="I'm sorry you feel that way. Please consult a healthcare professional.",
            urgency_level="EMERGENCY",
            user_message="I want to kill myself"
        )
        assert "MISSING_CRISIS_RESOURCES" in result["issues"], \
            "Should flag missing crisis resources for suicidal messages"
        assert "988" in result["corrected_response"], \
            "Corrected response should include 988 crisis line"

        # Test: safe response passes
        result = check_safety(
            response_text="Based on what you described, this could possibly be a tension headache. "
                           "Please consult a healthcare professional for a proper evaluation.",
            urgency_level="ROUTINE",
            user_message="I have a headache"
        )
        assert result["is_safe"], f"Safe response should pass, but got issues: {result['issues']}"

    print("✓ Safety guardrails pattern test passed")


def test_appointment_emergency_override():
    """Test that EMERGENCY urgency triggers ER recommendation."""
    from src.modules.appointment_recommender import recommend_appointment

    result = recommend_appointment(
        "chest pain",
        urgency_info={"level": "EMERGENCY"},
        extracted_symptoms=None
    )
    assert result["appointment_type"] == "Emergency Room (ER)"
    assert result["urgency"] == "IMMEDIATELY"

    print("✓ Appointment emergency override test passed")


def test_safety_poison_control():
    """Test that overdose messages trigger Poison Control resource."""
    from src.modules.safety_guardrails import check_safety

    _no_llm_issues = {"has_issues": False, "issues": []}

    with patch("src.modules.safety_guardrails._llm_safety_review", return_value=_no_llm_issues):
        result = check_safety(
            response_text="You should rest and see a doctor. Please consult a healthcare professional.",
            urgency_level="EMERGENCY",
            user_message="I took too many pills"
        )
        assert "MISSING_POISON_CONTROL" in result["issues"], \
            "Should flag missing Poison Control for overdose"
        corrected_lower = result["corrected_response"].lower()
        assert "poison control" in corrected_lower or "1-800-222-1222" in corrected_lower, \
            "Corrected response should include Poison Control info"

    print("✓ Safety Poison Control test passed")


def test_symptom_extractor_structure():
    """Test that symptom_extractor returns correct structure on empty/simple input."""
    from src.modules.symptom_extractor import extract_symptoms

    # Test that the function returns the expected structure even on error
    # (when LLM is unavailable, it returns fallback structure)
    try:
        result = extract_symptoms("")
    except Exception:
        import pytest
        pytest.skip("LLM not available for symptom extractor test")
        return

    assert "symptoms" in result, "Result should have 'symptoms' key"
    assert "body_systems" in result, "Result should have 'body_systems' key"
    assert isinstance(result["symptoms"], list), "symptoms should be a list"
    assert isinstance(result["body_systems"], list), "body_systems should be a list"

    print("✓ Symptom extractor structure test passed")


def test_conversation_manager_multiturn():
    """Test multi-turn conversation context accumulation."""
    from src.modules.conversation_manager import ConversationManager

    cm = ConversationManager(session_id="multi_turn_test")

    # Turn 1: user reports headache
    cm.add_user_message("I have a bad headache")
    cm.update_health_context(
        extracted_symptoms={"symptoms": [{"name": "headache"}]},
        urgency_info={"level": "ROUTINE"}
    )
    cm.add_assistant_message("Tell me more about your headache.")

    # Turn 2: user adds fever
    cm.add_user_message("I also have a fever of 102")
    cm.update_health_context(
        extracted_symptoms={"symptoms": [{"name": "fever"}]},
        urgency_info={"level": "URGENT"}
    )
    cm.add_assistant_message("With fever and headache, I recommend...")

    # Verify accumulated context
    assert cm.message_count == 2
    assert len(cm.get_history_as_messages()) == 4  # 2 user + 2 assistant
    assert "headache" in cm.health_context["symptoms_mentioned"]
    assert "fever" in cm.health_context["symptoms_mentioned"]
    assert len(cm.health_context["urgency_history"]) == 2
    assert cm.health_context["urgency_history"][0]["level"] == "ROUTINE"
    assert cm.health_context["urgency_history"][1]["level"] == "URGENT"

    # Verify summary includes both symptoms
    summary = cm.get_health_summary()
    assert "headache" in summary
    assert "fever" in summary

    # Verify serialization round-trip
    d = cm.to_dict()
    restored = ConversationManager.from_dict(d)
    assert restored.session_id == "multi_turn_test"
    assert restored.message_count == 2
    assert "headache" in restored.health_context["symptoms_mentioned"]

    print("✓ Multi-turn conversation manager test passed")


def test_safety_dangerous_pattern_correction():
    """Test that dangerous patterns are corrected in the response text."""
    from src.modules.safety_guardrails import check_safety

    _no_llm_issues = {"has_issues": False, "issues": []}

    with patch("src.modules.safety_guardrails._llm_safety_review", return_value=_no_llm_issues):
        result = check_safety(
            response_text="You should stop taking your medication immediately. Please consult a healthcare professional.",
            urgency_level="ROUTINE",
            user_message="should I stop my meds?"
        )
        assert not result["is_safe"]
        # Verify the dangerous text was removed/replaced
        assert "stop taking your medication" not in result["corrected_response"].lower() or \
               "[removed for safety]" in result["corrected_response"].lower()

    print("✓ Safety dangerous pattern correction test passed")


def test_pipeline_empty_input():
    """Test that empty input is handled gracefully."""
    try:
        from src.pipeline import process_message
    except Exception as exc:
        import pytest
        pytest.skip(f"Cannot import src.pipeline (chromadb issue): {exc}")

    result = process_message("")
    assert result["response"]["urgency_level"] == "N/A"
    assert "empty" in result["response"]["text"].lower() or "describe" in result["response"]["text"].lower()

    result2 = process_message("   ")
    assert result2["response"]["urgency_level"] == "N/A"

    print("✓ Pipeline empty input test passed")


if __name__ == "__main__":
    test_intent_emergency_keywords()
    test_urgency_emergency_patterns()
    test_conversation_manager()
    test_response_formatter()
    test_safety_guardrails_patterns()
    test_appointment_emergency_override()
    test_safety_poison_control()
    test_symptom_extractor_structure()
    test_conversation_manager_multiturn()
    test_safety_dangerous_pattern_correction()
    test_pipeline_empty_input()
    print("\n✅ All module tests passed!")
