# src/data_pipeline/collector.py

"""
Data Collector Module
----------------------
Collects REAL medical knowledge from the sources cited on the official project page:
https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/

Sources used (exactly as listed on the project page):
  1. MedlinePlus (medlineplus.gov) — NIH/NLM full XML bulk download
     1000+ validated health topic summaries, free, no API key needed
     https://medlineplus.gov/xml.html
  2. MedlinePlus Health Term Definitions — fitness, nutrition, general health, vitamins
  3. Synthetic Q&A — common health inquiry patterns per project guidelines

Attribution: "Information from MedlinePlus.gov, National Library of Medicine, NIH"
"""

import requests
import json
import zipfile
import io
import time
import re
from pathlib import Path
from datetime import date, timedelta
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

RAW_DATA_DIR = Path("data/raw")
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)


# ──────────────────────────────────────────────────────────────
# SOURCE 1: MedlinePlus Full Health Topics XML
# Published daily by NIH/NLM. Contains 1000+ health topics
# with full summaries, categories, related topics.
# Free public download — no account or API key required.
# ──────────────────────────────────────────────────────────────

def get_latest_medlineplus_xml_url():
    """
    Finds the URL of the most recently published MedlinePlus compressed XML.
    MedlinePlus publishes a new file every Tue-Sat.
    We try today and the 7 most recent days to find the latest one.
    """
    base = "https://medlineplus.gov/xml/mplus_topics_compressed_{date}.zip"
    today = date.today()

    for days_back in range(8):
        d = today - timedelta(days=days_back)
        url = base.format(date=d.strftime("%Y-%m-%d"))
        try:
            # Just check headers — don't download yet
            r = requests.head(url, timeout=10)
            if r.status_code == 200:
                print(f"  Found latest MedlinePlus XML: {url}")
                return url
        except Exception:
            continue

    return None


def fetch_medlineplus_health_topics():
    """
    Downloads and parses the full MedlinePlus health topics XML.
    The compressed zip is ~4.6 MB and contains 1000+ health topics
    with full summaries from NIH.

    Returns: list of document dicts
    """
    print("\n[1/3] Fetching MedlinePlus Health Topics (NIH)...")
    print("  Source: https://medlineplus.gov/xml.html")

    url = get_latest_medlineplus_xml_url()
    if not url:
        print("  Could not find MedlinePlus XML. Skipping.")
        return []

    try:
        print("  Downloading (~4.6 MB compressed)...")
        response = requests.get(url, timeout=60)
        response.raise_for_status()

        # Unzip in memory
        zf = zipfile.ZipFile(io.BytesIO(response.content))
        xml_filename = [f for f in zf.namelist() if f.endswith(".xml")][0]
        xml_content = zf.read(xml_filename)

        print(f"  Parsing XML ({len(xml_content) // 1024} KB)...")

        root = ET.fromstring(xml_content)
        documents = []

        for topic in root.findall(".//health-topic"):
            title = topic.get("title", "").strip()
            url_attr = topic.get("url", "")
            language = topic.get("language", "English")

            # Skip Spanish (keep English only)
            if language.lower() != "english":
                continue

            # Get full summary (contains HTML — we'll clean it)
            summary_el = topic.find("full-summary")
            if summary_el is None:
                continue

            # Strip HTML tags from summary
            # Note: use ET.tostring() not .text — .text only returns text before
            # the first child element, so <full-summary><p>text</p></full-summary>
            # would return None for .text even though content exists.
            raw_html = ET.tostring(summary_el, encoding="unicode", method="html")
            if not raw_html or len(raw_html.strip()) < 20:
                continue
            soup = BeautifulSoup(raw_html, "html.parser")
            clean_text = soup.get_text(separator=" ", strip=True)
            clean_text = re.sub(r"\s+", " ", clean_text).strip()

            if len(clean_text) < 100:
                continue

            # Get body system / category groups
            groups = [g.text.strip() for g in topic.findall("group") if g.text]

            # Get synonyms / also-called
            also_called = [a.text.strip() for a in topic.findall("also-called") if a.text]

            # Get related topics
            related = [r.get("title", "") for r in topic.findall("related-topic")]

            documents.append({
                "title": title,
                "content": clean_text,
                "source": "MedlinePlus (NIH/NLM)",
                "url": url_attr,
                "categories": groups,
                "also_called": also_called,
                "related_topics": related[:5],
                "data_type": "health_topic",
            })

        print(f"  Extracted {len(documents)} health topics from MedlinePlus")
        return documents

    except Exception as e:
        print(f"  Error fetching MedlinePlus topics: {e}")
        return []


