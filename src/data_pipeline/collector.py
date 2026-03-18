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
  3. Mayo Clinic health information — web-scraped condition summaries (public pages)
  4. Clinical Practice Guidelines — curated evidence-based guidelines (USPSTF, etc.)
  5. Public Medical Q&A — curated conversational health inquiries from public forums
  6. Synthetic Q&A — common health inquiry patterns per project guidelines

Attribution: "Information from MedlinePlus.gov, National Library of Medicine, NIH"
"""

import io
import json
import re
import sys
import time
import xml.etree.ElementTree as ET
import zipfile
from datetime import date, timedelta
from pathlib import Path

import requests
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
    print("\n[1/6] Fetching MedlinePlus Health Topics (NIH)...")
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

        root = ET.fromstring(
            xml_content
        )  # nosec B314 - MedlinePlus XML is a trusted source
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
            also_called = [
                a.text.strip() for a in topic.findall("also-called") if a.text
            ]

            # Get related topics
            related = [r.get("title", "") for r in topic.findall("related-topic")]

            documents.append(
                {
                    "title": title,
                    "content": clean_text,
                    "source": "MedlinePlus (NIH/NLM)",
                    "url": url_attr,
                    "categories": groups,
                    "also_called": also_called,
                    "related_topics": related[:5],
                    "data_type": "health_topic",
                }
            )

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
    "fitness": "https://medlineplus.gov/xml/fitnessdefinitions.xml",
    "nutrition": "https://medlineplus.gov/xml/nutritiondefinitions.xml",
    "vitamins": "https://medlineplus.gov/xml/vitaminsdefinitions.xml",
    "minerals": "https://medlineplus.gov/xml/mineralsdefinitions.xml",
}


def fetch_medlineplus_definitions():
    """
    Downloads MedlinePlus health term definitions.
    These cover fitness, nutrition, vitamins, minerals, and general health terms.

    Returns: list of definition dicts
    """
    print("\n[2/6] Fetching MedlinePlus Term Definitions (NIH)...")

    documents = []

    for category, url in DEFINITION_FILES.items():
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            root = ET.fromstring(  # nosec B314 - MedlinePlus XML is a trusted source
                response.content
            )

            # Actual structure: <term-group reference="..."><term>...</term><definition>...</definition></term-group>
            for group in root.findall(".//term-group"):
                term_el = group.find("term")
                def_el = group.find("definition")
                source_name = group.get("reference", "NIH").strip() or "NIH"

                if term_el is None or def_el is None:
                    continue
                if not term_el.text or not def_el.text:
                    continue

                # CDATA values sometimes start with a leading ">" — strip it
                term = term_el.text.strip().lstrip(">").strip()
                definition = def_el.text.strip().lstrip(">").strip()

                if len(definition) < 20:
                    continue

                documents.append(
                    {
                        "title": term,
                        "content": f"{term}: {definition}",
                        "source": f"MedlinePlus Definitions - {source_name}",
                        "categories": [category],
                        "data_type": "definition",
                    }
                )

            print(f"  {category}: fetched definitions")
            time.sleep(0.3)

        except Exception as e:
            print(f"  {category}: {e}")

    print(f"  Total definitions: {len(documents)}")
    return documents


# ──────────────────────────────────────────────────────────────
# SOURCE 3: Mayo Clinic Health Information
# Per OSRE spec: "Data sources can include ... Mayo Clinic
# health information"
# Scrapes publicly accessible condition overview pages.
# ──────────────────────────────────────────────────────────────

# Mayo Clinic public condition URLs (diseases-conditions index)
MAYO_CLINIC_CONDITIONS = [
    # High-priority conditions that cover major body systems
    (
        "diabetes",
        "https://www.mayoclinic.org/diseases-conditions/type-2-diabetes/symptoms-causes/syc-20351193",
    ),
    (
        "hypertension",
        "https://www.mayoclinic.org/diseases-conditions/high-blood-pressure/symptoms-causes/syc-20373410",
    ),
    (
        "asthma",
        "https://www.mayoclinic.org/diseases-conditions/asthma/symptoms-causes/syc-20369653",
    ),
    (
        "migraine",
        "https://www.mayoclinic.org/diseases-conditions/migraine-headache/symptoms-causes/syc-20360201",
    ),
    (
        "depression",
        "https://www.mayoclinic.org/diseases-conditions/depression/symptoms-causes/syc-20356007",
    ),
    (
        "anxiety",
        "https://www.mayoclinic.org/diseases-conditions/anxiety/symptoms-causes/syc-20350961",
    ),
    (
        "heart-attack",
        "https://www.mayoclinic.org/diseases-conditions/heart-attack/symptoms-causes/syc-20373106",
    ),
    (
        "stroke",
        "https://www.mayoclinic.org/diseases-conditions/stroke/symptoms-causes/syc-20350113",
    ),
    (
        "pneumonia",
        "https://www.mayoclinic.org/diseases-conditions/pneumonia/symptoms-causes/syc-20354204",
    ),
    (
        "arthritis",
        "https://www.mayoclinic.org/diseases-conditions/arthritis/symptoms-causes/syc-20350772",
    ),
    (
        "allergies",
        "https://www.mayoclinic.org/diseases-conditions/allergies/symptoms-causes/syc-20351497",
    ),
    (
        "covid-19",
        "https://www.mayoclinic.org/diseases-conditions/coronavirus/symptoms-causes/syc-20479963",
    ),
    (
        "copd",
        "https://www.mayoclinic.org/diseases-conditions/copd/symptoms-causes/syc-20353679",
    ),
    (
        "kidney-disease",
        "https://www.mayoclinic.org/diseases-conditions/chronic-kidney-disease/symptoms-causes/syc-20354521",
    ),
    (
        "anemia",
        "https://www.mayoclinic.org/diseases-conditions/anemia/symptoms-causes/syc-20351360",
    ),
    (
        "back-pain",
        "https://www.mayoclinic.org/diseases-conditions/back-pain/symptoms-causes/syc-20369906",
    ),
    (
        "urinary-tract-infection",
        "https://www.mayoclinic.org/diseases-conditions/urinary-tract-infection/symptoms-causes/syc-20353447",
    ),
    (
        "gastroesophageal-reflux",
        "https://www.mayoclinic.org/diseases-conditions/gerd/symptoms-causes/syc-20361940",
    ),
    (
        "influenza",
        "https://www.mayoclinic.org/diseases-conditions/flu/symptoms-causes/syc-20351719",
    ),
    (
        "skin-cancer",
        "https://www.mayoclinic.org/diseases-conditions/skin-cancer/symptoms-causes/syc-20377605",
    ),
]


def fetch_mayo_clinic_data():
    """
    Scrapes condition overview pages from Mayo Clinic (public).
    Extracts symptoms, causes, and overview content from each condition page.

    Returns: list of document dicts
    """
    print("\n[3/6] Fetching Mayo Clinic Health Information...")
    print("  Source: https://www.mayoclinic.org/diseases-conditions")

    documents = []
    headers = {
        "User-Agent": "NeuroHealth-Research-Bot/1.0 (OSRE 2026 academic project)"
    }

    for condition_name, url in MAYO_CLINIC_CONDITIONS:
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                print(f"  {condition_name}: HTTP {response.status_code}, skipping")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Extract main article content
            article = soup.find("article") or soup.find("div", class_="content")
            if not article:
                print(f"  {condition_name}: no article content found, skipping")
                continue

            # Remove nav, scripts, ads
            for tag in article.find_all(["script", "style", "nav", "aside", "footer"]):
                tag.decompose()

            text = article.get_text(separator=" ", strip=True)
            text = re.sub(r"\s+", " ", text).strip()

            if len(text) < 100:
                print(f"  {condition_name}: content too short, skipping")
                continue

            # Truncate very long pages to keep knowledge base balanced
            if len(text) > 5000:
                text = text[:5000] + "..."

            documents.append(
                {
                    "title": f"{condition_name.replace('-', ' ').title()} — Overview",
                    "content": text,
                    "source": "Mayo Clinic",
                    "url": url,
                    "categories": [condition_name],
                    "data_type": "condition_overview",
                }
            )
            print(f"  {condition_name}: collected ({len(text)} chars)")

            # Be respectful — rate limit
            time.sleep(1.0)

        except Exception as e:
            print(f"  {condition_name}: {e}")

    print(f"  Total Mayo Clinic documents: {len(documents)}")
    return documents


# ──────────────────────────────────────────────────────────────
# SOURCE 4: Clinical Practice Guidelines
# Per OSRE spec: "Data sources can include ... clinical
# practice guidelines"
# Curated evidence-based guidelines from USPSTF, AHA, ADA,
# etc. (structured data since guidelines.gov is deprecated).
# ──────────────────────────────────────────────────────────────


def create_clinical_guidelines_data():
    """
    Curated clinical practice guidelines from major medical organizations.
    Since guidelines.gov was retired in 2018, we compile guidelines from
    authoritative sources: USPSTF, AHA, ADA, CDC, ACOG, etc.

    Returns: list of guideline document dicts
    """
    print("\n[4/6] Compiling Clinical Practice Guidelines...")
    print("  Sources: USPSTF, AHA, ADA, CDC, ACOG, AAFP")

    guidelines = [
        # ── USPSTF Screening Recommendations ───────────────────
        {
            "title": "USPSTF: Colorectal Cancer Screening",
            "content": (
                "The U.S. Preventive Services Task Force (USPSTF) recommends screening for "
                "colorectal cancer in all adults aged 45 to 75 years (Grade A). For adults aged "
                "76 to 85, screening should be individualized based on health status and prior "
                "screening history (Grade C). Screening options include: high-sensitivity guaiac "
                "fecal occult blood test (gFOBT) or fecal immunochemical test (FIT) annually; "
                "stool DNA-FIT every 1-3 years; CT colonography every 5 years; flexible "
                "sigmoidoscopy every 5 years; flexible sigmoidoscopy every 10 years plus annual "
                "FIT; or colonoscopy every 10 years. Source: USPSTF 2021."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2021,
            "grade": "A",
            "categories": ["preventive_care", "colorectal_cancer", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Breast Cancer Screening (Mammography)",
            "content": (
                "The USPSTF recommends biennial screening mammography for women aged 40 to 74 "
                "years (Grade B, updated 2024). Women at higher risk due to family history, "
                "genetic mutations (BRCA1/BRCA2), or prior chest radiation may benefit from "
                "earlier or more frequent screening. The decision to start screening before age "
                "40 should be individualized. Breast MRI may be recommended in addition to "
                "mammography for high-risk women. Source: USPSTF 2024."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2024,
            "grade": "B",
            "categories": ["preventive_care", "breast_cancer", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Lung Cancer Screening",
            "content": (
                "The USPSTF recommends annual screening for lung cancer with low-dose computed "
                "tomography (LDCT) in adults aged 50 to 80 years who have a 20 pack-year "
                "smoking history and currently smoke or have quit within the past 15 years "
                "(Grade B). Screening should be discontinued once a person has not smoked for "
                "15 years or develops a health problem that limits life expectancy or ability "
                "to have curative lung surgery. Source: USPSTF 2021."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2021,
            "grade": "B",
            "categories": ["preventive_care", "lung_cancer", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Cervical Cancer Screening",
            "content": (
                "The USPSTF recommends screening for cervical cancer every 3 years with cervical "
                "cytology alone in women aged 21 to 29 years. For women aged 30 to 65, screening "
                "every 3 years with cytology alone, every 5 years with high-risk human "
                "papillomavirus (hrHPV) testing alone, or every 5 years with hrHPV testing in "
                "combination with cytology (cotesting) is recommended (Grade A). Screening is "
                "not recommended for women under 21, over 65 with adequate prior screening, or "
                "who have had a hysterectomy with removal of the cervix. Source: USPSTF 2018."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2018,
            "grade": "A",
            "categories": ["preventive_care", "cervical_cancer", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Depression Screening in Adults",
            "content": (
                "The USPSTF recommends screening for depression in the general adult population, "
                "including pregnant and postpartum women (Grade B). Screening should be "
                "implemented with adequate systems in place to ensure accurate diagnosis, "
                "effective treatment, and appropriate follow-up. The Patient Health "
                "Questionnaire (PHQ-9) is a commonly used validated screening tool. "
                "Source: USPSTF 2016."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2016,
            "grade": "B",
            "categories": ["mental_health", "depression", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Hypertension Screening",
            "content": (
                "The USPSTF recommends screening for high blood pressure in adults aged 18 "
                "years or older (Grade A). Adults with high blood pressure should receive "
                "confirmatory blood pressure measurement outside the clinical setting through "
                "ambulatory blood pressure monitoring (ABPM) or home blood pressure monitoring "
                "(HBPM). Hypertension is defined as systolic BP ≥130 mmHg or diastolic BP "
                "≥80 mmHg. Source: USPSTF 2021."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2021,
            "grade": "A",
            "categories": ["preventive_care", "hypertension", "screening"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "USPSTF: Prediabetes and Type 2 Diabetes Screening",
            "content": (
                "The USPSTF recommends screening for prediabetes and type 2 diabetes in adults "
                "aged 35 to 70 years who have overweight or obesity (Grade B). Clinicians "
                "should offer or refer patients with prediabetes to effective preventive "
                "interventions. Screening tests include fasting plasma glucose, HbA1c, or "
                "oral glucose tolerance test. Prediabetes: fasting glucose 100-125 mg/dL or "
                "HbA1c 5.7%-6.4%. Diabetes: fasting glucose ≥126 mg/dL or HbA1c ≥6.5%. "
                "Source: USPSTF 2021."
            ),
            "source": "USPSTF",
            "guideline_org": "U.S. Preventive Services Task Force",
            "year": 2021,
            "grade": "B",
            "categories": ["preventive_care", "diabetes", "screening"],
            "data_type": "clinical_guideline",
        },
        # ── AHA/ACC Guidelines ──────────────────────────────────
        {
            "title": "AHA/ACC: Hypertension Management",
            "content": (
                "The 2017 AHA/ACC guideline defines hypertension as blood pressure ≥130/80 mmHg. "
                "Stage 1 (130-139/80-89): lifestyle modifications including DASH diet, sodium "
                "reduction (<1500 mg/day ideal, <2300 mg/day maximum), regular aerobic exercise "
                "(90-150 min/week), weight loss if overweight (target BMI 18.5-24.9), moderation "
                "of alcohol intake, and potassium supplementation. Medication recommended if "
                "10-year ASCVD risk ≥10% or clinical CVD. Stage 2 (≥140/90): lifestyle changes "
                "plus antihypertensive medication. First-line medications: thiazide diuretics, "
                "ACE inhibitors, ARBs, or calcium channel blockers. Target BP <130/80 for most "
                "adults. Source: AHA/ACC 2017."
            ),
            "source": "AHA/ACC",
            "guideline_org": "American Heart Association / American College of Cardiology",
            "year": 2017,
            "categories": ["chronic_disease", "hypertension", "treatment"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "AHA: Heart Attack Warning Signs and Response",
            "content": (
                "The American Heart Association identifies these heart attack warning signs: "
                "chest discomfort (pressure, squeezing, fullness, pain) lasting more than a "
                "few minutes or recurring; discomfort in other upper body areas (one or both "
                "arms, back, neck, jaw, or stomach); shortness of breath with or without chest "
                "discomfort; cold sweat, nausea, or lightheadedness. Action: Call 911 "
                "immediately. Do not drive yourself. Chew an aspirin (325mg) if not allergic. "
                "Women may experience atypical symptoms more often: unusual fatigue, shortness "
                "of breath, nausea/vomiting, back or jaw pain. Every minute matters — faster "
                "treatment means less heart damage. Source: AHA 2023."
            ),
            "source": "AHA",
            "guideline_org": "American Heart Association",
            "year": 2023,
            "categories": ["emergency", "cardiac", "heart_attack"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "AHA: Stroke Warning Signs (FAST)",
            "content": (
                "The AHA/ASA recommends using FAST to recognize stroke: F — Face drooping "
                "(one side of the face droops or is numb); A — Arm weakness (one arm is weak "
                "or numb, drifts downward when raised); S — Speech difficulty (slurred or "
                "strange speech, unable to repeat simple sentence); T — Time to call 911 "
                "(even if symptoms go away, note the time of onset). Additional stroke "
                "symptoms: sudden numbness, confusion, trouble seeing in one or both eyes, "
                "trouble walking, dizziness, loss of balance, or sudden severe headache with "
                "no known cause. Treatment window: tPA (clot-busting drug) within 3-4.5 hours. "
                "Every minute of delay results in ~1.9 million neurons lost. Source: AHA/ASA 2023."
            ),
            "source": "AHA/ASA",
            "guideline_org": "American Heart Association / American Stroke Association",
            "year": 2023,
            "categories": ["emergency", "neurological", "stroke"],
            "data_type": "clinical_guideline",
        },
        # ── ADA Guidelines ──────────────────────────────────────
        {
            "title": "ADA: Standards of Care in Diabetes",
            "content": (
                "The American Diabetes Association 2024 Standards of Care recommend: "
                "A1C testing at least twice/year for patients meeting goals, quarterly if not "
                "at goal or therapy changed. A1C target <7% for most nonpregnant adults; "
                "individualized targets (6.5% to 8%) based on patient factors. Self-monitoring "
                "of blood glucose (SMBG) for insulin users: before meals and at bedtime for "
                "multiple-dose insulin. Continuous glucose monitoring (CGM) can be beneficial. "
                "Comprehensive foot exam annually. Dilated eye exam at diagnosis of type 2, "
                "within 5 years for type 1, then annually. Blood pressure target <130/80. "
                "Statin therapy for patients aged 40-75. Annual urine albumin-to-creatinine "
                "ratio and eGFR. Pneumococcal, influenza, hepatitis B, and COVID vaccines. "
                "Source: ADA Standards of Care 2024."
            ),
            "source": "ADA",
            "guideline_org": "American Diabetes Association",
            "year": 2024,
            "categories": [
                "chronic_disease",
                "diabetes",
                "treatment",
                "preventive_care",
            ],
            "data_type": "clinical_guideline",
        },
        # ── CDC Guidelines ──────────────────────────────────────
        {
            "title": "CDC: Adult Immunization Schedule",
            "content": (
                "CDC recommended adult immunizations (2024-2025): Influenza vaccine annually "
                "for all adults. COVID-19: updated vaccine as recommended. Td/Tdap: Tdap once "
                "if not previously received, then Td or Tdap booster every 10 years. MMR: 1+ "
                "doses for adults born after 1957 without immunity. Varicella: 2 doses for "
                "adults without evidence of immunity. Zoster (Shingrix): 2 doses for adults "
                "≥50 years. HPV: ages 19-26 (catch-up through age 45 by shared decision). "
                "Pneumococcal: PCV20 for all adults ≥65 and younger adults with risk factors. "
                "Hepatitis B: universal vaccination for adults aged 19-59; ≥60 with risk factors. "
                "Hepatitis A: for adults with specific risk factors. Meningococcal: for adults "
                "with specific risk factors (asplenia, complement deficiency, travel). "
                "Source: CDC ACIP 2024."
            ),
            "source": "CDC",
            "guideline_org": "Centers for Disease Control and Prevention",
            "year": 2024,
            "categories": ["preventive_care", "immunization", "vaccines"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "CDC: Childhood Immunization Schedule (0-18 years)",
            "content": (
                "CDC recommended childhood/adolescent immunizations (2024): Birth: HepB. "
                "2 months: RV, DTaP, Hib, PCV15, IPV, HepB. 4 months: RV, DTaP, Hib, PCV15, "
                "IPV. 6 months: RV, DTaP, Hib, PCV15, IPV, HepB, Influenza (annually from "
                "6 months). 12-15 months: Hib, PCV15, MMR, Varicella, HepA (2 doses through "
                "23 months). 4-6 years: DTaP, IPV, MMR, Varicella. 11-12 years: Tdap, HPV "
                "(2 doses), MenACWY. 16 years: MenACWY booster. Special considerations: "
                "children with immunocompromising conditions, asplenia, or HIV may need "
                "modified schedules. Catch-up schedule available for delayed vaccinations. "
                "Source: CDC ACIP 2024."
            ),
            "source": "CDC",
            "guideline_org": "Centers for Disease Control and Prevention",
            "year": 2024,
            "categories": ["preventive_care", "pediatric", "immunization", "vaccines"],
            "data_type": "clinical_guideline",
        },
        # ── ACOG Guidelines ─────────────────────────────────────
        {
            "title": "ACOG: Prenatal Care Guidelines",
            "content": (
                "The American College of Obstetricians and Gynecologists recommends the "
                "following prenatal care schedule: First visit (6-8 weeks): complete history, "
                "physical exam, blood type/Rh, CBC, urinalysis, STI screening, rubella "
                "immunity, hepatitis B/C, HIV. First trimester: genetic screening options "
                "discussion, folic acid 400-800 mcg daily. Second trimester: anatomy ultrasound "
                "(18-22 weeks), glucose challenge test (24-28 weeks), Tdap vaccine (27-36 "
                "weeks). Third trimester: Group B strep screening (36-37 weeks), assessment "
                "of fetal position. Visits schedule: every 4 weeks until 28 weeks, every "
                "2 weeks until 36 weeks, then weekly until delivery. Warning signs requiring "
                "immediate care: vaginal bleeding, severe headache with vision changes, "
                "decreased fetal movement, leaking fluid, contractions before 37 weeks. "
                "Source: ACOG 2023."
            ),
            "source": "ACOG",
            "guideline_org": "American College of Obstetricians and Gynecologists",
            "year": 2023,
            "categories": ["preventive_care", "prenatal", "obstetrics"],
            "data_type": "clinical_guideline",
        },
        # ── AAFP Guidelines ─────────────────────────────────────
        {
            "title": "AAFP: Annual Wellness Visit Recommendations",
            "content": (
                "The American Academy of Family Physicians recommends annual wellness visits "
                "include: vital signs (blood pressure, heart rate, weight, BMI), age-appropriate "
                "cancer screenings, immunization review/update, depression and anxiety screening "
                "(PHQ-9, GAD-7), fall risk assessment (≥65 years), cognitive assessment (≥65 "
                "years, if indicated), substance use screening (AUDIT-C, DAST), social "
                "determinants of health assessment, advance care planning discussion (≥65 years), "
                "medication review and reconciliation. Lab work as indicated: lipid panel "
                "(every 4-6 years if normal), fasting glucose or A1C (every 3 years if normal, "
                "≥35 with overweight), TSH (if symptomatic), CBC (if symptomatic or risk "
                "factors for anemia). Source: AAFP 2023."
            ),
            "source": "AAFP",
            "guideline_org": "American Academy of Family Physicians",
            "year": 2023,
            "categories": ["preventive_care", "wellness", "primary_care"],
            "data_type": "clinical_guideline",
        },
        # ── Emergency Guidelines ────────────────────────────────
        {
            "title": "AHA: Basic Life Support (BLS) Algorithm",
            "content": (
                "AHA Basic Life Support for adults: 1) Verify scene safety. 2) Check "
                "responsiveness — tap shoulders and shout. 3) If unresponsive, call 911 and "
                "get AED. 4) Check for pulse and breathing simultaneously (no more than 10 "
                "seconds). 5) No pulse: begin CPR with 30 compressions at 100-120/min, 2 "
                "inches deep, allowing full recoil. 6) After 30 compressions, give 2 rescue "
                "breaths (1 second each). 7) Continue 30:2 cycles until AED arrives or EMS "
                "takes over. 8) AED: turn on, attach pads, follow prompts, minimize "
                "interruptions. Compression-only CPR is recommended for untrained bystanders. "
                "For children (1-puberty): same ratio with less depth (about 2 inches). "
                "For infants: 2 fingers, 1.5 inches deep, 30:2 ratio. Source: AHA 2020."
            ),
            "source": "AHA",
            "guideline_org": "American Heart Association",
            "year": 2020,
            "categories": ["emergency", "bls", "cpr", "first_aid"],
            "data_type": "clinical_guideline",
        },
        {
            "title": "ACEP: Emergency Severity Index (ESI) Triage",
            "content": (
                "The Emergency Severity Index (ESI) is a five-level triage tool used in "
                "emergency departments. ESI-1 (Resuscitation): immediate life-threatening "
                "conditions — requires immediate intervention (cardiac arrest, respiratory "
                "failure, severe trauma). ESI-2 (Emergent): high-risk situations — should not "
                "wait (chest pain with cardiac features, acute stroke symptoms, severe allergic "
                "reaction, altered mental status). ESI-3 (Urgent): requires 2+ resources — "
                "stable but needs workup (abdominal pain needing labs and imaging, lacerations "
                "needing sutures). ESI-4 (Less Urgent): needs 1 resource (simple laceration, "
                "urinalysis for UTI symptoms). ESI-5 (Non-Urgent): needs no resources (medication "
                "refill, minor complaint, follow-up). Source: ACEP/ENA 2020."
            ),
            "source": "ACEP",
            "guideline_org": "American College of Emergency Physicians",
            "year": 2020,
            "categories": ["emergency", "triage", "assessment"],
            "data_type": "clinical_guideline",
        },
    ]

    documents = []
    for g in guidelines:
        documents.append(
            {
                "title": g["title"],
                "content": g["content"],
                "source": g["source"],
                "categories": g["categories"],
                "data_type": g["data_type"],
                "guideline_org": g.get("guideline_org", ""),
                "year": g.get("year", ""),
            }
        )

    print(f"  Compiled {len(documents)} clinical practice guidelines")
    return documents


# ──────────────────────────────────────────────────────────────
# SOURCE 5: Public Medical Q&A (Forum-Style Data)
# Per OSRE spec: "Collect and curate conversational health
# inquiry datasets from public medical Q&A forums, symptom
# checker logs, and healthcare chatbot interactions"
#
# Curated realistic forum-style Q&A based on common patterns
# seen in HealthBoards, MedHelp, Reddit r/AskDocs, and
# symptom checker interaction logs.
# ──────────────────────────────────────────────────────────────


def create_public_forum_qa_data():
    """
    Curated conversational health inquiries modeled on real public
    medical Q&A forum patterns (HealthBoards, MedHelp, Reddit
    r/AskDocs, WebMD community). These capture the informal,
    ambiguous, multi-symptom way real users describe health issues.

    Returns: list of forum-style Q&A dicts
    """
    print("\n[5/6] Creating public medical forum Q&A dataset...")

    forum_qa = [
        # ── Ambiguous / vague descriptions (common in forums) ──
        {
            "question": "Hey, so I've been feeling really off lately. Like tired all the time and my stomach has been weird. Not really pain but more like uncomfortable? IDK if I should see someone.",
            "answer": "Persistent fatigue combined with vague abdominal discomfort can have many causes — from stress and poor diet to thyroid issues, anemia, or GI conditions. Since this has been ongoing, it would be a good idea to schedule an appointment with your primary care doctor. They can run basic bloodwork (CBC, thyroid, metabolic panel) to rule out common causes. In the meantime, ensure you're staying hydrated, getting adequate sleep, and eating regular meals.",
            "urgency": "ROUTINE",
            "category": "general",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "my head has been hurting on and off for like a week. mostly behind my eyes. advil helps but it comes back. is this something serious?",
            "answer": "Recurring headaches behind the eyes that respond to OTC pain relievers are often tension headaches or could be related to eye strain, sinusitis, or migraine. They're usually not serious if they respond to medication. However, headaches lasting more than a week warrant a doctor visit to identify the pattern and triggers. Seek immediate care if you experience sudden severe headache, vision changes, neck stiffness, or fever with your headaches.",
            "urgency": "ROUTINE",
            "category": "headache",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "I googled my symptoms and now I'm freaking out. I have a lump in my neck and WebMD says it could be lymphoma. I'm only 25. Should I go to the ER??",
            "answer": "It's understandable to feel anxious after online searching. Neck lumps in young adults are most commonly swollen lymph nodes from infections (cold, flu, dental issues) and are usually benign. However, any new lump that persists for more than 2-3 weeks, is larger than 1cm, painless, hard/fixed, or associated with night sweats, unexplained weight loss, or persistent fever should be evaluated promptly. Schedule an appointment with your doctor within a week rather than the ER — they can examine it and order appropriate tests if needed.",
            "urgency": "SOON",
            "category": "general",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "First time posting. I'm a 34F and for the past month I've had heart palpitations, feeling shaky, and lost weight without trying. My mom has thyroid problems. Could this be related?",
            "answer": "Your symptoms (palpitations, shakiness, unintentional weight loss) combined with a family history of thyroid problems are concerning for hyperthyroidism (overactive thyroid). This is quite treatable but should be evaluated soon. Schedule an appointment with your doctor within the next few days — they'll likely order a TSH blood test, which can quickly confirm or rule out thyroid issues. If you experience severe chest pain, extreme shortness of breath, or a very rapid heart rate (>150 bpm), seek emergency care.",
            "urgency": "SOON",
            "category": "endocrine",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "UPDATE: went to the doc about my breathing issues. They said it might be anxiety but are doing a chest xray. Anyone else been told it's anxiety when they felt like they couldn't breathe?",
            "answer": "Yes, anxiety is a very common cause of breathing difficulty (dyspnea), and it's one of the most frequent reasons people visit ERs for breathing concerns. Anxiety can cause hyperventilation, chest tightness, and feeling like you can't take a deep breath. However, your doctor is doing the right thing ordering a chest X-ray to rule out physical causes. Follow up with the results and if anxiety is the cause, treatments like cognitive behavioral therapy (CBT), breathing exercises, and sometimes medication can help significantly.",
            "urgency": "ROUTINE",
            "category": "respiratory",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        # ── Multi-symptom / complex descriptions ────────────────
        {
            "question": "I'm 52M, been having more bathroom trips at night (3-4 times), weak stream, and sometimes feel like I can't empty completely. My dad had prostate issues. At what point should I worry?",
            "answer": "The symptoms you describe — urinary frequency, nocturia, weak stream, and incomplete emptying — are classic symptoms of benign prostatic hyperplasia (BPH), which is very common in men over 50. Given your family history, schedule an appointment with your primary doctor or urologist within the next couple of weeks. They'll likely do a digital rectal exam, PSA blood test, and urinalysis. While these symptoms are usually BPH (non-cancerous), evaluation is important to rule out other causes and discuss treatment options.",
            "urgency": "ROUTINE",
            "category": "urology",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "I don't have insurance and I noticed blood in my stool today. It was bright red and on the toilet paper. I can't afford an ER visit. What should I do?",
            "answer": "Bright red blood on toilet paper is most commonly from hemorrhoids or an anal fissure, especially if you've had constipation or straining. However, blood in stool should always be evaluated. Since you don't have insurance, consider these options: Federally Qualified Health Centers (FQHCs) offer care on a sliding fee scale based on income — find one at findahealthcenter.hrsa.gov. Many hospital systems have charity care programs. Some urgent care clinics have affordable rates. If you experience large amounts of blood, black/tarry stools, dizziness, or fainting, go to the ER regardless of cost — they must treat you under EMTALA law.",
            "urgency": "SOON",
            "category": "gastrointestinal",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "Has anyone dealt with chronic fatigue and joint pain after COVID? It's been 4 months since I had it and I still can't function normally. My doctor keeps saying give it time.",
            "answer": "What you're describing sounds like Long COVID (Post-COVID Condition), which is recognized by the WHO and CDC. Symptoms can include fatigue, joint pain, brain fog, and exercise intolerance lasting months. If your current doctor isn't addressing your concerns adequately, consider asking for a referral to a Long COVID clinic or infectious disease specialist. Some things that may help: pacing activities (avoiding boom-bust cycles), adequate rest, gentle gradually progressive exercise, and addressing individual symptoms. You're not alone — this affects a significant number of COVID survivors.",
            "urgency": "ROUTINE",
            "category": "post_covid",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "I'm 7 months pregnant and my hands and face are swelling up, and I have a bad headache that won't go away. My blood pressure was 150/95 at home. Is this normal?",
            "answer": "URGENT: These symptoms — facial and hand swelling, persistent headache, and elevated blood pressure (150/95) at 7 months pregnant — are warning signs of preeclampsia, which is a serious pregnancy complication. You need to contact your OB/midwife immediately or go to labor and delivery/ER NOW. Preeclampsia can rapidly worsen and affect both you and your baby. Do not wait for your next scheduled appointment. Additional warning signs to watch for: vision changes (blurring, seeing spots), upper abdominal pain, nausea/vomiting, and sudden severe swelling.",
            "urgency": "URGENT",
            "category": "obstetrics",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "my kid (3yo) has been pulling at his ears for 2 days and had a fever of 101 last night. He's cranky and not eating well. Ear infection maybe? Do I need to go in or can I wait?",
            "answer": "A 3-year-old with ear pulling, fever (101°F), irritability, and decreased appetite has classic signs of an ear infection (acute otitis media). While ear infections sometimes resolve on their own in older children, at age 3 with fever and clear discomfort, it's best to see the pediatrician within the next day or so. They can examine the ears and determine if antibiotics are needed. In the meantime, acetaminophen (Tylenol) or ibuprofen (Motrin/Advil) dosed for weight can help with pain and fever. Go to the ER if fever exceeds 104°F, child seems extremely ill, or you notice drainage/blood from the ear.",
            "urgency": "SOON",
            "category": "pediatric",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        # ── Symptom checker–style interactions ──────────────────
        {
            "question": "Symptom checker said 'seek emergency care' for my symptoms: dizziness, tingling in my fingers, and feeling like I'm going to pass out. But I have anxiety and feel like it might just be a panic attack. How do I tell the difference?",
            "answer": "Panic attacks and some medical emergencies (like cardiac events, low blood sugar, or TIA) can share overlapping symptoms including dizziness, tingling, and feeling faint. Key differences: Panic attacks usually peak within 10 minutes and resolve in 20-30 minutes; they often include a feeling of dread/doom, rapid breathing, and racing heart. Concerning signs that warrant ER evaluation: one-sided weakness or numbness, slurred speech, chest pain/pressure, symptoms lasting over 30 minutes, loss of consciousness, or symptoms that feel different from your typical panic attacks. If in doubt, it's always safer to seek evaluation. If these episodes are new, see your doctor for baseline cardiac and neurological evaluation.",
            "urgency": "SOON",
            "category": "general",
            "data_type": "forum_qa",
            "source": "Curated from symptom checker interaction patterns",
        },
        {
            "question": "Is it normal to have chest tightness after working out? I'm 28 and started going to the gym recently. It goes away after a few minutes of rest.",
            "answer": "Mild chest tightness during or shortly after vigorous exercise that resolves with rest can occur in people new to exercise, especially if you're working out intensely or in cold/dry air. This can sometimes be exercise-induced bronchoconstriction (exercise-induced asthma). However, chest tightness with exercise should be evaluated, particularly if it's accompanied by pain, shortness of breath disproportionate to your exertion, dizziness, or palpitations. Schedule a visit with your doctor for a baseline cardiac evaluation — they may order an ECG and potentially an exercise stress test. At 28 the risk of cardiac disease is low, but a medical evaluation for exercise-related chest symptoms is always prudent.",
            "urgency": "ROUTINE",
            "category": "cardiac",
            "data_type": "forum_qa",
            "source": "Curated from symptom checker interaction patterns",
        },
        # ── Mental health forum patterns ────────────────────────
        {
            "question": "I've been self-medicating with alcohol to deal with my anxiety. I know it's bad but I can't afford therapy. Drinking 4-5 beers every night now. Any advice?",
            "answer": "I'm glad you recognize this pattern and are reaching out. Using alcohol to manage anxiety is very common but it actually worsens anxiety over time and creates a cycle of dependence. The level you describe (4-5 drinks nightly) is also medically concerning. There are affordable/free options: SAMHSA helpline 1-800-662-4357 (free, confidential, 24/7); many therapists offer sliding-scale fees; community mental health centers provide low-cost care; apps like BetterHelp and Talkspace sometimes offer financial aid. For the anxiety itself: regular exercise, limiting caffeine, breathing exercises, and mindfulness meditation have strong evidence. Please be honest with your doctor about your alcohol use — they can help safely, without judgment.",
            "urgency": "SOON",
            "category": "mental_health",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        {
            "question": "Does anyone else get really bad health anxiety? Every little symptom I have I think is cancer or a heart attack. I've been to the ER 5 times this year for different things and everything comes back normal.",
            "answer": "What you're describing sounds like health anxiety (formerly called hypochondria, now illness anxiety disorder). It's a recognized condition where normal body sensations are interpreted as signs of serious illness. Frequent ER visits with normal results are a common pattern. Effective treatments include: cognitive behavioral therapy (CBT) specifically for health anxiety, which has strong evidence; selective serotonin reuptake inhibitors (SSRIs); and exposure and response prevention (ERP). Limiting symptom Googling can also help. Ask your primary doctor for a referral to a therapist experienced with health anxiety. You're not 'crazy' — this is a treatable anxiety condition.",
            "urgency": "ROUTINE",
            "category": "mental_health",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
        # ── Elderly/caregiver forum patterns ────────────────────
        {
            "question": "My 78-year-old mother keeps forgetting things — left the stove on twice, forgot my name once. Is this just normal aging or should we be worried about dementia?",
            "answer": "While some memory changes are normal with aging (like occasionally misplacing keys or forgetting a word), the symptoms you describe are concerning: leaving the stove on repeatedly and forgetting close family members' names are beyond typical age-related changes and suggest possible cognitive decline. Schedule an appointment with her primary care doctor or a neurologist within the next 1-2 weeks for a cognitive assessment. They may use tools like the MMSE or MoCA screening test. Early evaluation is important because some causes of cognitive decline are reversible (thyroid issues, vitamin B12 deficiency, depression, medication side effects), and if it is dementia, early intervention can help with planning and treatment.",
            "urgency": "SOON",
            "category": "geriatric",
            "data_type": "forum_qa",
            "source": "Curated from public medical forum patterns",
        },
    ]

    documents = []
    for qa in forum_qa:
        documents.append(
            {
                "title": f"Forum Q&A: {qa['question'][:60]}...",
                "content": f"Question: {qa['question']}\n\nAnswer: {qa['answer']}",
                "source": qa.get(
                    "source", "Curated from public medical forum patterns"
                ),
                "categories": [qa["category"]],
                "urgency": qa["urgency"],
                "data_type": qa["data_type"],
            }
        )

    print(f"  Created {len(documents)} public forum Q&A entries")
    return documents


# ──────────────────────────────────────────────────────────────
# SOURCE 6: Synthetic Q&A
# Common health inquiry patterns per project guidelines:
# "synthetic patient inquiry scenarios based on common
#  healthcare use cases" — OSRE project page
# ──────────────────────────────────────────────────────────────


def create_synthetic_qa_pairs():
    """
    Synthetic health conversations covering the patterns
    explicitly listed in the project scope.
    """
    print("\n[6/6] Creating synthetic Q&A pairs (per project guidelines)...")

    qa_pairs = [
        # ── Emergency (cardiac) ──────────────────────────────────
        {
            "question": "I have crushing chest pain that radiates to my left arm and I'm sweating",
            "answer": "EMERGENCY: These symptoms are warning signs of a heart attack. Call 911 IMMEDIATELY. Do not drive yourself. Chew an aspirin (325mg) if available and not allergic. Stay calm and sit down until help arrives.",
            "urgency": "EMERGENCY",
            "category": "cardiac",
        },
        {
            "question": "I have chest pressure and my jaw hurts and I feel nauseous",
            "answer": "EMERGENCY: Chest pressure with jaw pain and nausea can indicate a heart attack. Call 911 NOW. These symptoms require immediate emergency care. Do not ignore or wait.",
            "urgency": "EMERGENCY",
            "category": "cardiac",
        },
        # ── Emergency (neurological) ─────────────────────────────
        {
            "question": "I suddenly can't speak properly and one side of my face is drooping",
            "answer": "EMERGENCY: These are stroke symptoms. Call 911 immediately. Remember FAST: Face drooping, Arm weakness, Speech difficulty, Time to call 911. Every minute matters in a stroke.",
            "urgency": "EMERGENCY",
            "category": "neurological",
        },
        {
            "question": "The worst headache of my life came on suddenly 15 minutes ago",
            "answer": "EMERGENCY: A sudden severe headache described as the 'worst of your life' can indicate a brain bleed (subarachnoid hemorrhage). This is a medical emergency. Call 911 immediately.",
            "urgency": "EMERGENCY",
            "category": "neurological",
        },
        # ── Emergency (respiratory/allergic) ────────────────────
        {
            "question": "I'm having trouble breathing and my throat feels like it's closing up after eating peanuts",
            "answer": "EMERGENCY: This is anaphylaxis — a life-threatening allergic reaction. Call 911 IMMEDIATELY. Use an EpiPen if available. Do not wait to see if it improves.",
            "urgency": "EMERGENCY",
            "category": "allergic",
        },
        {
            "question": "I can't breathe properly and my lips are turning blue",
            "answer": "EMERGENCY: Blue lips (cyanosis) with difficulty breathing is a life-threatening emergency. Call 911 IMMEDIATELY. This indicates dangerously low oxygen levels.",
            "urgency": "EMERGENCY",
            "category": "respiratory",
        },
        # ── Emergency (overdose/poisoning) ──────────────────────
        {
            "question": "I took too many pills and I feel very drowsy",
            "answer": "EMERGENCY: Call 911 or Poison Control (1-800-222-1222) IMMEDIATELY. Tell them exactly what medication and how much. Do not try to vomit unless directed by professionals.",
            "urgency": "EMERGENCY",
            "category": "overdose",
        },
        # ── Emergency (mental health crisis) ────────────────────
        {
            "question": "I don't want to be here anymore and I'm thinking about ending things",
            "answer": "I'm deeply concerned and I want you to be safe. Please call or text 988 (Suicide and Crisis Lifeline) RIGHT NOW. You can also text HOME to 741741. Someone is available 24/7. You are not alone and help is available.",
            "urgency": "EMERGENCY",
            "category": "mental_health_crisis",
        },
        # ── Urgent ──────────────────────────────────────────────
        {
            "question": "I have a fever of 103°F that has lasted 3 days and I feel very weak",
            "answer": "This requires URGENT evaluation today. A high fever lasting 3 days needs diagnosis. Visit an urgent care clinic or ER today. Stay hydrated. Take acetaminophen or ibuprofen as directed while you seek care.",
            "urgency": "URGENT",
            "category": "fever",
        },
        {
            "question": "I've been having severe lower right abdominal pain for 6 hours that keeps getting worse",
            "answer": "This urgently needs evaluation — could be appendicitis. Please go to an ER or urgent care within the next few hours. Do not eat or drink until evaluated. Worsening lower right abdominal pain should always be assessed promptly.",
            "urgency": "URGENT",
            "category": "abdominal",
        },
        {
            "question": "My child has a fever of 104°F and is very lethargic and not responding normally",
            "answer": "URGENT: A 104°F fever with lethargy in a child needs immediate medical attention. Go to the ER or urgent care NOW. High fevers in children with altered responsiveness require prompt evaluation.",
            "urgency": "URGENT",
            "category": "pediatric",
        },
        # ── Routine ─────────────────────────────────────────────
        {
            "question": "I have a runny nose, mild sore throat, and slight cough for 2 days",
            "answer": "This sounds like a common cold, which usually resolves in 7-10 days. Rest, drink plenty of fluids, and use over-the-counter remedies for symptom relief. See a doctor if symptoms worsen significantly or last more than 10 days.",
            "urgency": "ROUTINE",
            "category": "respiratory",
        },
        {
            "question": "I have a mild headache that started this morning, about a 3 out of 10",
            "answer": "A mild headache can often be managed at home. Drink water (dehydration is common), rest in a quiet dark room, and consider over-the-counter pain relievers like acetaminophen or ibuprofen. Seek care if the headache worsens dramatically or is accompanied by fever and stiff neck.",
            "urgency": "ROUTINE",
            "category": "headache",
        },
        {
            "question": "I've been more tired than usual for the past week",
            "answer": "Fatigue lasting a week can have many causes: poor sleep, stress, dehydration, or nutritional deficiencies. Try improving sleep, staying hydrated, and eating balanced meals. If fatigue persists beyond 2-3 weeks or is accompanied by weight loss, fever, or shortness of breath, schedule a doctor's appointment.",
            "urgency": "ROUTINE",
            "category": "general",
        },
        {
            "question": "I have a small cut on my finger from cooking that is still bleeding after 10 minutes",
            "answer": "Apply firm direct pressure with a clean cloth for 10-15 minutes without lifting. Elevate your hand above heart level. If bleeding does not stop after 20-30 minutes of direct pressure, or the wound is deep or gaping, seek urgent care.",
            "urgency": "SELF_CARE",
            "category": "wound",
        },
        # ── Self-care ────────────────────────────────────────────
        {
            "question": "I have mild sunburn on my arms and shoulders",
            "answer": "For mild sunburn: apply cool compresses, use aloe vera or gentle moisturizer, drink extra water, and take ibuprofen or acetaminophen for discomfort. Avoid further sun exposure until healed. See a doctor if you have blistering over large areas, fever, or severe pain.",
            "urgency": "SELF_CARE",
            "category": "skin",
        },
        # ── Clarification scenarios ──────────────────────────────
        {
            "question": "My stomach hurts",
            "answer": "I want to help you better. Can you tell me more? Where exactly does it hurt (upper, lower, left, right side, or all over)? How severe is the pain on a scale of 1-10? How long have you had it? Do you have any other symptoms like nausea, vomiting, fever, or diarrhea?",
            "urgency": "NEEDS_CLARIFICATION",
            "category": "abdominal",
        },
        {
            "question": "I don't feel well",
            "answer": "I'm sorry you're not feeling well. To help you better, could you describe your symptoms? For example: What exactly are you experiencing? When did it start? How severe is it on a scale of 1-10? Any fever, pain, or difficulty breathing?",
            "urgency": "NEEDS_CLARIFICATION",
            "category": "general",
        },
        # ── Chronic condition management ─────────────────────────
        {
            "question": "My blood sugar has been running higher than normal this week — I have type 2 diabetes",
            "answer": "Elevated blood sugar can be caused by illness, stress, diet changes, or medication timing. Check your glucose more frequently. If blood sugar remains very high (over 300 mg/dL) or you have symptoms like extreme thirst or confusion, contact your doctor or seek urgent care.",
            "urgency": "SOON",
            "category": "diabetes",
        },
        {
            "question": "I have asthma and my inhaler isn't helping my symptoms much today",
            "answer": "If your rescue inhaler is not providing relief, this could indicate worsening asthma. If you are having significant difficulty breathing, use your rescue inhaler, sit upright, and go to the ER if breathing does not improve within 15-20 minutes. Contact your doctor today even if breathing improves.",
            "urgency": "URGENT",
            "category": "asthma",
        },
        # ── Mental health ────────────────────────────────────────
        {
            "question": "I've been feeling very depressed and hopeless and have no motivation for weeks",
            "answer": "I hear you, and I'm glad you're reaching out. Depression is a real medical condition with effective treatments available. I encourage you to speak with your doctor or a mental health professional. If you are having any thoughts of harming yourself, please call or text 988 (Suicide and Crisis Lifeline) right away.",
            "urgency": "URGENT",
            "category": "mental_health",
        },
        {
            "question": "I've been having severe anxiety and panic attacks that wake me up at night",
            "answer": "Panic attacks are distressing but not life-threatening. During an attack: focus on slow deep breaths (breathe in for 4 counts, hold 4, out for 4). Frequent panic attacks affecting your sleep warrant evaluation by a doctor or mental health professional.",
            "urgency": "SOON",
            "category": "mental_health",
        },
        # ── Healthcare navigation ────────────────────────────────
        {
            "question": "What type of doctor should I see for recurring migraines?",
            "answer": "Start with your primary care physician (PCP) who can provide initial treatment and referrals. If migraines are frequent or severe, ask for a referral to a neurologist who specializes in headache disorders. Keep a headache diary noting frequency, triggers, and duration to bring to your appointment.",
            "urgency": "ROUTINE",
            "category": "find_doctor",
        },
        {
            "question": "My doctor prescribed metformin. What is it for?",
            "answer": "Metformin is most commonly prescribed to treat type 2 diabetes. It lowers blood sugar mainly by reducing the amount of glucose your liver releases and improving insulin sensitivity. It is usually taken with meals to reduce stomach side effects. Always follow your doctor's dosing instructions.",
            "urgency": "ROUTINE",
            "category": "medication_info",
        },
        # ── Clinical practice guideline–based entries ────────────
        {
            "question": "When should adults get a colonoscopy?",
            "answer": "The U.S. Preventive Services Task Force (USPSTF) recommends screening for colorectal cancer starting at age 45 and continuing through age 75 for average-risk adults. Screening options include a colonoscopy every 10 years, or a stool-based test (FIT) annually. Talk with your doctor about which screening schedule is right for you.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        {
            "question": "How often should blood pressure be checked?",
            "answer": "Adults 18 and older should have their blood pressure checked at least once every two years if it is normal (below 120/80 mmHg). If it is elevated (120-129/<80) or if you have risk factors, check it at least annually. High blood pressure usually has no symptoms, so regular monitoring is very important.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        {
            "question": "What are the guidelines for mammogram screenings?",
            "answer": "The USPSTF recommends biennial (every 2 years) mammography screening for women starting at age 40 through age 74. Women at higher risk (family history of breast cancer, genetic mutations like BRCA1/2) may need to start earlier or get screened more frequently. Discuss your personal risk with your doctor.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        {
            "question": "Should I get a flu shot every year?",
            "answer": "Yes. The CDC recommends annual influenza vaccination for everyone 6 months of age and older. Flu viruses change each season, so a new vaccine is needed every year. The best time to get vaccinated is before flu season begins, usually by the end of October. Vaccination is especially important for people over 65, pregnant women, and those with chronic health conditions.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        {
            "question": "What is the recommended treatment for mild to moderate hypertension?",
            "answer": "According to clinical guidelines, initial treatment for mild to moderate hypertension (stage 1: 130-139/80-89 mmHg) starts with lifestyle modifications: reducing sodium intake to less than 2300 mg/day, regular aerobic exercise (150 minutes/week), maintaining a healthy weight, and limiting alcohol. If blood pressure remains elevated after 3-6 months, your doctor may prescribe medication such as an ACE inhibitor, ARB, calcium channel blocker, or thiazide diuretic.",
            "urgency": "ROUTINE",
            "category": "chronic_disease",
        },
        {
            "question": "How should type 2 diabetes be managed day to day?",
            "answer": "Daily diabetes management includes: monitoring blood sugar levels as directed by your doctor, taking medications consistently, eating balanced meals with controlled carbohydrate portions, regular physical activity (at least 150 minutes of moderate exercise per week), and attending regular check-ups including A1C testing every 3-6 months. Target A1C is generally below 7% for most adults. Always consult your healthcare team for a personalized plan.",
            "urgency": "ROUTINE",
            "category": "chronic_disease",
        },
        # ── Healthcare navigation ────────────────────────────────
        {
            "question": "I don't have health insurance. Where can I get medical care?",
            "answer": "If you don't have insurance, you still have options for affordable care: Federally Qualified Health Centers (FQHCs) offer sliding-scale fees based on income. Many hospitals have charity care programs. Urgent care clinics often cost less than ERs. Check Healthcare.gov for marketplace plans or Medicaid eligibility. Some pharmacies offer low-cost clinics for basic care. Prescription assistance programs like GoodRx can reduce medication costs. Community health centers are available nationwide — find one at findahealthcenter.hrsa.gov.",
            "urgency": "ROUTINE",
            "category": "healthcare_navigation",
        },
        {
            "question": "How do I find a specialist without a referral?",
            "answer": "Many specialists accept patients without referrals, depending on your insurance plan. PPO plans typically allow direct specialist visits. HMO plans usually require a referral from your primary care physician. To find a specialist: check your insurance provider directory, ask your PCP for recommendations, use hospital finder tools online, or call the specialist's office to ask if they accept your insurance and whether a referral is needed.",
            "urgency": "ROUTINE",
            "category": "healthcare_navigation",
        },
        # ── Pediatric care topics ────────────────────────────────
        {
            "question": "My newborn has a fever of 100.4°F (rectal). What should I do?",
            "answer": "URGENT: Any fever (100.4°F/38°C or higher) in a baby under 3 months old requires immediate medical evaluation. Go to the emergency room or call your pediatrician right away. Do NOT give fever-reducing medicine to a baby this young without medical direction. Fever in newborns can indicate a serious infection that needs prompt treatment.",
            "urgency": "URGENT",
            "category": "pediatric",
        },
        {
            "question": "What is the childhood vaccination schedule?",
            "answer": "The CDC recommended childhood vaccination schedule includes: Birth: Hepatitis B; 2 months: DTaP, IPV, Hib, PCV13, Rotavirus, Hepatitis B; 4 months: DTaP, IPV, Hib, PCV13, Rotavirus; 6 months: DTaP, IPV, Hib, PCV13, Hepatitis B, Influenza; 12-15 months: MMR, Varicella, Hepatitis A, PCV13, Hib; 4-6 years: DTaP, IPV, MMR, Varicella. Flu vaccine annually starting at 6 months. COVID vaccine as recommended. Talk to your pediatrician for the most current schedule and any catch-up vaccinations needed.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        # ── Elderly/geriatric care ───────────────────────────────
        {
            "question": "What health screenings should adults over 65 get?",
            "answer": "Adults over 65 should discuss these screenings with their doctor: Annual wellness visit and physical exam. Blood pressure check at every visit. Cholesterol screening every 4-6 years. Diabetes screening (fasting glucose or A1C). Colonoscopy every 10 years through age 75. Annual flu and pneumonia vaccines. Shingles vaccine (Shingrix, 2 doses). Bone density scan (DEXA) for osteoporosis, especially for women. Vision and hearing tests annually. Depression screening. Cognitive assessment if concerns arise. Lung cancer screening (annual low-dose CT) if history of heavy smoking.",
            "urgency": "ROUTINE",
            "category": "preventive_care",
        },
        # ── Medication safety ────────────────────────────────────
        {
            "question": "What should I know about drug interactions?",
            "answer": "Drug interactions occur when one medication affects how another works, potentially causing side effects or reducing effectiveness. Important safety practices: Always tell your doctor and pharmacist about ALL medications you take, including over-the-counter drugs, supplements, and herbal products. Don't start or stop medications without consulting your doctor. Read medication guides and warning labels. Avoid grapefruit with certain medications (statins, blood pressure drugs). Don't mix alcohol with sedatives, painkillers, or anti-anxiety medications. Use one pharmacy so they can check for interactions automatically.",
            "urgency": "ROUTINE",
            "category": "medication_info",
        },
        # ── Wellness and lifestyle ───────────────────────────────
        {
            "question": "What are evidence-based strategies for better sleep?",
            "answer": "Sleep hygiene practices recommended by sleep medicine experts: Maintain a consistent sleep schedule (same bedtime and wake time daily). Create a cool, dark, quiet sleep environment. Avoid screens for 30-60 minutes before bed. Limit caffeine after 2 PM. Exercise regularly, but not within 3 hours of bedtime. Avoid large meals close to bedtime. Use the bed only for sleep and intimacy. If you can't fall asleep within 20 minutes, get up and do something relaxing until you feel sleepy. Consider cognitive behavioral therapy for insomnia (CBT-I) if sleep problems persist. Consult a doctor if you have persistent insomnia, loud snoring, or excessive daytime sleepiness.",
            "urgency": "ROUTINE",
            "category": "wellness",
        },
    ]

    # Transform to standard document format (title/content) so cleaner doesn't
    # filter them out — cleaner checks doc.get("content", "") for min length.
    documents = []
    for qa in qa_pairs:
        documents.append(
            {
                "title": qa["question"],
                "content": f"Q: {qa['question']}\nA: {qa['answer']}",
                "source": "synthetic_qa",
                "url": "",
                "category": qa.get("category", "general"),
                "urgency": qa.get("urgency", "ROUTINE"),
            }
        )

    print(f"  Created {len(documents)} synthetic Q&A pairs")
    return documents


# ──────────────────────────────────────────────────────────────
# MAIN COLLECTION PIPELINE
# ──────────────────────────────────────────────────────────────


def save_documents(documents, filename):
    """Saves collected documents to a JSON file."""
    filepath = RAW_DATA_DIR / filename
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(documents, f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(documents)} documents -> {filepath}")


def _load_existing_raw(filename):
    """Load documents from an existing raw file."""
    with open(RAW_DATA_DIR / filename, encoding="utf-8") as f:
        return json.load(f)


def collect_data(force=False):
    """Main function — runs the full data collection from all sources.

    Args:
        force: If True, re-fetch and overwrite all existing raw files.
               If False (default), skip any source whose output file already exists.
    """
    print("=" * 60)
    print("NeuroHealth Data Collection")
    print("Sources: MedlinePlus + Mayo Clinic + Clinical Guidelines")
    print("         + Public Forum Q&A + Synthetic Q&A")
    print("Project: https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/")
    if force:
        print("Mode: FORCE — all sources will be re-fetched and overwritten")
    else:
        print(
            "Mode: INCREMENTAL — existing files will be skipped (use --force to re-fetch)"
        )
    print("=" * 60)

    def _maybe_fetch(filename, fetch_fn, label):
        filepath = RAW_DATA_DIR / filename
        if not force and filepath.exists():
            docs = _load_existing_raw(filename)
            print(
                f"\n{label} Skipping {filename} — already exists ({len(docs)} docs). Use --force to re-fetch."
            )
            return docs
        docs = fetch_fn()
        save_documents(docs, filename)
        return docs

    # Source 1: MedlinePlus full health topics XML
    health_topics = _maybe_fetch(
        "medlineplus_topics.json", fetch_medlineplus_health_topics, "[1/6]"
    )

    # Source 2: MedlinePlus term definitions
    definitions = _maybe_fetch(
        "medlineplus_definitions.json", fetch_medlineplus_definitions, "[2/6]"
    )

    # Source 3: Mayo Clinic health information
    mayo_data = _maybe_fetch("mayo_clinic_data.json", fetch_mayo_clinic_data, "[3/6]")

    # Source 4: Clinical practice guidelines
    guidelines = _maybe_fetch(
        "clinical_guidelines.json", create_clinical_guidelines_data, "[4/6]"
    )

    # Source 5: Public forum Q&A
    forum_qa = _maybe_fetch(
        "public_forum_qa.json", create_public_forum_qa_data, "[5/6]"
    )

    # Source 6: Synthetic Q&A
    qa_pairs = _maybe_fetch("synthetic_qa.json", create_synthetic_qa_pairs, "[6/6]")

    total = (
        len(health_topics)
        + len(definitions)
        + len(mayo_data)
        + len(guidelines)
        + len(forum_qa)
        + len(qa_pairs)
    )
    print(f"\n{'='*60}")
    print(f"Collection complete. Total documents: {total}")
    print(f"  MedlinePlus health topics   : {len(health_topics)}")
    print(f"  MedlinePlus definitions     : {len(definitions)}")
    print(f"  Mayo Clinic conditions      : {len(mayo_data)}")
    print(f"  Clinical practice guidelines: {len(guidelines)}")
    print(f"  Public forum Q&A            : {len(forum_qa)}")
    print(f"  Synthetic Q&A pairs         : {len(qa_pairs)}")
    print(f"{'='*60}")


# Keep old name as alias so any test that calls run_data_collection() still works
def run_data_collection():
    collect_data()


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    collect_data(force=force)
