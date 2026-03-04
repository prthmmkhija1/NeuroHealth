# evaluation/ablation_study.py

"""
Ablation Study Module
-----------------------
Per the OSRE26 spec: "ablation studies" are required to evaluate each
component's contribution to overall system performance.

This module systematically disables one pipeline component at a time
and re-runs the benchmark suite to measure the impact.

Components tested:
  1. RAG retrieval (disable context → LLM generates from parametric knowledge only)
  2. Safety guardrails (disable post-generation safety checks)
  3. Intent recognition (disable intent classification → treat everything as SYMPTOM_CHECK)
  4. Urgency assessment (disable → always returns ROUTINE)
  5. Conversation history (disable → no multi-turn context)

Usage:
    python evaluation/ablation_study.py
"""

import sys
import json
import time
from pathlib import Path
from copy import deepcopy

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.benchmarks import TEST_CASES, _load_json_test_cases


# ── Ablated Pipeline Functions ─────────────────────────────────────────

def _pipeline_no_rag(user_message, session_id=None):
    """Pipeline with RAG retrieval disabled — LLM uses only parametric knowledge."""
    from src.modules.intent_recognizer import classify_intent
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.urgency_assessor import assess_urgency
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.safety_guardrails import check_safety
    from src.modules.conversation_manager import ConversationManager
    from src.modules.response_formatter import format_response
    from src.rag.generator import generate_response

    session = ConversationManager()
    session.add_user_message(user_message)

    intent_info = classify_intent(user_message)

    if intent_info["intent"] == "OUT_OF_SCOPE":
        return {
            "session_id": session.session_id,
            "response": {
                "text": "I'm NeuroHealth, a health-focused assistant.",
                "urgency_level": "N/A",
                "urgency_color": "#888888",
                "metadata": {}
            },
            "debug": {"intent": intent_info}
        }

    symptoms = extract_symptoms(user_message)
    # NO RAG retrieval — pass empty context
    medical_context = "No retrieved context (ablation: RAG disabled)."
    urgency = assess_urgency(user_message, symptoms)
    appointment = recommend_appointment(user_message, urgency, symptoms)
    raw_response = generate_response(user_message, medical_context)
    safety_check = check_safety(raw_response, urgency["level"], user_message)
    formatted = format_response(safety_check["corrected_response"], urgency, appointment, user_message)

    return {
        "session_id": session.session_id,
        "response": formatted,
        "debug": {"intent": intent_info, "symptoms": symptoms, "urgency": urgency}
    }


def _pipeline_no_safety(user_message, session_id=None):
    """Pipeline with safety guardrails disabled."""
    from src.modules.intent_recognizer import classify_intent
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.urgency_assessor import assess_urgency
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.conversation_manager import ConversationManager
    from src.modules.response_formatter import format_response
    from src.rag.retriever import retrieve_context
    from src.rag.generator import generate_response

    session = ConversationManager()
    session.add_user_message(user_message)

    intent_info = classify_intent(user_message)

    if intent_info["intent"] == "OUT_OF_SCOPE":
        return {
            "session_id": session.session_id,
            "response": {
                "text": "I'm NeuroHealth, a health-focused assistant.",
                "urgency_level": "N/A",
                "urgency_color": "#888888",
                "metadata": {}
            },
            "debug": {"intent": intent_info}
        }

    symptoms = extract_symptoms(user_message)
    medical_context = retrieve_context(user_message)
    urgency = assess_urgency(user_message, symptoms)
    appointment = recommend_appointment(user_message, urgency, symptoms)
    raw_response = generate_response(user_message, medical_context)
    # NO safety check — pass raw response directly
    formatted = format_response(raw_response, urgency, appointment, user_message)

    return {
        "session_id": session.session_id,
        "response": formatted,
        "debug": {"intent": intent_info, "symptoms": symptoms, "urgency": urgency}
    }


def _pipeline_no_intent(user_message, session_id=None):
    """Pipeline with intent recognition disabled — always assumes SYMPTOM_CHECK."""
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.urgency_assessor import assess_urgency
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.safety_guardrails import check_safety
    from src.modules.conversation_manager import ConversationManager
    from src.modules.response_formatter import format_response
    from src.rag.retriever import retrieve_context
    from src.rag.generator import generate_response

    session = ConversationManager()
    session.add_user_message(user_message)

    # NO intent recognition — always SYMPTOM_CHECK
    intent_info = {"intent": "SYMPTOM_CHECK", "confidence": 1.0, "reasoning": "ablation"}

    symptoms = extract_symptoms(user_message)
    medical_context = retrieve_context(user_message)
    urgency = assess_urgency(user_message, symptoms)
    appointment = recommend_appointment(user_message, urgency, symptoms)
    raw_response = generate_response(user_message, medical_context)
    safety_check = check_safety(raw_response, urgency["level"], user_message)
    formatted = format_response(safety_check["corrected_response"], urgency, appointment, user_message)

    return {
        "session_id": session.session_id,
        "response": formatted,
        "debug": {"intent": intent_info, "symptoms": symptoms, "urgency": urgency}
    }


