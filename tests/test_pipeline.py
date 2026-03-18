# tests/test_pipeline.py

"""
End-to-end pipeline tests.
Requires both the vector store AND the LLM model to be loaded.
Best run on JLAB-GPU with A100.
"""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.helpers import import_pipeline, vector_store_ready

# Use shared helpers from conftest
_vector_store_ready = vector_store_ready
_import_pipeline = import_pipeline


def test_emergency_detection():
    """Test that the pipeline correctly identifies emergencies."""
    process_message = _import_pipeline()

    result = process_message("I'm having crushing chest pain and my left arm is numb")

    assert (
        result["response"]["urgency_level"] == "EMERGENCY"
    ), f"Expected EMERGENCY, got {result['response']['urgency_level']}"
    assert (
        "911" in result["response"]["text"].lower()
    ), "Emergency response should mention 911"

    print("✓ Emergency detection test passed")


def test_out_of_scope():
    """Test that non-health questions are handled correctly."""
    process_message = _import_pipeline()

    result = process_message("What is the capital of France?")

    assert (
        result["response"]["urgency_level"] == "N/A"
    ), f"Expected N/A urgency, got {result['response']['urgency_level']}"
    assert (
        "health" in result["response"]["text"].lower()
    ), "Out-of-scope response should mention health"

    print("✓ Out-of-scope test passed")


def test_session_continuity():
    """Test that conversations maintain context across turns."""
    process_message = _import_pipeline()

    # First message
    result1 = process_message("I have a headache")
    session_id = result1["session_id"]

    # Second message using same session
    result2 = process_message("It started two days ago", session_id=session_id)

    assert result2["session_id"] == session_id, "Session ID should persist"

    print("✓ Session continuity test passed")


def test_routine_query():
    """Test a routine health question."""
    process_message = _import_pipeline()

    result = process_message("I have a runny nose and mild cough since yesterday")

    urgency = result["response"]["urgency_level"]
    assert urgency in [
        "ROUTINE",
        "SELF_CARE",
        "SOON",
    ], f"Mild cold should be ROUTINE/SELF_CARE/SOON, got {urgency}"
    assert (
        "911" not in result["response"]["text"].lower()
    ), "Routine response should NOT mention 911"

    print("✓ Routine query test passed")


if __name__ == "__main__":
    print("Running end-to-end pipeline tests...")
    print("(These require the vector store and LLM model to be loaded)\n")

    try:
        test_emergency_detection()
        test_out_of_scope()
        test_session_continuity()
        test_routine_query()
        print("\n✅ All pipeline tests passed!")
    except Exception as e:
        print(f"\n⚠ Pipeline test failed: {e}")
        print("Make sure you've run the data pipeline and have the model available.")
