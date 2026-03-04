# src/data_pipeline/cleaner.py

"""
Data Cleaner Module
-------------------
Raw text from websites is messy — it has HTML tags, extra spaces, and irrelevant content.
This module cleans all of that up so the AI gets clean, useful text.
Think of it as editing a rough draft into a clean final copy.
"""

import sys
import json
import re
import warnings
from pathlib import Path
from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning

# Suppress false-positive warning when cleaning URL-like strings
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

RAW_DATA_DIR = Path("data/raw")
PROCESSED_DATA_DIR = Path("data/processed")
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)


def clean_text(text):
    """
    Cleans a piece of text.
    - Removes HTML tags
    - Removes extra whitespace
    - Removes weird characters
    """
    if not text:
        return ""

    # Remove HTML tags (like <b>, <p>, etc.)
    soup = BeautifulSoup(text, "html.parser")
    text = soup.get_text()

    # Replace multiple spaces/newlines with single space
    text = re.sub(r'\s+', ' ', text)

    # Remove characters that aren't normal text, BUT preserve medical chars
    # Keep: ° (degrees, e.g. 103°F), % (e.g. 95% saturation), / (e.g. 120/80),
    #       " (inches), + (e.g. COVID+), # (e.g. #1), @ ≥ ≤ < > —
    text = re.sub(r'[^\w\s.,;:?!()\-\'°%/"#+<>≥≤—&@]', ' ', text)

    # Final cleanup
    text = text.strip()

    return text


def clean_document(doc):
    """Cleans a single document dictionary."""
    cleaned = {}

    for key, value in doc.items():
        if isinstance(value, str):
            cleaned[key] = clean_text(value)
        else:
            cleaned[key] = value

    return cleaned


def filter_low_quality_docs(documents, min_length=100):
    """
    Removes documents that are too short to be useful.
    A document with only 50 characters is probably useless.
    """
    filtered = [doc for doc in documents if len(doc.get("content", "")) >= min_length]
    removed = len(documents) - len(filtered)
    print(f"  Removed {removed} low-quality documents (too short)")
    return filtered


def deduplicate_docs(documents):
    """Removes duplicate documents based on content similarity."""
    seen_titles = set()
    unique_docs = []

    for doc in documents:
        title = doc.get("title", "").lower()
        if title not in seen_titles:
            seen_titles.add(title)
            unique_docs.append(doc)

    removed = len(documents) - len(unique_docs)
    print(f"  Removed {removed} duplicate documents")
    return unique_docs


def run_cleaning(force=False):
    """Main function — cleans all raw data files.

    Args:
        force: If True, re-clean and overwrite all existing cleaned files.
               If False (default), skip any source whose cleaned file already exists.
    """
    print("=" * 50)
    print("Starting Data Cleaning Pipeline")
    if force:
        print("Mode: FORCE — all files will be re-cleaned and overwritten")
    else:
        print("Mode: INCREMENTAL — existing cleaned files will be skipped (use --force to re-clean)")
    print("=" * 50)

    raw_files = list(RAW_DATA_DIR.glob("*.json"))

    if not raw_files:
        print("No raw data files found. Run collector.py first.")
        return

    for raw_file in raw_files:
        output_path = PROCESSED_DATA_DIR / f"cleaned_{raw_file.name}"

        if not force and output_path.exists():
            print(f"\nSkipping: {raw_file.name} — {output_path.name} already exists. Use --force to re-clean.")
            continue

        print(f"\nProcessing: {raw_file.name}")

        with open(raw_file, "r", encoding="utf-8") as f:
            documents = json.load(f)

        print(f"  Original count: {len(documents)}")

        # Clean each document
        cleaned_docs = [clean_document(doc) for doc in documents]

        # Remove low-quality and duplicates
        cleaned_docs = filter_low_quality_docs(cleaned_docs)
        cleaned_docs = deduplicate_docs(cleaned_docs)

        print(f"  Final count: {len(cleaned_docs)}")

        # Save cleaned data
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(cleaned_docs, f, indent=2)

        print(f"  Saved to: {output_path}")

    print("\nData cleaning complete!")


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    run_cleaning(force=force)