def _pipeline_no_urgency(user_message, session_id=None):
    """Pipeline with urgency assessment disabled — always returns ROUTINE."""
    from src.modules.intent_recognizer import classify_intent
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.safety_guardrails import check_safety
    from src.modules.conversation_manager import ConversationManager
    from src.modules.response_formatter import format_response
    from src.rag.retriever import retrieve_context
    from src.rag.generator import generate_response

    session = ConversationManager()
    session.add_user_message(user_message)

    intent_info = classify_intent(user_message)

    if intent_info["intent"] == "OUT_OF_SCOPE":
        return {
            "session_id": session.session_id,
            "response": {
                "text": "I'm NeuroHealth, a health-focused assistant.",
                "urgency_level": "N/A",
                "urgency_color": "#888888",
                "metadata": {}
            },
            "debug": {"intent": intent_info}
        }

    symptoms = extract_symptoms(user_message)
    medical_context = retrieve_context(user_message)
    # NO urgency assessment — always ROUTINE
    urgency = {
        "level": "ROUTINE", "level_number": 4,
        "recommendation": "Schedule a regular appointment",
        "reasoning": "ablation: urgency disabled",
        "call_to_action": "Schedule an appointment.",
        "warning_signs": [], "color_code": "GREEN"
    }
    appointment = recommend_appointment(user_message, urgency, symptoms)
    raw_response = generate_response(user_message, medical_context)
    safety_check = check_safety(raw_response, urgency["level"], user_message)
    formatted = format_response(safety_check["corrected_response"], urgency, appointment, user_message)

    return {
        "session_id": session.session_id,
        "response": formatted,
        "debug": {"intent": intent_info, "symptoms": symptoms, "urgency": urgency}
    }


def _pipeline_no_conversation_history(user_message, session_id=None):
    """Pipeline with conversation history disabled — no multi-turn context."""
    from src.modules.intent_recognizer import classify_intent
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.urgency_assessor import assess_urgency
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.safety_guardrails import check_safety
    from src.modules.response_formatter import format_response
    from src.rag.retriever import retrieve_context
    from src.rag.generator import generate_response

    # NO conversation manager — no multi-turn context, fresh state every turn
    intent_info = classify_intent(user_message)

    if intent_info["intent"] == "OUT_OF_SCOPE":
        return {
            "session_id": "ablation_no_history",
            "response": {
                "text": "I'm NeuroHealth, a health-focused assistant.",
                "urgency_level": "N/A",
                "urgency_color": "#888888",
                "metadata": {}
            },
            "debug": {"intent": intent_info}
        }

    symptoms = extract_symptoms(user_message)
    medical_context = retrieve_context(user_message)
    urgency = assess_urgency(user_message, symptoms)
    appointment = recommend_appointment(user_message, urgency, symptoms)
    # No conversation history passed to generator
    raw_response = generate_response(user_message, medical_context)
    safety_check = check_safety(raw_response, urgency["level"], user_message)
    formatted = format_response(safety_check["corrected_response"], urgency, appointment, user_message)

    return {
        "session_id": "ablation_no_history",
        "response": formatted,
        "debug": {"intent": intent_info, "symptoms": symptoms, "urgency": urgency}
    }


# ── Ablation Runner ───────────────────────────────────────────────────

ABLATION_CONFIGS = {
    "full_pipeline": None,  # None = use the real pipeline
    "no_rag": _pipeline_no_rag,
    "no_safety": _pipeline_no_safety,
    "no_intent": _pipeline_no_intent,
    "no_urgency": _pipeline_no_urgency,
    "no_conversation_history": _pipeline_no_conversation_history,
}


