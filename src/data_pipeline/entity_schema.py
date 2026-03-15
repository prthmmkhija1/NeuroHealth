# src/data_pipeline/entity_schema.py

"""
Structured Entity Schema
--------------------------
Per OSRE spec: "Design structured representations for symptoms,
conditions, urgency levels, and appointment recommendations to
enable effective retrieval and reasoning."

This module defines a structured medical entity schema that maps:
  condition → symptoms → urgency_default → specialist → ICD-10 codes
  → risk_factors → red_flags → self_care_okay

Used by the pipeline for structured reasoning during retrieval,
urgency assessment, and appointment recommendation.

Usage:
    from src.data_pipeline.entity_schema import (
        CONDITION_SCHEMA, SYMPTOM_ONTOLOGY, URGENCY_RULES,
        lookup_condition, get_red_flags_for_symptoms
    )
"""

import json
from pathlib import Path

SCHEMA_DIR = Path("data/processed")
SCHEMA_DIR.mkdir(parents=True, exist_ok=True)


# ── Symptom Ontology ────────────────────────────────────────────────
# Maps symptom names to body systems and standard descriptors

SYMPTOM_ONTOLOGY = {
    # ── Head / Neurological ──
    "headache": {
        "body_system": "neurological",
        "icd10": "R51.9",
        "common_causes": ["tension", "migraine", "sinusitis", "dehydration", "hypertension"],
        "red_flag_modifiers": ["sudden onset", "worst ever", "thunderclap", "with fever and stiff neck"],
    },
    "dizziness": {
        "body_system": "neurological",
        "icd10": "R42",
        "common_causes": ["BPPV", "dehydration", "orthostatic hypotension", "anemia", "medication side effect"],
        "red_flag_modifiers": ["with one-sided weakness", "with slurred speech", "with vision loss"],
    },
    "confusion": {
        "body_system": "neurological",
        "icd10": "R41.0",
        "common_causes": ["infection", "medication", "metabolic", "stroke", "delirium"],
        "red_flag_modifiers": ["sudden onset", "with fever", "in elderly"],
    },
    "seizure": {
        "body_system": "neurological",
        "icd10": "R56.9",
        "common_causes": ["epilepsy", "fever", "metabolic", "medication withdrawal"],
        "red_flag_modifiers": ["first ever", "lasting >5 min", "no recovery"],
    },
    # ── Cardiac / Cardiovascular ──
    "chest_pain": {
        "body_system": "cardiovascular",
        "icd10": "R07.9",
        "common_causes": ["musculoskeletal", "GERD", "anxiety", "angina", "MI", "PE"],
        "red_flag_modifiers": ["crushing", "radiating to arm/jaw", "with sweating", "with shortness of breath"],
    },
    "palpitations": {
        "body_system": "cardiovascular",
        "icd10": "R00.2",
        "common_causes": ["anxiety", "caffeine", "dehydration", "arrhythmia", "thyroid"],
        "red_flag_modifiers": ["with syncope", "with chest pain", "sustained >30 min"],
    },
    # ── Respiratory ──
    "shortness_of_breath": {
        "body_system": "respiratory",
        "icd10": "R06.0",
        "common_causes": ["asthma", "anxiety", "COPD", "pneumonia", "PE", "heart failure"],
        "red_flag_modifiers": ["sudden onset", "at rest", "with chest pain", "cyanosis"],
    },
    "cough": {
        "body_system": "respiratory",
        "icd10": "R05.9",
        "common_causes": ["viral URI", "allergies", "asthma", "GERD", "ACE inhibitor"],
        "red_flag_modifiers": ["with blood", "lasting >3 weeks", "with weight loss", "with night sweats"],
    },
    # ── Gastrointestinal ──
    "abdominal_pain": {
        "body_system": "gastrointestinal",
        "icd10": "R10.9",
        "common_causes": ["gastritis", "IBS", "constipation", "appendicitis", "gallstones"],
        "red_flag_modifiers": ["right lower quadrant", "sudden severe", "with rigid abdomen", "with fever"],
    },
    "nausea_vomiting": {
        "body_system": "gastrointestinal",
        "icd10": "R11.2",
        "common_causes": ["gastroenteritis", "food poisoning", "pregnancy", "medication", "migraine"],
        "red_flag_modifiers": ["blood in vomit", "projectile", "with severe abdominal pain", ">24 hours"],
    },
    "blood_in_stool": {
        "body_system": "gastrointestinal",
        "icd10": "K92.1",
        "common_causes": ["hemorrhoids", "fissure", "diverticulosis", "IBD", "colorectal cancer"],
        "red_flag_modifiers": ["black/tarry", "large volume", "with weight loss", "with anemia"],
    },
    # ── Musculoskeletal ──
    "back_pain": {
        "body_system": "musculoskeletal",
        "icd10": "M54.5",
        "common_causes": ["muscle strain", "disc herniation", "arthritis", "spinal stenosis"],
        "red_flag_modifiers": ["with leg weakness", "with bladder dysfunction", "after trauma", "with fever"],
    },
    "joint_pain": {
        "body_system": "musculoskeletal",
        "icd10": "M25.50",
        "common_causes": ["osteoarthritis", "gout", "rheumatoid arthritis", "injury", "infection"],
        "red_flag_modifiers": ["hot/red/swollen single joint", "with fever", "after trauma"],
    },
    # ── Dermatological ──
    "rash": {
        "body_system": "dermatological",
        "icd10": "R21",
        "common_causes": ["contact dermatitis", "eczema", "viral exanthem", "drug reaction", "fungal"],
        "red_flag_modifiers": ["with fever", "rapidly spreading", "with mucosal involvement", "blistering"],
    },
    # ── General / Systemic ──
    "fever": {
        "body_system": "systemic",
        "icd10": "R50.9",
        "common_causes": ["viral infection", "bacterial infection", "inflammatory", "medication"],
        "red_flag_modifiers": ["in infant <3 months", ">104°F", "lasting >3 days", "with rash", "immunocompromised"],
    },
    "fatigue": {
        "body_system": "systemic",
        "icd10": "R53.83",
        "common_causes": ["poor sleep", "stress", "anemia", "thyroid", "depression", "diabetes"],
        "red_flag_modifiers": ["with weight loss", "with night sweats", "lasting >2 weeks", "progressive"],
    },
    "weight_loss_unintentional": {
        "body_system": "systemic",
        "icd10": "R63.4",
        "common_causes": ["cancer", "hyperthyroidism", "diabetes", "depression", "malabsorption"],
        "red_flag_modifiers": [">5% in 6 months", "with night sweats", "with fatigue"],
    },
    # ── Mental Health ──
    "depressed_mood": {
        "body_system": "psychiatric",
        "icd10": "F32.9",
        "common_causes": ["major depressive disorder", "adjustment disorder", "grief", "substance use"],
        "red_flag_modifiers": ["with suicidal ideation", "with hopelessness", "with plan/intent"],
    },
    "anxiety": {
        "body_system": "psychiatric",
        "icd10": "F41.9",
        "common_causes": ["generalized anxiety", "panic disorder", "social anxiety", "PTSD"],
        "red_flag_modifiers": ["with panic attacks", "with avoidance behavior", "with substance use"],
    },
}


