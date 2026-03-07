# 🧠 NeuroHealth

[![License: CC BY 4.0](https://img.shields.io/badge/License-CC_BY_4.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![LLM: Llama 3.1-8B](https://img.shields.io/badge/LLM-Llama_3.1--8B-purple.svg)](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)
[![OSRE 2026](https://img.shields.io/badge/OSRE-2026-green.svg)](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/)

**AI-Powered Health Assistant** — An intelligent health chatbot that uses RAG (Retrieval-Augmented Generation) with a locally-hosted Llama 3.1-8B model to provide safe, evidence-informed health guidance. Built as part of the [UC Santa Cruz OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/) program.

> ⚠️ **Medical Disclaimer:** NeuroHealth is a research prototype and is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns. In an emergency, call **911** immediately.

---

## Features

- **Symptom Assessment** — Understands and extracts symptoms from natural language
- **Urgency Triage** — Classifies urgency (Emergency → Self-Care) using clinical principles
- **Medical Knowledge Retrieval** — RAG pipeline retrieves relevant medical information before responding
- **Safety Guardrails** — Every response is checked for dangerous advice before being shown
- **Mental Health Crisis Detection** — Detects suicidal ideation and self-harm, provides crisis resources (988 Lifeline)
- **Multi-turn Conversations** — Remembers context across conversation turns
- **Appointment Recommendations** — Suggests appropriate specialists and timing
- **Preventive Care Guidance** — Wellness, screening, and vaccination recommendations
- **Health Literacy Adaptation** — Adjusts language complexity to match the user's level
- **Data Validation** — Validates medical data integrity before indexing
- **Poison Control Detection** — Detects overdose/poisoning and provides Poison Control resources
- **Ablation Studies** — Measures each component's contribution to overall performance
- **Equity Evaluation** — Tests consistency across demographics and health literacy levels
- **Inference Profiling** — Component-level latency analysis for optimization

## Tech Stack

| Component        | Technology                                                           |
| ---------------- | -------------------------------------------------------------------- |
| **LLM**          | Llama 3.1-8B-Instruct (local, zero API cost)                         |
| **Embeddings**   | all-MiniLM-L6-v2 (sentence-transformers, local)                      |
| **Vector DB**    | ChromaDB (persistent, local)                                         |
| **Web UI**       | Streamlit                                                            |
| **API**          | FastAPI                                                              |
| **GPU**          | Nvidia A100 40GB (JupyterLab)                                        |
| **Data Sources** | MedlinePlus, Mayo Clinic, Clinical Guidelines, Public Q&A, Synthetic |

## Data Sources

| #   | Source                           | Type            | Description                                                                                |
| --- | -------------------------------- | --------------- | ------------------------------------------------------------------------------------------ |
| 1   | **MedlinePlus Health Topics**    | Web API (XML)   | NIH/NLM curated health topic summaries                                                     |
| 2   | **MedlinePlus Definitions**      | Web API (XML)   | Medical term definitions and explanations                                                  |
| 3   | **Mayo Clinic**                  | Web scraping    | Condition pages for 20 common conditions                                                   |
| 4   | **Clinical Practice Guidelines** | Curated dataset | 17 guidelines from USPSTF, AHA, ADA, CDC, ACOG, AAFP, ACEP                                 |
| 5   | **Public Medical Q&A**           | Curated dataset | 15 forum-style Q&A entries covering ambiguous, pediatric, elderly, mental health scenarios |
| 6   | **Synthetic Q&A**                | Generated       | Condition-based question-answer pairs for knowledge coverage                               |

## Architecture

```
User Input
    │
    ▼
┌───────────────────────┐
│   Intent Recognizer   │  ← Classifies: SYMPTOM_CHECK, EMERGENCY, MEDICATION_INFO,
│                       │     PREVENTIVE_CARE, MENTAL_HEALTH, OUT_OF_SCOPE, etc.
└──────────┬────────────┘
           │
    ┌──────┴──────────────────────────────┐
    │                                      │
    ▼                                      ▼
┌──────────────┐  ┌──────────┐  ┌─────────────────┐
│ Symptom      │  │ Urgency  │  │ Knowledge Base  │
│ Extractor    │  │ Assessor │  │ (RAG Retriever) │
└──────┬───────┘  └────┬─────┘  └────────┬────────┘
       │               │                 │
       └───────────────┴─────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │   LLM Generator │  ← Llama 3.1-8B with retrieved context
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Safety Guardrails│ ← Regex + LLM safety review
              └────────┬────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ Response Formatter│
              └────────┬────────┘
                       │
                       ▼
                 Final Response
```

## Project Structure

```
NeuroHealth/
├── src/
│   ├── llm_utils.py              ← Shared local Llama inference (singleton)
│   ├── pipeline.py               ← Main pipeline (connects everything)
│   ├── data_pipeline/
│   │   ├── collector.py          ← Collects medical data (MedlinePlus, Mayo Clinic, CPGs, forums, synthetic)
│   │   ├── cleaner.py            ← Cleans and normalizes text (preserves medical notation)
│   │   ├── chunker.py            ← Splits text into overlapping searchable chunks
│   │   ├── validator.py          ← Validates data quality and medical accuracy
│   │   └── entity_schema.py      ← Structured symptom/condition/urgency/specialist schema
│   ├── knowledge_base/
│   │   ├── embedder.py           ← Converts text to vector embeddings
│   │   └── vector_store.py       ← ChromaDB vector database with deduplication
│   ├── rag/
│   │   ├── retriever.py          ← Finds relevant medical info from vector store
│   │   └── generator.py          ← Generates the final answer (health-literacy aware)
│   └── modules/
│       ├── intent_recognizer.py  ← Classifies user intent (10 categories)
│       ├── symptom_extractor.py  ← Extracts structured symptoms with body systems
│       ├── urgency_assessor.py   ← Determines urgency level (5-level triage)
│       ├── appointment_recommender.py ← Recommends specialists + preparation
│       ├── safety_guardrails.py  ← Multi-layer safety checks on every response
│       ├── conversation_manager.py ← Session memory + health context tracking
│       └── response_formatter.py ← Formats final output with urgency indicators
│   ├── data_pipeline/
├── evaluation/
│   ├── benchmarks.py             ← Automated performance tests (23+ cases)
│   ├── safety_tests.py           ← Adversarial safety tests (27+ cases)
│   ├── ablation_study.py         ← Component contribution analysis (6 configs)
│   ├── equity_tests.py           ← Demographic equity evaluation
│   ├── inference_profiler.py     ← Inference latency profiling
│   ├── human_evaluation.py       ← Human evaluation forms (7 dimensions)
│   ├── baseline_comparison.py    ← Baseline/external system benchmarking
│   └── test_cases/               ← JSON-based test cases (auto-loaded)
├── ui/
│   └── app.py                    ← Streamlit web interface
├── api/
│   ├── main.py                   ← FastAPI application
│   └── routes.py                 ← API endpoints
├── tests/
│   ├── conftest.py               ← Pytest configuration and shared fixtures
│   ├── test_data_pipeline.py     ← Data pipeline unit tests
│   ├── test_modules.py           ← Module unit tests (no GPU needed)
│   ├── test_rag.py               ← RAG component tests
│   └── test_pipeline.py          ← End-to-end pipeline tests (GPU needed)
├── data/                         ← Created at runtime (contents git-ignored)
│   ├── raw/                      ← Raw collected data (JSON)
│   ├── processed/                ← Cleaned, chunked, embedded data
│   └── vector_db/                ← ChromaDB persistent store
├── .env                          ← Environment variables (NOT in git)
├── .env.example                  ← Environment variable template
├── .gitignore
├── requirements.txt
├── pyproject.toml                ← Project metadata and build configuration
├── LICENSE                       ← CC BY 4.0
├── GUIDE.md                      ← Complete build guide
├── CONTRIBUTING.md               ← Contribution guidelines
└── README.md
```

---

## Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/prthmmkhija1/NeuroHealth.git
cd NeuroHealth
```

### 2. Create Environment

```bash
conda create -n neurohealth python=3.11 -y
conda activate neurohealth
pip install -r requirements.txt
```

### 3. Configure `.env`

Create a `.env` file in the project root:

```env
USE_LOCAL_LLM=true
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_TOKEN=hf_YOUR_TOKEN_HERE
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./data/vector_db
MAX_NEW_TOKENS=1024
TEMPERATURE=0.3
```

> You need a HuggingFace token with access to the Llama 3.1 model. Apply at [meta-llama/Llama-3.1-8B-Instruct](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct).

### 4. Build the Knowledge Base

Run these in order:

```bash
python src/data_pipeline/collector.py    # Collect medical data from MedlinePlus
python src/data_pipeline/cleaner.py      # Clean and normalize text
python src/data_pipeline/chunker.py      # Split into overlapping chunks
python src/knowledge_base/embedder.py    # Generate vector embeddings
python src/knowledge_base/vector_store.py # Build ChromaDB vector store
```

### 5. Run Tests

```bash
# Module tests (no GPU needed — tests keyword logic, formatters, safety regex)
python tests/test_modules.py

# Data pipeline tests (no GPU needed — tests collector, cleaner, chunker)
python tests/test_data_pipeline.py

# RAG tests (needs vector store built)
python tests/test_rag.py

# End-to-end tests (needs GPU + model loaded)
python tests/test_pipeline.py
```

### 6. Launch the Web UI

```bash
streamlit run ui/app.py
# Opens at http://localhost:8501
```

### 7. Launch the API

```bash
uvicorn api.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

---

## API Reference

### Base URL

```
http://localhost:8000
```

### Endpoints

#### `GET /`

Health check / service info.

**Response:**

```json
{
  "name": "NeuroHealth API",
  "version": "1.0.0",
  "status": "running",
  "docs": "/docs"
}
```

#### `GET /health`

Liveness probe.

**Response:**

```json
{ "status": "healthy" }
```

#### `POST /api/v1/chat`

Send a message to NeuroHealth and receive a health assistant response.

**Request Body:**

```json
{
  "message": "I have a headache and fever for 2 days",
  "session_id": null
}
```

| Field        | Type   | Required | Description                                       |
| ------------ | ------ | -------- | ------------------------------------------------- |
| `message`    | string | Yes      | The user's health question or symptom description |
| `session_id` | string | No       | Session ID for multi-turn conversation continuity |

**Response:**

```json
{
  "session_id": "20250101_120000",
  "response_text": "🟡 SEE DOCTOR SOON\n\nBased on your symptoms...",
  "urgency_level": "SOON",
  "urgency_color": "#FFCC00"
}
```

| Field           | Type   | Description                                         |
| --------------- | ------ | --------------------------------------------------- |
| `session_id`    | string | Use this in subsequent requests for multi-turn      |
| `response_text` | string | Formatted response with urgency indicator           |
| `urgency_level` | string | One of: EMERGENCY, URGENT, SOON, ROUTINE, SELF_CARE |
| `urgency_color` | string | Hex color code for the urgency level                |

#### `GET /api/v1/sessions/{session_id}`

Retrieve conversation history for a session.

**Response:**

```json
{
  "session_id": "20250101_120000",
  "created_at": "2025-01-01 12:00:00",
  "message_count": 3,
  "messages": [
    { "role": "user", "content": "I have a headache" },
    { "role": "assistant", "content": "..." }
  ],
  "health_context": {
    "symptoms_mentioned": ["headache"],
    "urgency_history": [{ "turn": 1, "level": "ROUTINE" }]
  }
}
```

#### `POST /api/v1/chat/stream`

SSE (Server-Sent Events) streaming version of `/chat`. Returns events progressively for real-time rendering on web/mobile clients.

**Request Body:** Same as `POST /chat`.

**Response:** `Content-Type: text/event-stream`

Each SSE event is a JSON object:

```
data: {"type": "metadata", "session_id": "...", "urgency_level": "ROUTINE", "urgency_color": "#00CC00"}
data: {"type": "token", "text": "Based on your "}
data: {"type": "token", "text": "symptoms, it sounds "}
data: {"type": "done", "session_id": "..."}
```

#### `POST /api/v1/feedback`

Submit user satisfaction feedback (CSAT/MOS tracking).

**Request Body:**

```json
{
  "session_id": "20250101_120000",
  "rating": 4,
  "thumbs": "up",
  "comment": "Very helpful response"
}
```

#### `GET /api/v1/feedback/summary`

Get aggregated satisfaction metrics.

**Response:**

```json
{
  "total": 42,
  "average_rating": 4.2,
  "thumbs_up": 35,
  "thumbs_down": 7,
  "csat_score": 78.6
}
```

### Example Usage (cURL)

```bash
# Start a conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have a bad headache and stiff neck"}'

# Continue the conversation
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "It started yesterday", "session_id": "SESSION_ID_FROM_ABOVE"}'
```

### Example Usage (Python)

```python
import requests

# Send a message
response = requests.post("http://localhost:8000/api/v1/chat", json={
    "message": "I have chest pain and difficulty breathing",
})
data = response.json()
print(data["urgency_level"])    # "EMERGENCY"
print(data["response_text"])    # Full formatted response with 911 guidance
```

---

## Deployment

### Local Development (HP-INT — no GPU)

Best for coding, testing keyword logic, and UI work.

```bash
conda activate neurohealth
# Run non-LLM tests
python tests/test_modules.py
python tests/test_data_pipeline.py
# Run Streamlit UI (will error on LLM calls without GPU)
streamlit run ui/app.py
```

### GPU Server (JLAB-GPU — A100)

Best for full inference, embedding, and evaluation.

```bash
conda activate neurohealth
# Build knowledge base
python src/data_pipeline/collector.py
python src/data_pipeline/cleaner.py
python src/data_pipeline/chunker.py
python src/knowledge_base/embedder.py
python src/knowledge_base/vector_store.py

# Run full test suite
python tests/test_modules.py
python tests/test_data_pipeline.py
python tests/test_rag.py
python tests/test_pipeline.py

# Run evaluation
python evaluation/benchmarks.py
python evaluation/safety_tests.py
python evaluation/ablation_study.py
python evaluation/equity_tests.py
python evaluation/inference_profiler.py

# Launch services
streamlit run ui/app.py &
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Sync Between Environments

```bash
# On HP-INT: push code
git add -A && git commit -m "update" && git push

# On JLAB-GPU: pull and run
git pull && python src/pipeline.py
```

---

## Urgency Levels

| Level                  | Color  | Action                  | Response Time           |
| ---------------------- | ------ | ----------------------- | ----------------------- |
| 🔴 EMERGENCY           | Red    | Call 911 immediately    | Immediate               |
| 🟠 URGENT              | Orange | See doctor within hours | Same day                |
| 🟡 SOON                | Yellow | See doctor in 1-2 days  | 1-2 days                |
| 🟢 ROUTINE             | Green  | Schedule an appointment | This week               |
| 🔵 SELF_CARE           | Blue   | Manage at home          | Self-guided             |
| ⚪ NEEDS_CLARIFICATION | Gray   | More info needed        | Ask follow-up questions |

## Intent Categories

| Intent           | Description                                 |
| ---------------- | ------------------------------------------- |
| EMERGENCY        | Life-threatening situation detected         |
| SYMPTOM_CHECK    | User describing symptoms                    |
| MEDICATION_INFO  | Asking about medications or supplements     |
| FIND_DOCTOR      | Looking for healthcare providers            |
| APPOINTMENT_BOOK | Scheduling/changing appointments            |
| GENERAL_INFO     | General health/medical questions            |
| MENTAL_HEALTH    | Emotional or mental health concerns         |
| PREVENTIVE_CARE  | Wellness, screenings, vaccinations          |
| FOLLOW_UP        | Following up on previous medical encounters |
| OUT_OF_SCOPE     | Non-health-related messages                 |

## Safety

- **Multi-layer safety architecture:**
  1. Emergency keyword detection runs **before** the LLM (instant, reliable)
  2. Regex pattern matching catches dangerous advice, definitive diagnoses, and dismissive reassurance
  3. Mental health crisis detection with automatic 988 Lifeline and Crisis Text Line resources
  4. LLM-based safety review catches subtle issues missed by regex
  5. Automatic correction: unsafe responses are fixed before being shown to users
- **Emergency recall target: 100%** — never miss a life-threatening case
- **Responses never diagnose** — only suggest possibilities
- **Prescription medication is never recommended** with specific dosing
- **Anti-science misinformation is rejected** (e.g., anti-vaccine claims)
- **Disclaimer is always present** in health-related responses

## Evaluation

Run the evaluation suite on a GPU environment:

```bash
# Benchmarks — tests urgency accuracy, emergency recall, intent classification
python evaluation/benchmarks.py

# Safety tests — adversarial jailbreaks, crisis detection, edge cases
python evaluation/safety_tests.py

# Ablation study — measures contribution of each pipeline component
python evaluation/ablation_study.py

# Equity tests — demographic consistency across age, literacy, gender
python evaluation/equity_tests.py

# Inference profiling — latency breakdown per component
python evaluation/inference_profiler.py

# Human evaluation — generates scoring forms for healthcare professionals
python evaluation/human_evaluation.py

# Baseline comparison — benchmark vs keyword baseline and external systems
python evaluation/baseline_comparison.py
```

Key metrics:

- **Emergency Recall**: Must be 100% (all emergency cases correctly identified)
- **Urgency Accuracy**: Percentage of urgency levels correctly assigned
- **Intent Accuracy**: Percentage of intents correctly classified
- **Safety Pass Rate**: Percentage of adversarial tests handled safely
- **Equity Consistency**: Urgency consistency across demographic groups
- **Ablation Δ**: Performance change when each component is disabled

### Results (GPU Run — Nvidia A100, March 7 2026)

#### Benchmark Performance (37 test cases)

| Metric               | NeuroHealth   |
| -------------------- | ------------- |
| **Emergency Recall** | **100%** ✅   |
| Overall Pass Rate    | 64.9% (24/37) |
| Urgency Accuracy     | 57.7%         |
| Intent Accuracy      | 75.0%         |
| Safety Pass Rate     | 97.3%         |

> **Emergency Recall = 100%** is the primary safety requirement. Every life-threatening case (chest pain, stroke, anaphylaxis, overdose, suicidal crisis) was correctly identified and routed to emergency services.
>
> The 57.7% urgency accuracy reflects conservative over-triage (e.g., ROUTINE cases classified as SOON), which is clinically safer than under-triage.

#### Baseline Comparison

| System                               | Emergency Recall | Urgency Accuracy |
| ------------------------------------ | ---------------- | ---------------- |
| **NeuroHealth (RAG + Llama 3.1-8B)** | **100%**         | 61.1%            |
| Keyword/Rule-Based Baseline          | 50%              | 72.2%            |

> NeuroHealth achieves **2× emergency recall** vs the keyword baseline, the critical safety improvement this project targets.

#### Ablation Study (6 configurations)

| Configuration           | Emergency Recall | Intent Accuracy | Safety Pass Rate |
| ----------------------- | ---------------- | --------------- | ---------------- |
| Full Pipeline           | **100%**         | 75.0%           | 97.3%            |
| No RAG                  | 100%             | 85.7%           | 94.6%            |
| No Safety Guardrails    | 100%             | 85.7%           | 97.3%            |
| No Intent Module        | 100%             | 32.1%           | 97.3%            |
| **No Urgency Module**   | **0%**           | 85.7%           | 97.3%            |
| No Conversation History | 100%             | 85.7%           | 97.3%            |

> Removing the Urgency Assessment module drops Emergency Recall to **0%**, confirming it is the most safety-critical component.

#### Safety & Adversarial Testing (27 adversarial cases)

| Category                  | Tests | Passed | Failed   |
| ------------------------- | ----- | ------ | -------- |
| Jailbreak attempts        | 4     | 4      | 0        |
| Mental health crisis      | 4     | 4      | 0        |
| Ambiguous symptoms        | 3     | 3      | 0        |
| Overdose / Poison Control | 1     | 1      | 0        |
| Prescription fishing      | 1     | 1      | 0        |
| Misinformation            | 2     | 1      | 1 (HIGH) |
| Chronic disease           | 2     | 1      | 1 (HIGH) |
| Pediatric                 | 1     | 0      | 1 (HIGH) |
| Preventive care           | 2     | 1      | 1 (HIGH) |
| Healthcare navigation     | 1     | 1      | 0        |
| **CRITICAL failures**     | —     | —      | **0**    |

> 0 CRITICAL failures. The 4 HIGH failures involve edge-case content checks (not safety bypasses) and are noted for future improvement.

#### Equity Evaluation

| Group                            | Consistency |
| -------------------------------- | ----------- |
| Age groups (emergency scenarios) | 100%        |
| Health literacy levels           | 100%        |
| Overall demographic consistency  | **83.3%**   |

> Inconsistency noted in age-group handling for mild, non-emergency pediatric vs. senior scenarios — flagged for future work.

#### Inference Profiling (Nvidia A100 40 GB)

| Component                  | Mean Latency |
| -------------------------- | ------------ |
| Intent Recognition         | 2.97s        |
| Symptom Extraction         | 5.95s        |
| RAG Retrieval              | 1.27s        |
| Urgency Assessment         | 8.28s        |
| Appointment Recommendation | 10.34s       |
| Response Generation        | 16.11s       |
| Safety Check               | 3.24s        |
| **Total (avg)**            | **48.2s**    |

> Warmup time (first inference): 67s for model loading. Subsequent requests average 48s end-to-end on a local Llama 3.1-8B inference stack.

### Human Evaluation

Per the OSRE specification, NeuroHealth includes a **human evaluation framework** for healthcare professionals. Run `python evaluation/human_evaluation.py` to generate:

- **JSON evaluation forms** with 7 scoring dimensions (clinical safety, accuracy, appropriateness, health literacy, completeness, empathy/tone, user satisfaction)
- **CSV scoring sheets** ready for distribution to clinical reviewers
- **8 curated test cases** spanning emergency, routine, mental health, chronic disease, pediatric, and ambiguous scenarios

Each case is scored on a 1-5 scale across all dimensions by human reviewers.

## Contributing

This project is part of the [OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/) program at UC Santa Cruz Open Source Program Office (OSPO). See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest tests/`)
5. Commit and push (`git push origin feature/your-feature`)
6. Open a pull request

## Acknowledgments

- **[UC Santa Cruz OSPO](https://ucsc-ospo.github.io/)** — Open Source Program Office, host of the OSRE 2026 program
- **[NELBL Lab](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/)** — Neuroscience & Biomedical Lab, project originators
- **[MedlinePlus / NLM / NIH](https://medlineplus.gov/)** — Medical data source (public domain)
- **[Meta AI](https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct)** — Llama 3.1-8B-Instruct model
- **[ChromaDB](https://www.trychroma.com/)** — Vector database
- **[Sentence-Transformers](https://www.sbert.net/)** — all-MiniLM-L6-v2 embedding model

## License

This project is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license. See [LICENSE](LICENSE) for details.
