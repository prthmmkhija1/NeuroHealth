# tests/test_modules.py

"""
Tests for individual modules (can run on HP-INT without GPU).
Tests keyword-based logic and pure Python modules only.
LLM-dependent tests are skipped if model is not loaded.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_intent_emergency_keywords():
    """Test that emergency keywords trigger EMERGENCY intent without LLM."""
    from src.modules.intent_recognizer import classify_intent

    emergency_messages = [
        "I think I'm having a heart attack",
        "I can't breathe at all",
        "Someone has passed out and is unconscious",
        "I think I might kill myself",
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

    # Test: emergency response missing emergency language
    result = check_safety(
        response_text="You should rest and drink fluids.",
        urgency_level="EMERGENCY",
        user_message="chest pain"
    )
    assert not result["is_safe"], "Should flag missing emergency redirect"
    assert "MISSING_EMERGENCY_REDIRECT" in result["issues"]
    assert "911" in result["corrected_response"]

    # Test: dangerous pattern detection
    result = check_safety(
        response_text="You should stop taking your medication immediately.",
        urgency_level="ROUTINE",
        user_message="medication question"
    )
    assert not result["is_safe"], "Should flag dangerous medication advice"

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


if __name__ == "__main__":
    test_intent_emergency_keywords()
    test_urgency_emergency_patterns()
    test_conversation_manager()
    test_response_formatter()
    test_safety_guardrails_patterns()
    test_appointment_emergency_override()
    print("\n✅ All module tests passed!")
