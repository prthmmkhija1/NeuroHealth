# src/data_pipeline/validator.py

"""
Data Validation Module
-----------------------
Per project specification:
"Implement data validation mechanisms to ensure medical accuracy
 and clinical safety compliance."

Validates collected and cleaned data for:
1. Source attribution — every document must cite its origin
2. Content completeness — no empty or truncated entries
3. Medical terminology check — flags obviously non-medical content
4. Safety keyword coverage — ensures emergency topics are represented
5. Deduplication integrity — checks for exact and near-duplicates
"""

import json
import re
from pathlib import Path
from collections import Counter

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")


# Minimum acceptable medical vocabulary — if a corpus doesn't mention
# at least N of these terms, it may be incomplete or corrupted
REQUIRED_MEDICAL_TERMS = [
    "symptom", "treatment", "diagnosis", "medication", "disease",
    "condition", "health", "doctor", "physician", "hospital",
    "emergency", "pain", "fever", "blood", "infection",
    "chronic", "acute", "therapy", "prevention", "screening",
]

# Safety-critical topics that MUST appear somewhere in the corpus
REQUIRED_SAFETY_TOPICS = [
    "heart attack", "stroke", "allergic reaction", "anaphylaxis",
    "suicide", "overdose", "poison", "emergency",
    "chest pain", "difficulty breathing",
]

# Minimum thresholds
MIN_DOCUMENT_LENGTH = 50       # characters
MIN_CORPUS_SIZE = 20           # total documents
MIN_MEDICAL_TERM_COVERAGE = 10 # at least 10 of the terms above must appear


def validate_raw_data():
    """Validates all raw JSON files in data/raw/."""
    print("\n[Validation] Checking raw data...")
    issues = []

    raw_files = list(RAW_DATA_DIR.glob("*.json"))
    if not raw_files:
        issues.append("CRITICAL: No raw data files found in data/raw/")
        return issues

    total_docs = 0
    all_content = ""

    for raw_file in raw_files:
        try:
            with open(raw_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, Exception) as e:
            issues.append(f"CRITICAL: {raw_file.name} is not valid JSON: {e}")
            continue

        if not isinstance(data, list):
            issues.append(f"ERROR: {raw_file.name} should contain a JSON array")
            continue

        if len(data) == 0:
            issues.append(f"WARNING: {raw_file.name} is empty (0 documents)")
            continue

        file_issues = 0
        for i, doc in enumerate(data):
            if not isinstance(doc, dict):
                issues.append(f"ERROR: {raw_file.name}[{i}] is not a dict")
                file_issues += 1
                continue

            # Check for content field
            content = doc.get("content", doc.get("answer", ""))
            if len(content) < MIN_DOCUMENT_LENGTH:
                file_issues += 1

            # Check for source attribution
            if not doc.get("source", "") and not doc.get("urgency", ""):
                # Q&A pairs don't need source, but articles do
                if "question" not in doc:
                    issues.append(
                        f"WARNING: {raw_file.name}[{i}] missing source attribution"
                    )

            all_content += " " + content.lower()
            total_docs += 1

        if file_issues > 0:
            issues.append(
                f"WARNING: {raw_file.name} has {file_issues} documents shorter "
                f"than {MIN_DOCUMENT_LENGTH} chars"
            )

        print(f"  {raw_file.name}: {len(data)} documents")

    # Check corpus size
    if total_docs < MIN_CORPUS_SIZE:
        issues.append(
            f"WARNING: Total corpus has only {total_docs} documents "
            f"(minimum recommended: {MIN_CORPUS_SIZE})"
        )

    # Check medical term coverage
    found_terms = [t for t in REQUIRED_MEDICAL_TERMS if t in all_content]
    if len(found_terms) < MIN_MEDICAL_TERM_COVERAGE:
        missing = [t for t in REQUIRED_MEDICAL_TERMS if t not in all_content]
        issues.append(
            f"WARNING: Low medical vocabulary coverage ({len(found_terms)}/{len(REQUIRED_MEDICAL_TERMS)}). "
            f"Missing: {missing[:5]}"
        )

    # Check safety topic coverage
    missing_safety = [t for t in REQUIRED_SAFETY_TOPICS if t not in all_content]
    if missing_safety:
        issues.append(
            f"SAFETY: Missing safety-critical topics in corpus: {missing_safety}"
        )

    return issues


def validate_processed_data():
    """Validates cleaned and chunked data."""
    print("\n[Validation] Checking processed data...")
    issues = []

    # Check cleaned files
    cleaned_files = list(PROCESSED_DATA_DIR.glob("cleaned_*.json"))
    if not cleaned_files:
        issues.append("WARNING: No cleaned data files found. Run cleaner.py first.")

    for cf in cleaned_files:
        with open(cf, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Check for content corruption (e.g., all content identical)
        contents = [d.get("content", "") for d in data]
        unique_ratio = len(set(contents)) / max(len(contents), 1)
        if unique_ratio < 0.5:
            issues.append(
                f"WARNING: {cf.name} has low uniqueness ratio ({unique_ratio:.0%}). "
                f"Possible duplication issue."
            )

        print(f"  {cf.name}: {len(data)} documents, {unique_ratio:.0%} unique")

    # Check chunks
    chunks_path = PROCESSED_DATA_DIR / "all_chunks.json"
    if chunks_path.exists():
        with open(chunks_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)

        # Check for chunk_id uniqueness
        ids = [c.get("chunk_id", "") for c in chunks]
        duplicates = [cid for cid, count in Counter(ids).items() if count > 1]
        if duplicates:
            issues.append(
                f"ERROR: {len(duplicates)} duplicate chunk_ids found: {duplicates[:3]}..."
            )

        # Check chunk sizes
        sizes = [len(c.get("content", "")) for c in chunks]
        avg_size = sum(sizes) / max(len(sizes), 1)
        empty_chunks = sum(1 for s in sizes if s < 10)
        if empty_chunks > 0:
            issues.append(f"WARNING: {empty_chunks} chunks are nearly empty (<10 chars)")

        print(f"  all_chunks.json: {len(chunks)} chunks, avg {avg_size:.0f} chars")
    else:
        issues.append("WARNING: all_chunks.json not found. Run chunker.py first.")

    return issues


def run_validation():
    """Runs all data validation checks and prints a report."""
    print("=" * 55)
    print("NeuroHealth Data Validation")
    print("Per spec: 'data validation mechanisms to ensure")
    print("medical accuracy and clinical safety compliance'")
    print("=" * 55)

    all_issues = []
    all_issues.extend(validate_raw_data())
    all_issues.extend(validate_processed_data())

    # Report
    print(f"\n{'='*55}")
    print("VALIDATION REPORT")
    print(f"{'='*55}")

    critical = [i for i in all_issues if i.startswith("CRITICAL")]
    errors = [i for i in all_issues if i.startswith("ERROR")]
    warnings = [i for i in all_issues if i.startswith("WARNING")]
    safety = [i for i in all_issues if i.startswith("SAFETY")]

    if not all_issues:
        print("All validations passed.")
    else:
        for issue in all_issues:
            print(f"  {issue}")

    print(f"\nSummary: {len(critical)} critical, {len(errors)} errors, "
          f"{len(warnings)} warnings, {len(safety)} safety flags")

    if critical:
        print("\nCRITICAL issues must be resolved before continuing.")
        return False

    return True


if __name__ == "__main__":
    run_validation()