# ──────────────────────────────────────────────────────────────
# SOURCE 2: MedlinePlus Health Term Definitions
# Free XML files from NIH covering fitness, nutrition,
# vitamins, minerals, and general health terms.
# ──────────────────────────────────────────────────────────────

DEFINITION_FILES = {
    "general_health": "https://medlineplus.gov/xml/generalhealthdefinitions.xml",
    "fitness":        "https://medlineplus.gov/xml/fitnessdefinitions.xml",
    "nutrition":      "https://medlineplus.gov/xml/nutritiondefinitions.xml",
    "vitamins":       "https://medlineplus.gov/xml/vitaminsdefinitions.xml",
    "minerals":       "https://medlineplus.gov/xml/mineralsdefinitions.xml",
}


def fetch_medlineplus_definitions():
    """
    Downloads MedlinePlus health term definitions.
    These cover fitness, nutrition, vitamins, minerals, and general health terms.

    Returns: list of definition dicts
    """
    print("\n[2/3] Fetching MedlinePlus Term Definitions (NIH)...")

    documents = []

    for category, url in DEFINITION_FILES.items():
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(response.content)

            for item in root.findall(".//item"):
                term_el = item.find("term")
                def_el = item.find("definition")
                source_el = item.find("source")

                if term_el is None or def_el is None:
                    continue
                if not term_el.text or not def_el.text:
                    continue

                term = term_el.text.strip()
                definition = def_el.text.strip()
                source_name = source_el.text.strip() if (source_el is not None and source_el.text) else "NIH"

                if len(definition) < 20:
                    continue

                documents.append({
                    "title": term,
                    "content": f"{term}: {definition}",
                    "source": f"MedlinePlus Definitions - {source_name}",
                    "categories": [category],
                    "data_type": "definition",
                })

            print(f"  {category}: fetched definitions")
            time.sleep(0.3)

        except Exception as e:
            print(f"  {category}: {e}")

    print(f"  Total definitions: {len(documents)}")
    return documents


# ──────────────────────────────────────────────────────────────
# SOURCE 3: Synthetic Q&A
# Common health inquiry patterns per project guidelines:
# "synthetic patient inquiry scenarios based on common
#  healthcare use cases" — OSRE project page
# ──────────────────────────────────────────────────────────────