# ── Condition Schema ────────────────────────────────────────────────
# Maps conditions to structured clinical attributes

CONDITION_SCHEMA = {
    # ── Emergency Conditions ─────────────────────────────────────
    "myocardial_infarction": {
        "display_name": "Heart Attack (Myocardial Infarction)",
        "icd10": ["I21.9"],
        "symptoms": ["chest_pain", "shortness_of_breath", "nausea_vomiting", "palpitations"],
        "key_features": ["crushing/pressure chest pain", "radiation to left arm/jaw", "diaphoresis", "nausea"],
        "default_urgency": "EMERGENCY",
        "urgency_level": 1,
        "specialist": "emergency_medicine",
        "action": "Call 911 immediately",
        "risk_factors": ["age >45 male / >55 female", "smoking", "hypertension", "diabetes", "family history", "obesity"],
        "red_flags": ["crushing chest pain >10 min", "arm/jaw radiation", "sweating with chest pain"],
        "self_care_okay": False,
    },
    "stroke": {
        "display_name": "Stroke (Cerebrovascular Accident)",
        "icd10": ["I63.9", "I61.9"],
        "symptoms": ["confusion", "headache", "dizziness"],
        "key_features": ["facial drooping", "arm weakness", "speech difficulty", "sudden onset"],
        "default_urgency": "EMERGENCY",
        "urgency_level": 1,
        "specialist": "emergency_medicine",
        "action": "Call 911 immediately — FAST protocol",
        "risk_factors": ["hypertension", "atrial fibrillation", "diabetes", "smoking", "age >65"],
        "red_flags": ["sudden face drooping", "sudden arm weakness", "sudden speech difficulty"],
        "self_care_okay": False,
    },
    "anaphylaxis": {
        "display_name": "Anaphylaxis (Severe Allergic Reaction)",
        "icd10": ["T78.2"],
        "symptoms": ["shortness_of_breath", "rash"],
        "key_features": ["throat swelling", "difficulty breathing", "hives", "known allergen exposure"],
        "default_urgency": "EMERGENCY",
        "urgency_level": 1,
        "specialist": "emergency_medicine",
        "action": "Call 911, use EpiPen if available",
        "risk_factors": ["known allergies", "prior anaphylaxis", "asthma"],
        "red_flags": ["throat tightness/swelling", "difficulty breathing after exposure"],
        "self_care_okay": False,
    },
    "pulmonary_embolism": {
        "display_name": "Pulmonary Embolism",
        "icd10": ["I26.99"],
        "symptoms": ["chest_pain", "shortness_of_breath", "palpitations"],
        "key_features": ["sudden pleuritic chest pain", "rapid onset dyspnea", "tachycardia", "hemoptysis"],
        "default_urgency": "EMERGENCY",
        "urgency_level": 1,
        "specialist": "emergency_medicine",
        "action": "Call 911 — requires immediate imaging and treatment",
        "risk_factors": ["recent surgery", "immobility", "oral contraceptives", "DVT history", "cancer"],
        "red_flags": ["sudden chest pain with dyspnea", "coughing blood"],
        "self_care_okay": False,
    },
    # ── Urgent Conditions ────────────────────────────────────────
    "appendicitis": {
        "display_name": "Appendicitis",
        "icd10": ["K35.80"],
        "symptoms": ["abdominal_pain", "nausea_vomiting", "fever"],
        "key_features": ["RLQ pain", "migration from periumbilical", "rebound tenderness", "anorexia"],
        "default_urgency": "URGENT",
        "urgency_level": 2,
        "specialist": "general_surgery",
        "action": "Go to ER within hours",
        "risk_factors": ["age 10-30", "male", "family history"],
        "red_flags": ["worsening RLQ pain", "fever with RLQ pain"],
        "self_care_okay": False,
    },
    "preeclampsia": {
        "display_name": "Preeclampsia",
        "icd10": ["O14.90"],
        "symptoms": ["headache"],
        "key_features": ["hypertension in pregnancy", "proteinuria", "edema", "visual changes"],
        "default_urgency": "URGENT",
        "urgency_level": 2,
        "specialist": "obstetrics",
        "action": "Contact OB or go to labor and delivery immediately",
        "risk_factors": ["first pregnancy", "age >35", "obesity", "chronic hypertension", "family history"],
        "red_flags": ["BP >140/90 in pregnancy", "severe headache", "visual changes", "RUQ pain"],
        "self_care_okay": False,
    },
    "diabetic_ketoacidosis": {
        "display_name": "Diabetic Ketoacidosis (DKA)",
        "icd10": ["E10.10", "E11.10"],
        "symptoms": ["nausea_vomiting", "abdominal_pain", "confusion"],
        "key_features": ["fruity breath", "rapid breathing", "extreme thirst", "high blood sugar"],
        "default_urgency": "URGENT",
        "urgency_level": 2,
        "specialist": "endocrinology",
        "action": "ER evaluation urgently needed",
        "risk_factors": ["type 1 diabetes", "infection", "missed insulin doses"],
        "red_flags": ["blood sugar >300 with nausea", "fruity breath", "altered mental status"],
        "self_care_okay": False,
    },
    # ── Soon / Routine Conditions ────────────────────────────────
    "migraine": {
        "display_name": "Migraine",
        "icd10": ["G43.909"],
        "symptoms": ["headache", "nausea_vomiting"],
        "key_features": ["unilateral", "throbbing", "photophobia", "phonophobia", "aura"],
        "default_urgency": "ROUTINE",
        "urgency_level": 4,
        "specialist": "neurology",
        "action": "Schedule appointment with PCP or neurologist",
        "risk_factors": ["family history", "female", "hormonal changes", "stress"],
        "red_flags": ["new onset >50 years", "sudden thunderclap", "with fever/stiff neck"],
        "self_care_okay": True,
    },
    "hypertension": {
        "display_name": "Hypertension (High Blood Pressure)",
        "icd10": ["I10"],
        "symptoms": ["headache", "dizziness"],
        "key_features": ["often asymptomatic", "elevated BP readings", "headache if severe"],
        "default_urgency": "ROUTINE",
        "urgency_level": 4,
        "specialist": "internal_medicine",
        "action": "Schedule appointment with PCP",
        "risk_factors": ["age", "obesity", "high sodium diet", "family history", "sedentary lifestyle"],
        "red_flags": ["BP >180/120", "with chest pain", "with vision changes", "with headache"],
        "self_care_okay": True,
    },
    "type2_diabetes": {
        "display_name": "Type 2 Diabetes Mellitus",
        "icd10": ["E11.9"],
        "symptoms": ["fatigue", "weight_loss_unintentional"],
        "key_features": ["polyuria", "polydipsia", "polyphagia", "slow wound healing"],
        "default_urgency": "ROUTINE",
        "urgency_level": 4,
        "specialist": "endocrinology",
        "action": "Schedule appointment with PCP or endocrinologist",
        "risk_factors": ["obesity", "family history", "sedentary lifestyle", "age >45", "gestational diabetes"],
        "red_flags": ["blood sugar >300", "with nausea/vomiting", "fruity breath"],
        "self_care_okay": True,
    },
    "asthma": {
        "display_name": "Asthma",
        "icd10": ["J45.909"],
        "symptoms": ["shortness_of_breath", "cough"],
        "key_features": ["wheezing", "chest tightness", "worse at night/exercise", "episodic"],
        "default_urgency": "ROUTINE",
        "urgency_level": 4,
        "specialist": "pulmonology",
        "action": "Schedule appointment with PCP or pulmonologist",
        "risk_factors": ["family history", "allergies", "childhood asthma", "smoking exposure"],
        "red_flags": ["no relief from rescue inhaler", "unable to speak in sentences", "cyanosis"],
        "self_care_okay": True,
    },
    "depression": {
        "display_name": "Major Depressive Disorder",
        "icd10": ["F32.9"],
        "symptoms": ["depressed_mood", "fatigue"],
        "key_features": ["persistent sadness", "anhedonia", "sleep changes", "appetite changes", "concentration difficulty"],
        "default_urgency": "SOON",
        "urgency_level": 3,
        "specialist": "psychiatry",
        "action": "Schedule appointment with PCP or mental health professional",
        "risk_factors": ["family history", "prior episodes", "chronic illness", "substance use", "trauma"],
        "red_flags": ["suicidal ideation", "self-harm", "psychotic features"],
        "self_care_okay": False,
    },
    "anxiety_disorder": {
        "display_name": "Anxiety Disorder",
        "icd10": ["F41.9"],
        "symptoms": ["anxiety", "palpitations"],
        "key_features": ["excessive worry", "restlessness", "muscle tension", "sleep disturbance"],
        "default_urgency": "ROUTINE",
        "urgency_level": 4,
        "specialist": "psychiatry",
        "action": "Schedule appointment with PCP or mental health professional",
        "risk_factors": ["family history", "trauma", "chronic stress", "substance use"],
        "red_flags": ["panic attacks", "avoidance leading to disability", "substance use for coping"],
        "self_care_okay": True,
    },
    "common_cold": {
        "display_name": "Common Cold (Upper Respiratory Infection)",
        "icd10": ["J00"],
        "symptoms": ["cough", "fever", "fatigue"],
        "key_features": ["runny nose", "sore throat", "mild cough", "low-grade fever"],
        "default_urgency": "SELF_CARE",
        "urgency_level": 5,
        "specialist": None,
        "action": "Self-care at home; see doctor if worsening or lasting >10 days",
        "risk_factors": ["season", "close contact", "stress", "poor sleep"],
        "red_flags": ["fever >103°F", "symptoms >10 days", "severe sinus pain", "difficulty breathing"],
        "self_care_okay": True,
    },
}


