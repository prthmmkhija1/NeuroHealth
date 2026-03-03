# src/data_pipeline/collector.py

"""
Data Collector Module
---------------------
This module downloads medical information from trusted public health websites.
Think of it as a librarian who goes to the library and photocopies relevant chapters.
"""

import requests
import json
import time
import os
from pathlib import Path
from bs4 import BeautifulSoup

# Where to save raw downloaded data
RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


def fetch_medlineplus_topics():
    """
    Downloads health topic pages from MedlinePlus.
    MedlinePlus has a public API — meaning they allow programs to download their data.

    Returns: list of documents, each being a dict with 'title', 'content', 'source'
    """
    print("Fetching MedlinePlus health topics...")

    documents = []

    # MedlinePlus provides a free API to get their health topics
    base_url = "https://wsearch.nlm.nih.gov/ws/query"

    # List of common health topics to fetch
    health_topics = [
        "fever", "headache", "chest pain", "shortness of breath",
        "abdominal pain", "back pain", "cough", "fatigue",
        "nausea", "dizziness", "rash", "joint pain",
        "diabetes", "hypertension", "depression", "anxiety",
        "asthma", "allergies", "cold", "flu",
        "sore throat", "urinary tract infection", "migraine",
        "high blood pressure", "heart disease", "stroke",
        "emergency signs", "when to call 911", "first aid"
    ]

    for topic in health_topics:
        try:
            params = {
                "db": "healthTopics",
                "term": topic,
                "retmax": 5,
                "rettype": "brief"
            }

            response = requests.get(base_url, params=params, timeout=10)

            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "lxml-xml")

                for doc in soup.find_all("document"):
                    title_tag = doc.find("content", attrs={"name": "title"})
                    summary_tag = doc.find("content", attrs={"name": "FullSummary"})

                    if title_tag and summary_tag:
                        document = {
                            "title": title_tag.get_text(strip=True),
                            "content": summary_tag.get_text(strip=True),
                            "source": "MedlinePlus",
                            "topic": topic,
                            "url": doc.get("url", "")
                        }
                        documents.append(document)

                print(f"  ✓ Fetched: {topic}")

            # Be polite — don't hammer the server
            time.sleep(0.5)

        except Exception as e:
            print(f"  ✗ Failed to fetch {topic}: {e}")

    return documents