def create_synthetic_qa_pairs():
    """
    Synthetic health conversations covering the patterns
    explicitly listed in the project scope.
    """
    print("\n[3/3] Creating synthetic Q&A pairs (per project guidelines)...")

    qa_pairs = [
        # ── Emergency (cardiac) ──────────────────────────────────
        {
            "question": "I have crushing chest pain that radiates to my left arm and I'm sweating",
            "answer": "EMERGENCY: These symptoms are warning signs of a heart attack. Call 911 IMMEDIATELY. Do not drive yourself. Chew an aspirin (325mg) if available and not allergic. Stay calm and sit down until help arrives.",
            "urgency": "EMERGENCY", "category": "cardiac"
        },
        {
            "question": "I have chest pressure and my jaw hurts and I feel nauseous",
            "answer": "EMERGENCY: Chest pressure with jaw pain and nausea can indicate a heart attack. Call 911 NOW. These symptoms require immediate emergency care. Do not ignore or wait.",
            "urgency": "EMERGENCY", "category": "cardiac"
        },
        # ── Emergency (neurological) ─────────────────────────────
        {
            "question": "I suddenly can't speak properly and one side of my face is drooping",
            "answer": "EMERGENCY: These are stroke symptoms. Call 911 immediately. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911. Every minute matters in a stroke.",
            "urgency": "EMERGENCY", "category": "neurological"
        },
        {
            "question": "The worst headache of my life came on suddenly 15 minutes ago",
            "answer": "EMERGENCY: A sudden severe headache described as the 'worst of your life' can indicate a brain bleed (subarachnoid hemorrhage). This is a medical emergency. Call 911 immediately.",
            "urgency": "EMERGENCY", "category": "neurological"
        },
        # ── Emergency (respiratory/allergic) ────────────────────
        {
            "question": "I'm having trouble breathing and my throat feels like it's closing up after eating peanuts",
            "answer": "EMERGENCY: This is anaphylaxis — a life-threatening allergic reaction. Call 911 IMMEDIATELY. Use an EpiPen if available. Do not wait to see if it improves.",
            "urgency": "EMERGENCY", "category": "allergic"
        },
        {
            "question": "I can't breathe properly and my lips are turning blue",
            "answer": "EMERGENCY: Blue lips (cyanosis) with difficulty breathing is a life-threatening emergency. Call 911 IMMEDIATELY. This indicates dangerously low oxygen levels.",
            "urgency": "EMERGENCY", "category": "respiratory"
        },
        # ── Emergency (overdose/poisoning) ──────────────────────
        {
            "question": "I took too many pills and I feel very drowsy",
            "answer": "EMERGENCY: Call 911 or Poison Control (1-800-222-1222) IMMEDIATELY. Tell them exactly what medication and how much. Do not try to vomit unless directed by professionals.",
            "urgency": "EMERGENCY", "category": "overdose"
        },
        # ── Emergency (mental health crisis) ────────────────────
        {
            "question": "I don't want to be here anymore and I'm thinking about ending things",
            "answer": "I'm deeply concerned and I want you to be safe. Please call or text 988 (Suicide and Crisis Lifeline) RIGHT NOW. You can also text HOME to 741741. Someone is available 24/7. You are not alone and help is available.",
            "urgency": "EMERGENCY", "category": "mental_health_crisis"
        },
        # ── Urgent ──────────────────────────────────────────────
        {
            "question": "I have a fever of 103°F that has lasted 3 days and I feel very weak",
            "answer": "This requires URGENT evaluation today. A high fever lasting 3 days needs diagnosis. Visit an urgent care clinic or ER today. Stay hydrated. Take acetaminophen or ibuprofen as directed while you seek care.",
            "urgency": "URGENT", "category": "fever"
        },
        {
            "question": "I've been having severe lower right abdominal pain for 6 hours that keeps getting worse",
            "answer": "This urgently needs evaluation — could be appendicitis. Please go to an ER or urgent care within the next few hours. Do not eat or drink until evaluated. Worsening lower right abdominal pain should always be assessed promptly.",
            "urgency": "URGENT", "category": "abdominal"
        },
        {
            "question": "My child has a fever of 104°F and is very lethargic and not responding normally",
            "answer": "URGENT: A 104°F fever with lethargy in a child needs immediate medical attention. Go to the ER or urgent care NOW. High fevers in children with altered responsiveness require prompt evaluation.",
            "urgency": "URGENT", "category": "pediatric"
        },
        # ── Routine ─────────────────────────────────────────────
        {
            "question": "I have a runny nose, mild sore throat, and slight cough for 2 days",
            "answer": "This sounds like a common cold, which usually resolves in 7-10 days. Rest, drink plenty of fluids, and use over-the-counter remedies for symptom relief. See a doctor if symptoms worsen significantly or last more than 10 days.",
            "urgency": "ROUTINE", "category": "respiratory"
        },
        {
            "question": "I have a mild headache that started this morning, about a 3 out of 10",
            "answer": "A mild headache can often be managed at home. Drink water (dehydration is common), rest in a quiet dark room, and consider over-the-counter pain relievers like acetaminophen or ibuprofen. Seek care if the headache worsens dramatically or is accompanied by fever and stiff neck.",
            "urgency": "ROUTINE", "category": "headache"
        },
        {
            "question": "I've been more tired than usual for the past week",
            "answer": "Fatigue lasting a week can have many causes: poor sleep, stress, dehydration, or nutritional deficiencies. Try improving sleep, staying hydrated, and eating balanced meals. If fatigue persists beyond 2-3 weeks or is accompanied by weight loss, fever, or shortness of breath, schedule a doctor's appointment.",
            "urgency": "ROUTINE", "category": "general"
        },
        {
            "question": "I have a small cut on my finger from cooking that is still bleeding after 10 minutes",
            "answer": "Apply firm direct pressure with a clean cloth for 10-15 minutes without lifting. Elevate your hand above heart level. If bleeding does not stop after 20-30 minutes of direct pressure, or the wound is deep or gaping, seek urgent care.",
            "urgency": "SELF_CARE", "category": "wound"
        },
        # ── Self-care ────────────────────────────────────────────
        {
            "question": "I have mild sunburn on my arms and shoulders",
            "answer": "For mild sunburn: apply cool compresses, use aloe vera or gentle moisturizer, drink extra water, and take ibuprofen or acetaminophen for discomfort. Avoid further sun exposure until healed. See a doctor if you have blistering over large areas, fever, or severe pain.",
            "urgency": "SELF_CARE", "category": "skin"
        },
        # ── Clarification scenarios ──────────────────────────────
        {
            "question": "My stomach hurts",
            "answer": "I want to help you better. Can you tell me more? Where exactly does it hurt (upper, lower, left, right side, or all over)? How severe is the pain on a scale of 1-10? How long have you had it? Do you have any other symptoms like nausea, vomiting, fever, or diarrhea?",
            "urgency": "NEEDS_CLARIFICATION", "category": "abdominal"
        },
        {
            "question": "I don't feel well",
            "answer": "I'm sorry you're not feeling well. To help you better, could you describe your symptoms? For example: What exactly are you experiencing? When did it start? How severe is it on a scale of 1-10? Any fever, pain, or difficulty breathing?",
            "urgency": "NEEDS_CLARIFICATION", "category": "general"
        },
        # ── Chronic condition management ─────────────────────────
        {
            "question": "My blood sugar has been running higher than normal this week — I have type 2 diabetes",
            "answer": "Elevated blood sugar can be caused by illness, stress, diet changes, or medication timing. Check your glucose more frequently. If blood sugar remains very high (over 300 mg/dL) or you have symptoms like extreme thirst or confusion, contact your doctor or seek urgent care.",
            "urgency": "SOON", "category": "diabetes"
        },
        {
            "question": "I have asthma and my inhaler isn't helping my symptoms much today",
            "answer": "If your rescue inhaler is not providing relief, this could indicate worsening asthma. If you are having significant difficulty breathing, use your rescue inhaler, sit upright, and go to the ER if breathing does not improve within 15-20 minutes. Contact your doctor today even if breathing improves.",
            "urgency": "URGENT", "category": "asthma"
        },
        # ── Mental health ────────────────────────────────────────
        {
            "question": "I've been feeling very depressed and hopeless and have no motivation for weeks",
            "answer": "I hear you, and I'm glad you're reaching out. Depression is a real medical condition with effective treatments available. I encourage you to speak with your doctor or a mental health professional. If you are having any thoughts of harming yourself, please call or text 988 (Suicide and Crisis Lifeline) right away.",
            "urgency": "URGENT", "category": "mental_health"
        },
        {
            "question": "I've been having severe anxiety and panic attacks that wake me up at night",
            "answer": "Panic attacks are distressing but not life-threatening. During an attack: focus on slow deep breaths (breathe in for 4 counts, hold 4, out for 4). Frequent panic attacks affecting your sleep warrant evaluation by a doctor or mental health professional.",
            "urgency": "SOON", "category": "mental_health"
        },
        # ── Healthcare navigation ────────────────────────────────
        {
            "question": "What type of doctor should I see for recurring migraines?",
            "answer": "Start with your primary care physician (PCP) who can provide initial treatment and referrals. If migraines are frequent or severe, ask for a referral to a neurologist who specializes in headache disorders. Keep a headache diary noting frequency, triggers, and duration to bring to your appointment.",
            "urgency": "ROUTINE", "category": "find_doctor"
        },
        {
            "question": "My doctor prescribed metformin. What is it for?",
            "answer": "Metformin is most commonly prescribed to treat type 2 diabetes. It lowers blood sugar mainly by reducing the amount of glucose your liver releases and improving insulin sensitivity. It is usually taken with meals to reduce stomach side effects. Always follow your doctor's dosing instructions.",
            "urgency": "ROUTINE", "category": "medication_info"
        },
        # ── Clinical practice guideline–based entries ────────────
        {
            "question": "When should adults get a colonoscopy?",
            "answer": "The U.S. Preventive Services Task Force (USPSTF) recommends screening for colorectal cancer starting at age 45 and continuing through age 75 for average-risk adults. Screening options include a colonoscopy every 10 years, or a stool-based test (FIT) annually. Talk with your doctor about which screening schedule is right for you.",
            "urgency": "ROUTINE", "category": "preventive_care"
        },
        {
            "question": "How often should blood pressure be checked?",
            "answer": "Adults 18 and older should have their blood pressure checked at least once every two years if it is normal (below 120/80 mmHg). If it is elevated (120-129/<80) or if you have risk factors, check it at least annually. High blood pressure usually has no symptoms, so regular monitoring is very important.",
            "urgency": "ROUTINE", "category": "preventive_care"
        },
        {
            "question": "What are the guidelines for mammogram screenings?",
            "answer": "The USPSTF recommends biennial (every 2 years) mammography screening for women starting at age 40 through age 74. Women at higher risk (family history of breast cancer, genetic mutations like BRCA1/2) may need to start earlier or get screened more frequently. Discuss your personal risk with your doctor.",
            "urgency": "ROUTINE", "category": "preventive_care"
        },
        {
            "question": "Should I get a flu shot every year?",
            "answer": "Yes. The CDC recommends annual influenza vaccination for everyone 6 months of age and older. Flu viruses change each season, so a new vaccine is needed every year. The best time to get vaccinated is before flu season begins, usually by the end of October. Vaccination is especially important for people over 65, pregnant women, and those with chronic health conditions.",
            "urgency": "ROUTINE", "category": "preventive_care"
        },
        {
            "question": "What is the recommended treatment for mild to moderate hypertension?",
            "answer": "According to clinical guidelines, initial treatment for mild to moderate hypertension (stage 1: 130-139/80-89 mmHg) starts with lifestyle modifications: reducing sodium intake to less than 2300 mg/day, regular aerobic exercise (150 minutes/week), maintaining a healthy weight, and limiting alcohol. If blood pressure remains elevated after 3-6 months, your doctor may prescribe medication such as an ACE inhibitor, ARB, calcium channel blocker, or thiazide diuretic.",
            "urgency": "ROUTINE", "category": "chronic_disease"
        },
        {
            "question": "How should type 2 diabetes be managed day to day?",
            "answer": "Daily diabetes management includes: monitoring blood sugar levels as directed by your doctor, taking medications consistently, eating balanced meals with controlled carbohydrate portions, regular physical activity (at least 150 minutes of moderate exercise per week), and attending regular check-ups including A1C testing every 3-6 months. Target A1C is generally below 7% for most adults. Always consult your healthcare team for a personalized plan.",
            "urgency": "ROUTINE", "category": "chronic_disease"
        },
    ]

    print(f"  Created {len(qa_pairs)} synthetic Q&A pairs")
    return qa_pairs


