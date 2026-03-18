# evaluation/inference_profiler.py

"""
Inference Efficiency Profiler
-------------------------------
Per the OSRE26 spec: "inference efficiency optimization."

Profiles the NeuroHealth pipeline to measure latency of each component,
identifies bottlenecks, and provides optimization recommendations.

Usage:
    python evaluation/inference_profiler.py
"""

import json
import sys
import time
from pathlib import Path
from statistics import mean, stdev

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── Test Messages for Profiling ────────────────────────────────────────

PROFILE_MESSAGES = [
    "I have a headache",
    "I'm having crushing chest pain and my left arm hurts",
    "What are common symptoms of the flu?",
    "I've been feeling very anxious and can't sleep for weeks",
    "I need to find a dermatologist near me",
]


def _time_component(fn, *args, **kwargs):
    """Time a single function call."""
    start = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed = time.perf_counter() - start
    return result, elapsed


def profile_pipeline_components(user_message):
    """
    Profiles each component of the pipeline individually.
    Returns a dict of component → time in seconds.
    """
    from src.modules.appointment_recommender import recommend_appointment
    from src.modules.intent_recognizer import classify_intent
    from src.modules.response_formatter import format_response
    from src.modules.safety_guardrails import check_safety
    from src.modules.symptom_extractor import extract_symptoms
    from src.modules.urgency_assessor import assess_urgency
    from src.rag.generator import generate_response
    from src.rag.retriever import retrieve_context

    timings = {}

    # Intent Recognition
    intent_info, t = _time_component(classify_intent, user_message)
    timings["intent_recognition"] = t

    # Symptom Extraction
    symptoms, t = _time_component(extract_symptoms, user_message)
    timings["symptom_extraction"] = t

    # RAG Retrieval
    context, t = _time_component(retrieve_context, user_message)
    timings["rag_retrieval"] = t

    # Urgency Assessment
    urgency, t = _time_component(assess_urgency, user_message, symptoms)
    timings["urgency_assessment"] = t

    # Appointment Recommendation
    appointment, t = _time_component(
        recommend_appointment, user_message, urgency, symptoms
    )
    timings["appointment_recommendation"] = t

    # Response Generation (LLM)
    raw_response, t = _time_component(generate_response, user_message, context)
    timings["response_generation"] = t

    # Safety Check
    safety, t = _time_component(
        check_safety, raw_response, urgency["level"], user_message
    )
    timings["safety_check"] = t

    # Response Formatting
    formatted, t = _time_component(
        format_response,
        safety["corrected_response"],
        urgency,
        appointment,
        user_message,
    )
    timings["response_formatting"] = t

    timings["total"] = sum(timings.values())

    return timings


def run_profiling():
    """
    Runs profiling across multiple messages and reports stats.
    """
    print("=" * 60)
    print("INFERENCE EFFICIENCY PROFILER")
    print("=" * 60)

    # Warm-up run (first LLM call loads the model)
    print("\n[Warm-up] Loading model...")
    from src.pipeline import process_message

    warmup_start = time.perf_counter()
    process_message("test warm-up")
    warmup_time = time.perf_counter() - warmup_start
    print(f"  Model loaded in {warmup_time:.1f}s")

    # Profile each message
    all_timings = []
    for msg in PROFILE_MESSAGES:
        print(f"\nProfiling: '{msg[:60]}'")
        timings = profile_pipeline_components(msg)
        all_timings.append(timings)

        # Print per-component times
        for component, elapsed in sorted(timings.items(), key=lambda x: -x[1]):
            if component == "total":
                continue
            pct = (elapsed / timings["total"]) * 100
            bar = "█" * int(pct / 2)
            print(f"  {component:<28} {elapsed:>6.3f}s  ({pct:>5.1f}%) {bar}")
        print(f"  {'TOTAL':<28} {timings['total']:>6.3f}s")

    # ── Aggregate Statistics ────────────────────────────────────
    print("\n" + "=" * 60)
    print("AGGREGATE STATISTICS")
    print("=" * 60)

    components = [k for k in all_timings[0].keys() if k != "total"]
    print(
        f"\n{'Component':<28} {'Mean':>7} {'StdDev':>7} {'Min':>7} {'Max':>7} {'% Total':>8}"
    )
    print("-" * 64)

    total_means = {}
    for comp in components:
        times = [t[comp] for t in all_timings]
        m = mean(times)
        s = stdev(times) if len(times) > 1 else 0
        mn = min(times)
        mx = max(times)
        total_means[comp] = m
        print(f"  {comp:<26} {m:>6.3f}s {s:>6.3f}s {mn:>6.3f}s {mx:>6.3f}s")

    total_times = [t["total"] for t in all_timings]
    total_m = mean(total_times)
    print(f"\n  {'TOTAL':<26} {total_m:>6.3f}s")

    # Percentage breakdown
    print(f"\n{'Bottleneck Analysis':}")
    sorted_comps = sorted(total_means.items(), key=lambda x: -x[1])
    for comp, m in sorted_comps:
        pct = (m / total_m) * 100
        bar = "█" * int(pct / 2)
        print(f"  {comp:<28} {pct:>5.1f}% {bar}")

    # ── Recommendations ─────────────────────────────────────────
    print("\n" + "=" * 60)
    print("OPTIMIZATION RECOMMENDATIONS")
    print("=" * 60)

    biggest_bottleneck = sorted_comps[0][0]
    print(f"\n  Biggest bottleneck: {biggest_bottleneck}")

    if (
        "generation" in biggest_bottleneck
        or "response_generation" == biggest_bottleneck
    ):
        print("  → Consider: smaller model, quantization, vLLM/TGI serving, KV cache")
    if "rag_retrieval" in biggest_bottleneck:
        print("  → Consider: pre-computed embeddings, HNSW index tuning, caching")
    if "intent" in biggest_bottleneck:
        print("  → Consider: lightweight classifier (DistilBERT) instead of LLM")
    if "symptom" in biggest_bottleneck:
        print("  → Consider: NER model (spaCy/scispaCy) instead of LLM extraction")
    if "safety" in biggest_bottleneck:
        print(
            "  → Consider: regex-only mode (skip LLM safety review) for low-risk queries"
        )

    if total_m > 10:
        print(f"\n  ⚠️ Average total latency ({total_m:.1f}s) exceeds 10s target.")
        print("  Consider: model quantization, batching, or async processing.")
    elif total_m > 5:
        print(f"\n  ⚡ Average total latency ({total_m:.1f}s) is moderate.")
    else:
        print(
            f"\n  ✅ Average total latency ({total_m:.1f}s) is within acceptable range."
        )

    # Save results
    output_path = Path(__file__).parent / "profiling_results.json"
    results = {
        "warmup_time": warmup_time,
        "messages_profiled": len(PROFILE_MESSAGES),
        "average_total_latency": total_m,
        "component_means": {k: round(v, 4) for k, v in total_means.items()},
        "all_timings": all_timings,
    }
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Results saved to {output_path}")

    return results


if __name__ == "__main__":
    run_profiling()