# ── Urgency Rules ───────────────────────────────────────────────────
# Structured urgency escalation rules for symptom combinations

URGENCY_RULES = [
    {
        "rule_id": "UR001",
        "description": "Chest pain with radiation → EMERGENCY",
        "trigger_symptoms": ["chest_pain"],
        "trigger_modifiers": ["radiating to arm", "radiating to jaw", "crushing", "with sweating"],
        "escalate_to": "EMERGENCY",
    },
    {
        "rule_id": "UR002",
        "description": "Sudden neurological deficits → EMERGENCY",
        "trigger_symptoms": ["confusion", "dizziness", "headache"],
        "trigger_modifiers": ["sudden onset", "face drooping", "arm weakness", "speech difficulty"],
        "escalate_to": "EMERGENCY",
    },
    {
        "rule_id": "UR003",
        "description": "Breathing difficulty + cyanosis → EMERGENCY",
        "trigger_symptoms": ["shortness_of_breath"],
        "trigger_modifiers": ["cyanosis", "blue lips", "cannot speak"],
        "escalate_to": "EMERGENCY",
    },
    {
        "rule_id": "UR004",
        "description": "Infant fever → URGENT",
        "trigger_symptoms": ["fever"],
        "trigger_modifiers": ["infant", "baby", "newborn", "under 3 months"],
        "escalate_to": "URGENT",
    },
    {
        "rule_id": "UR005",
        "description": "Suicidal ideation → EMERGENCY",
        "trigger_symptoms": ["depressed_mood"],
        "trigger_modifiers": ["suicidal", "want to die", "end my life", "no point"],
        "escalate_to": "EMERGENCY",
    },
    {
        "rule_id": "UR006",
        "description": "Abdominal pain + fever in RLQ → URGENT (appendicitis)",
        "trigger_symptoms": ["abdominal_pain", "fever"],
        "trigger_modifiers": ["right lower", "worsening", "rebound"],
        "escalate_to": "URGENT",
    },
    {
        "rule_id": "UR007",
        "description": "High BP in pregnancy → URGENT (preeclampsia)",
        "trigger_symptoms": ["headache"],
        "trigger_modifiers": ["pregnant", "swelling", "high blood pressure", "vision changes"],
        "escalate_to": "URGENT",
    },
    {
        "rule_id": "UR008",
        "description": "Blood in vomit or large volume blood in stool → URGENT",
        "trigger_symptoms": ["blood_in_stool", "nausea_vomiting"],
        "trigger_modifiers": ["blood in vomit", "large amount", "black tarry", "hematemesis"],
        "escalate_to": "URGENT",
    },
]