# ──────────────────────────────────────────────────────────────
# MAIN COLLECTION PIPELINE
# ──────────────────────────────────────────────────────────────

def save_documents(documents, filename):
    """Saves collected documents to a JSON file."""
    filepath = RAW_DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(documents)} documents -> {filepath}")


def collect_data():
    """Main function — runs the full data collection from all sources."""
    print("=" * 55)
    print("NeuroHealth Data Collection")
    print("Sources: MedlinePlus (NIH) + Synthetic Q&A")
    print("Project: https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/")
    print("=" * 55)

    # Source 1: MedlinePlus full health topics XML
    health_topics = fetch_medlineplus_health_topics()
    save_documents(health_topics, "medlineplus_topics.json")

    # Source 2: MedlinePlus term definitions
    definitions = fetch_medlineplus_definitions()
    save_documents(definitions, "medlineplus_definitions.json")

    # Source 3: Synthetic Q&A
    qa_pairs = create_synthetic_qa_pairs()
    save_documents(qa_pairs, "synthetic_qa.json")

    total = len(health_topics) + len(definitions) + len(qa_pairs)
    print(f"\n{'='*55}")
    print(f"Collection complete. Total documents: {total}")
    print(f"  MedlinePlus health topics : {len(health_topics)}")
    print(f"  MedlinePlus definitions   : {len(definitions)}")
    print(f"  Synthetic Q&A pairs       : {len(qa_pairs)}")
    print(f"{'='*55}")


# Keep old name as alias so any test that calls run_data_collection() still works
def run_data_collection():
    collect_data()


if __name__ == "__main__":
    collect_data()
