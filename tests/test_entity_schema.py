# tests/test_entity_schema.py

"""
Tests for the structured entity schema module.
Verifies symptom ontology, condition schema, urgency rules,
specialist map, and all lookup functions.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_pipeline.entity_schema import (
    CONDITION_SCHEMA,
    SYMPTOM_ONTOLOGY,
    URGENCY_RULES,
    SPECIALIST_MAP,
    lookup_condition,
    get_conditions_for_symptom,
    get_red_flags_for_symptoms,
    check_urgency_rules,
    get_specialist_info,
)


def test_symptom_ontology_structure():
    """All symptom entries have required keys."""
    required_keys = {"body_system", "icd10", "common_causes", "red_flag_modifiers"}
    assert len(SYMPTOM_ONTOLOGY) >= 15, "Should have at least 15 symptoms"

    for name, entry in SYMPTOM_ONTOLOGY.items():
        for key in required_keys:
            assert key in entry, f"Symptom '{name}' missing key '{key}'"
        assert isinstance(entry["common_causes"], list)
        assert isinstance(entry["red_flag_modifiers"], list)
        assert len(entry["icd10"]) > 0, f"Symptom '{name}' missing ICD-10"


def test_condition_schema_structure():
    """All condition entries have required keys."""
    required_keys = {
        "display_name", "icd10", "symptoms", "key_features",
        "default_urgency", "urgency_level", "specialist", "action",
        "risk_factors", "red_flags", "self_care_okay",
    }
    assert len(CONDITION_SCHEMA) >= 10, "Should have at least 10 conditions"

    for name, entry in CONDITION_SCHEMA.items():
        for key in required_keys:
            assert key in entry, f"Condition '{name}' missing key '{key}'"
        assert entry["default_urgency"] in {
            "EMERGENCY", "URGENT", "SOON", "ROUTINE", "SELF_CARE"
        }, f"Condition '{name}' has invalid urgency: {entry['default_urgency']}"
        assert isinstance(entry["icd10"], list)
        assert isinstance(entry["symptoms"], list)


def test_urgency_rules_structure():
    """All urgency rules have required keys."""
    required_keys = {"rule_id", "description", "trigger_symptoms", "trigger_modifiers", "escalate_to"}
    assert len(URGENCY_RULES) >= 5, "Should have at least 5 urgency rules"

    for rule in URGENCY_RULES:
        for key in required_keys:
            assert key in rule, f"Rule '{rule.get('rule_id', '?')}' missing key '{key}'"


def test_specialist_map_completeness():
    """Specialist map has required keys and covers all conditions."""
    assert len(SPECIALIST_MAP) >= 10, "Should have at least 10 specialists"

    for key, info in SPECIALIST_MAP.items():
        assert "display_name" in info
        assert "where" in info
        assert "when" in info

    # Every condition's specialist should be in the map (or None)
    for cond_name, cond in CONDITION_SCHEMA.items():
        spec = cond.get("specialist")
        if spec is not None:
            assert spec in SPECIALIST_MAP, (
                f"Condition '{cond_name}' references specialist '{spec}' "
                f"not in SPECIALIST_MAP"
            )


def test_lookup_condition():
    """lookup_condition returns correct data or None."""
    mi = lookup_condition("myocardial_infarction")
    assert mi is not None
    assert mi["default_urgency"] == "EMERGENCY"
    assert "I21.9" in mi["icd10"]

    assert lookup_condition("nonexistent_condition_xyz") is None


def test_get_conditions_for_symptom():
    """Get all conditions linked to chest_pain."""
    results = get_conditions_for_symptom("chest_pain")
    assert len(results) >= 2, "chest_pain should map to multiple conditions"

    names = [r["condition"] for r in results]
    assert "myocardial_infarction" in names
    assert "pulmonary_embolism" in names


def test_get_red_flags():
    """Get red flags for headache and fever."""
    red_flags = get_red_flags_for_symptoms(["headache", "fever"])
    assert len(red_flags) >= 4, "Should have multiple red flags"

    symptoms_covered = {rf["symptom"] for rf in red_flags}
    assert "headache" in symptoms_covered
    assert "fever" in symptoms_covered


def test_check_urgency_rules_emergency():
    """Chest pain with crushing should trigger EMERGENCY."""
    result = check_urgency_rules(
        symptom_keys=["chest_pain"],
        user_text_lower="i have crushing chest pain radiating to my arm"
    )
    assert result == "EMERGENCY"


def test_check_urgency_rules_suicidal():
    """Depressed mood with suicidal ideation should trigger EMERGENCY."""
    result = check_urgency_rules(
        symptom_keys=["depressed_mood"],
        user_text_lower="i feel depressed and suicidal"
    )
    assert result == "EMERGENCY"


def test_check_urgency_rules_no_match():
    """Normal symptoms without red flags should return None."""
    result = check_urgency_rules(
        symptom_keys=["cough"],
        user_text_lower="i have a mild cough for 2 days"
    )
    assert result is None


def test_get_specialist_info():
    """Get specialist details."""
    info = get_specialist_info("emergency_medicine")
    assert info is not None
    assert "Emergency" in info["display_name"]

    assert get_specialist_info("nonexistent_specialty") is None


def test_emergency_conditions_are_emergency():
    """All conditions with urgency_level 1 should be EMERGENCY."""
    for name, cond in CONDITION_SCHEMA.items():
        if cond["urgency_level"] == 1:
            assert cond["default_urgency"] == "EMERGENCY", (
                f"Condition '{name}' has urgency_level=1 but default_urgency={cond['default_urgency']}"
            )
            assert cond["self_care_okay"] is False, (
                f"EMERGENCY condition '{name}' should not allow self-care"
            )


if __name__ == "__main__":
    test_symptom_ontology_structure()
    test_condition_schema_structure()
    test_urgency_rules_structure()
    test_specialist_map_completeness()
    test_lookup_condition()
    test_get_conditions_for_symptom()
    test_get_red_flags()
    test_check_urgency_rules_emergency()
    test_check_urgency_rules_suicidal()
    test_check_urgency_rules_no_match()
    test_get_specialist_info()
    test_emergency_conditions_are_emergency()
    print("\n✅ All entity schema tests passed!")