def create_synthetic_qa_pairs():
    """
    Creates fake but realistic patient conversations.
    These are written by us to cover common scenarios the AI needs to handle.

    Returns: list of Q&A pairs
    """
    print("Creating synthetic Q&A pairs...")

    qa_pairs = [
        # Emergency scenarios
        {
            "question": "I have crushing chest pain that radiates to my left arm and I'm sweating",
            "answer": "EMERGENCY: These symptoms are classic warning signs of a heart attack. Call 911 (emergency services) IMMEDIATELY. Do not drive yourself. Chew an aspirin (325mg) if available and not allergic. Stay calm and sit down until help arrives.",
            "urgency": "EMERGENCY",
            "category": "cardiac"
        },
        {
            "question": "I suddenly can't speak properly and one side of my face is drooping",
            "answer": "EMERGENCY: These are stroke symptoms. Call 911 immediately. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911. Every minute matters during a stroke.",
            "urgency": "EMERGENCY",
            "category": "neurological"
        },
        {
            "question": "I'm having trouble breathing and my throat feels like it's closing up after eating peanuts",
            "answer": "EMERGENCY: This sounds like a severe allergic reaction (anaphylaxis). Call 911 IMMEDIATELY. Use an EpiPen if available. Do not wait to see if it gets better.",
            "urgency": "EMERGENCY",
            "category": "allergic"
        },
        {
            "question": "I took too many pills and I feel very drowsy",
            "answer": "EMERGENCY: Call 911 or Poison Control (1-800-222-1222) IMMEDIATELY. Tell them exactly what you took and how much. Do not try to make yourself vomit unless instructed by professionals.",
            "urgency": "EMERGENCY",
            "category": "overdose"
        },
        # Urgent scenarios
        {
            "question": "I have a fever of 103°F that has lasted 3 days and I feel very weak",
            "answer": "This requires URGENT medical attention within the next few hours. A high fever lasting this long needs evaluation. Please visit an urgent care clinic or emergency room today. Stay hydrated and take acetaminophen/ibuprofen for fever while you seek care.",
            "urgency": "URGENT",
            "category": "fever"
        },
        {
            "question": "I've been having severe abdominal pain on the lower right side for the past 6 hours",
            "answer": "This could be appendicitis, which requires URGENT evaluation. Please go to the emergency room or urgent care within the next few hours. Do not eat or drink anything until you are evaluated. Lower right abdominal pain that is persistent and worsening should always be checked.",
            "urgency": "URGENT",
            "category": "abdominal"
        },
        # Routine scenarios
        {
            "question": "I have a mild cold with runny nose and slight sore throat for 2 days",
            "answer": "This sounds like a common cold, which usually resolves on its own in 7-10 days. Rest, drink plenty of fluids, and consider over-the-counter remedies for symptom relief. See a doctor if symptoms worsen or persist beyond 10 days.",
            "urgency": "ROUTINE",
            "category": "respiratory"
        },
        {
            "question": "I have a headache that started this morning and is a 4/10 in severity",
            "answer": "A mild headache can often be managed at home. Try drinking water (dehydration is a common cause), resting in a dark quiet room, and over-the-counter pain relievers like acetaminophen or ibuprofen. If the headache worsens significantly, is the 'worst headache of your life', or comes with fever/stiff neck, seek immediate care.",
            "urgency": "ROUTINE",
            "category": "headache"
        },
        {
            "question": "I've been feeling more tired than usual for about a week",
            "answer": "Fatigue lasting a week can have many causes including poor sleep, stress, dehydration, or dietary issues. Try improving sleep hygiene, staying hydrated, and eating balanced meals. If fatigue persists beyond 2 weeks or is accompanied by other symptoms like weight loss, fever, or shortness of breath, schedule a doctor's appointment.",
            "urgency": "ROUTINE",
            "category": "general"
        },
        # Clarifying question scenarios
        {
            "question": "my stomach hurts",
            "answer": "I want to help you better. Can you tell me more? For example: Where exactly does it hurt (upper, lower, right, left side)? How severe is the pain on a scale of 1-10? How long have you had it? Is it constant or comes and goes? Any other symptoms like nausea, vomiting, or fever?",
            "urgency": "NEEDS_CLARIFICATION",
            "category": "abdominal"
        },
        {
            "question": "I don't feel well",
            "answer": "I'm sorry to hear that. To help you better, could you describe what you're experiencing? For example: What symptoms do you have? When did they start? How severe would you rate them on a scale of 1-10?",
            "urgency": "NEEDS_CLARIFICATION",
            "category": "general"
        },
        # Mental health scenarios
        {
            "question": "I've been feeling very depressed and hopeless lately",
            "answer": "I hear you, and I'm glad you're sharing this. Depression is a real medical condition and there is help available. I encourage you to reach out to a mental health professional. If you're in crisis or having thoughts of self-harm, please call the 988 Suicide and Crisis Lifeline (call or text 988) immediately. You are not alone.",
            "urgency": "URGENT",
            "category": "mental_health"
        },
        {
            "question": "I don't want to be here anymore",
            "answer": "I'm concerned about you and want to make sure you're safe. If you're having thoughts of ending your life, please call the 988 Suicide and Crisis Lifeline RIGHT NOW (call or text 988). You can also text HOME to 741741 for the Crisis Text Line. Someone is available 24/7 to help you. You matter.",
            "urgency": "EMERGENCY",
            "category": "mental_health_crisis"
        },
    ]

    return qa_pairs


def save_documents(documents, filename):
    """Saves collected documents to a JSON file."""
    filepath = RAW_DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"Saved {len(documents)} documents to {filepath}")


def run_data_collection():
    """Main function — runs the full data collection pipeline."""
    print("=" * 50)
    print("Starting Data Collection Pipeline")
    print("=" * 50)

    # Step 1: Fetch from MedlinePlus
    medline_docs = fetch_medlineplus_topics()
    save_documents(medline_docs, "medlineplus_articles.json")

    # Step 2: Create synthetic Q&A
    qa_pairs = create_synthetic_qa_pairs()
    save_documents(qa_pairs, "synthetic_qa.json")

    print("\nData collection complete!")
    print(f"Total documents: {len(medline_docs) + len(qa_pairs)}")


if __name__ == "__main__":
    run_data_collection()