def _score_run(pipeline_fn, test_cases):
    """Run a set of test cases and return scores."""
    emergency_cases = [t for t in test_cases if t.get("expected_urgency") == "EMERGENCY"]
    emergency_correct = 0
    total_urgency = 0
    urgency_correct = 0
    total_intent = 0
    intent_correct = 0
    safety_passed = 0
    total = len(test_cases)

    for test in test_cases:
        try:
            result = pipeline_fn(test["message"])
            response_text = result["response"]["text"].lower()
            urgency_level = result["response"]["urgency_level"]
            detected_intent = result.get("debug", {}).get("intent", {}).get("intent", "")

            if "expected_urgency" in test:
                total_urgency += 1
                if urgency_level == test["expected_urgency"]:
                    urgency_correct += 1
                    if test["expected_urgency"] == "EMERGENCY":
                        emergency_correct += 1

            if "expected_intent" in test:
                total_intent += 1
                if detected_intent == test["expected_intent"]:
                    intent_correct += 1

            forbidden = test.get("must_not_contain", [])
            if all(phrase not in response_text for phrase in forbidden):
                safety_passed += 1

        except Exception:
            pass

    return {
        "emergency_recall": emergency_correct / len(emergency_cases) if emergency_cases else 1.0,
        "urgency_accuracy": urgency_correct / total_urgency if total_urgency else 0,
        "intent_accuracy": intent_correct / total_intent if total_intent else 0,
        "safety_pass_rate": safety_passed / total if total else 0,
    }


def run_ablation_study():
    """
    Runs the full ablation study.
    For each configuration, runs all benchmark test cases and reports metrics.
    """
    from src.pipeline import process_message

    # Merge test cases
    json_cases = _load_json_test_cases()
    existing_ids = {t["id"] for t in TEST_CASES}
    all_tests = TEST_CASES + [c for c in json_cases if c["id"] not in existing_ids]

    print("=" * 70)
    print("ABLATION STUDY — Component Contribution Analysis")
    print("=" * 70)
    print(f"Running {len(all_tests)} test cases across {len(ABLATION_CONFIGS)} configurations\n")

    results = {}

    for config_name, ablated_fn in ABLATION_CONFIGS.items():
        fn = process_message if ablated_fn is None else ablated_fn
        label = config_name.replace("_", " ").title()
        print(f"\n{'─'*50}")
        print(f"Configuration: {label}")
        print(f"{'─'*50}")

        start = time.time()
        scores = _score_run(fn, all_tests)
        elapsed = time.time() - start

        scores["time_seconds"] = round(elapsed, 1)
        results[config_name] = scores

        print(f"  Emergency Recall:  {scores['emergency_recall']:.1%}")
        print(f"  Urgency Accuracy:  {scores['urgency_accuracy']:.1%}")
        print(f"  Intent Accuracy:   {scores['intent_accuracy']:.1%}")
        print(f"  Safety Pass Rate:  {scores['safety_pass_rate']:.1%}")
        print(f"  Time:              {scores['time_seconds']}s")

    # ── Comparison Table ────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("ABLATION COMPARISON SUMMARY")
    print("=" * 70)
    header = f"{'Configuration':<20} {'Emerg Recall':>13} {'Urgency Acc':>12} {'Intent Acc':>11} {'Safety':>8} {'Time':>6}"
    print(header)
    print("-" * 70)

    baseline = results.get("full_pipeline", {})
    for config_name, scores in results.items():
        label = config_name.replace("_", " ").title()
        er = f"{scores['emergency_recall']:.1%}"
        ua = f"{scores['urgency_accuracy']:.1%}"
        ia = f"{scores['intent_accuracy']:.1%}"
        sp = f"{scores['safety_pass_rate']:.1%}"
        t = f"{scores['time_seconds']}s"
        print(f"{label:<20} {er:>13} {ua:>12} {ia:>11} {sp:>8} {t:>6}")

    # ── Delta from baseline ─────────────────────────────────────────
    if baseline:
        print(f"\n{'Configuration':<20} {'ΔEmerg':>8} {'ΔUrgency':>10} {'ΔIntent':>9} {'ΔSafety':>9}")
        print("-" * 56)
        for config_name, scores in results.items():
            if config_name == "full_pipeline":
                continue
            label = config_name.replace("_", " ").title()
            de = scores["emergency_recall"] - baseline["emergency_recall"]
            du = scores["urgency_accuracy"] - baseline["urgency_accuracy"]
            di = scores["intent_accuracy"] - baseline["intent_accuracy"]
            ds = scores["safety_pass_rate"] - baseline["safety_pass_rate"]
            print(f"{label:<20} {de:>+8.1%} {du:>+10.1%} {di:>+9.1%} {ds:>+9.1%}")

    # Save results
    output_path = Path(__file__).parent / "ablation_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_path}")

    return results


if __name__ == "__main__":
    run_ablation_study()
