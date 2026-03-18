# tests/test_baseline_comparison.py

"""
Tests for the baseline comparison evaluation module.
Verifies the keyword baseline triage and scoring logic.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from evaluation.baseline_comparison import (
    COMPARISON_CASES,
    EXTERNAL_BASELINES,
    _score_system,
    baseline_keyword_triage,
)


def test_keyword_baseline_emergency():
    """Keyword baseline detects emergency keywords."""
    result = baseline_keyword_triage("I'm having crushing chest pain")
    assert result["urgency"] == "EMERGENCY"
    assert result["method"] == "keyword_match"


def test_keyword_baseline_urgent():
    """Keyword baseline detects urgent keywords."""
    result = baseline_keyword_triage("I have a high fever of 103 degrees")
    assert result["urgency"] == "URGENT"


def test_keyword_baseline_routine():
    """Keyword baseline detects routine keywords."""
    result = baseline_keyword_triage("I have a mild headache")
    assert result["urgency"] == "ROUTINE"


def test_keyword_baseline_self_care():
    """Keyword baseline detects self-care keywords."""
    result = baseline_keyword_triage("I have a paper cut on my finger")
    assert result["urgency"] == "SELF_CARE"


def test_keyword_baseline_fallback():
    """Keyword baseline falls back to ROUTINE for unknown input."""
    result = baseline_keyword_triage("I feel a bit off today")
    assert result["urgency"] == "ROUTINE"
    assert result["method"] == "fallback"


def test_external_baselines_present():
    """External baseline references exist and have required keys."""
    assert len(EXTERNAL_BASELINES) >= 4
    for name, info in EXTERNAL_BASELINES.items():
        assert "description" in info
        assert "source" in info


def test_comparison_cases_structure():
    """All comparison cases have required fields."""
    assert len(COMPARISON_CASES) >= 15
    for case in COMPARISON_CASES:
        assert "id" in case
        assert "message" in case
        assert "expected_urgency" in case
        assert case["expected_urgency"] in {
            "EMERGENCY",
            "URGENT",
            "ROUTINE",
            "SELF_CARE",
        }


def test_score_system_runs():
    """_score_system produces valid metrics for the keyword baseline."""
    scores = _score_system(baseline_keyword_triage, COMPARISON_CASES)
    assert 0 <= scores["urgency_accuracy"] <= 1
    assert 0 <= scores["emergency_recall"] <= 1
    assert scores["total"] == len(COMPARISON_CASES)
    assert scores["correct"] <= scores["total"]


def test_keyword_baseline_suicidal():
    """Keyword baseline detects suicidal ideation as emergency."""
    result = baseline_keyword_triage("I want to die, I can't take it anymore")
    assert result["urgency"] == "EMERGENCY"


def test_keyword_baseline_overdose():
    """Keyword baseline detects overdose as emergency."""
    result = baseline_keyword_triage("I took too many pills, possible overdose")
    assert result["urgency"] == "EMERGENCY"


if __name__ == "__main__":
    test_keyword_baseline_emergency()
    test_keyword_baseline_urgent()
    test_keyword_baseline_routine()
    test_keyword_baseline_self_care()
    test_keyword_baseline_fallback()
    test_external_baselines_present()
    test_comparison_cases_structure()
    test_score_system_runs()
    test_keyword_baseline_suicidal()
    test_keyword_baseline_overdose()
    print("\n✅ All baseline comparison tests passed!")