# ── Specialist Map ──────────────────────────────────────────────────
# Maps specialist codes to full details

SPECIALIST_MAP = {
    "emergency_medicine": {
        "display_name": "Emergency Medicine",
        "where": "Emergency Room (ER)",
        "when": "Immediately — call 911 or go to nearest ER",
    },
    "cardiology": {
        "display_name": "Cardiologist",
        "where": "Cardiology clinic or hospital",
        "when": "Within days to weeks depending on severity",
    },
    "neurology": {
        "display_name": "Neurologist",
        "where": "Neurology clinic",
        "when": "Within 1-4 weeks; sooner if acute symptoms",
    },
    "pulmonology": {
        "display_name": "Pulmonologist",
        "where": "Pulmonology clinic",
        "when": "Within 2-4 weeks",
    },
    "gastroenterology": {
        "display_name": "Gastroenterologist",
        "where": "GI clinic",
        "when": "Within 2-4 weeks; sooner if bleeding",
    },
    "endocrinology": {
        "display_name": "Endocrinologist",
        "where": "Endocrinology clinic",
        "when": "Within 2-6 weeks",
    },
    "psychiatry": {
        "display_name": "Psychiatrist / Mental Health Professional",
        "where": "Mental health clinic or telehealth",
        "when": "Within 1-2 weeks; immediately if crisis",
    },
    "obstetrics": {
        "display_name": "Obstetrician (OB/GYN)",
        "where": "OB/GYN office or labor and delivery",
        "when": "Urgently for pregnancy complications",
    },
    "general_surgery": {
        "display_name": "General Surgeon",
        "where": "Hospital / surgical clinic",
        "when": "Urgently if acute abdomen; otherwise 1-2 weeks",
    },
    "internal_medicine": {
        "display_name": "Internist / Primary Care",
        "where": "Primary care clinic",
        "when": "Within 1-2 weeks for non-urgent; same-day for urgent",
    },
    "orthopedics": {
        "display_name": "Orthopedic Surgeon",
        "where": "Orthopedics clinic",
        "when": "Within 1-2 weeks; urgently for fractures",
    },
    "dermatology": {
        "display_name": "Dermatologist",
        "where": "Dermatology clinic",
        "when": "Within 2-6 weeks; sooner if suspicious lesion",
    },
}


# ── Lookup Functions ────────────────────────────────────────────────

def lookup_condition(condition_key):
    """Look up a condition by key. Returns the schema dict or None."""
    return CONDITION_SCHEMA.get(condition_key)


def get_conditions_for_symptom(symptom_key):
    """Find all conditions that list a given symptom."""
    matches = []
    for cond_key, cond in CONDITION_SCHEMA.items():
        if symptom_key in cond.get("symptoms", []):
            matches.append({
                "condition": cond_key,
                "display_name": cond["display_name"],
                "default_urgency": cond["default_urgency"],
                "specialist": cond.get("specialist"),
            })
    urgency_order = {"EMERGENCY": 1, "URGENT": 2, "SOON": 3, "ROUTINE": 4, "SELF_CARE": 5}
    return sorted(matches, key=lambda x: urgency_order.get(x.get("default_urgency", "ROUTINE"), 99))


def get_red_flags_for_symptoms(symptom_keys):
    """Get all red flag modifiers for a list of symptoms."""
    red_flags = []
    for sk in symptom_keys:
        if sk in SYMPTOM_ONTOLOGY:
            for rf in SYMPTOM_ONTOLOGY[sk]["red_flag_modifiers"]:
                red_flags.append({"symptom": sk, "red_flag": rf})
    return red_flags


def check_urgency_rules(symptom_keys, user_text_lower):
    """
    Check if any urgency escalation rules fire given the symptoms
    and the user's raw text.

    Returns: escalated urgency level string or None
    """
    highest = None
    priority = {"EMERGENCY": 1, "URGENT": 2, "SOON": 3, "ROUTINE": 4, "SELF_CARE": 5}

    for rule in URGENCY_RULES:
        # Check if any trigger symptom is present
        symptom_match = any(s in symptom_keys for s in rule["trigger_symptoms"])
        # Check if any trigger modifier appears in user text
        modifier_match = any(m.lower() in user_text_lower for m in rule["trigger_modifiers"])

        if symptom_match and modifier_match:
            level = rule["escalate_to"]
            if highest is None or priority.get(level, 99) < priority.get(highest, 99):
                highest = level

    return highest


def get_specialist_info(specialist_key):
    """Get full specialist information."""
    return SPECIALIST_MAP.get(specialist_key)


def export_schema_json():
    """Export the full schema to JSON for external tools or documentation."""
    schema = {
        "symptom_ontology": SYMPTOM_ONTOLOGY,
        "condition_schema": CONDITION_SCHEMA,
        "urgency_rules": [
            {k: v for k, v in rule.items()} for rule in URGENCY_RULES
        ],
        "specialist_map": SPECIALIST_MAP,
    }

    out_path = SCHEMA_DIR / "entity_schema.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2, ensure_ascii=False)
    print(f"Exported entity schema to {out_path}")
    return schema


if __name__ == "__main__":
    schema = export_schema_json()
    print(f"\nSymptom ontology entries: {len(SYMPTOM_ONTOLOGY)}")
    print(f"Condition schema entries: {len(CONDITION_SCHEMA)}")
    print(f"Urgency rules: {len(URGENCY_RULES)}")
    print(f"Specialist map entries: {len(SPECIALIST_MAP)}")

    # Demo lookup
    print("\n--- Demo: chest_pain symptom lookup ---")
    for cond in get_conditions_for_symptom("chest_pain"):
        print(f"  {cond['display_name']} → {cond['default_urgency']} → {cond['specialist']}")

    print("\n--- Demo: Red flags for [headache, fever] ---")
    for rf in get_red_flags_for_symptoms(["headache", "fever"]):
        print(f"  {rf['symptom']}: {rf['red_flag']}")
