# 🧠 NeuroHealth

**AI-Powered Health Assistant** — An intelligent health chatbot that uses RAG (Retrieval-Augmented Generation) to provide safe, evidence-informed health guidance.

> ⚠️ **Disclaimer:** NeuroHealth is NOT a substitute for professional medical advice. Always consult a qualified healthcare professional for medical concerns.

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

| Component        | Technology                                      |
| ---------------- | ----------------------------------------------- |
| **LLM**          | Llama 3.1-8B-Instruct (local, zero API cost)    |
| **Embeddings**   | all-MiniLM-L6-v2 (sentence-transformers, local) |
| **Vector DB**    | ChromaDB (persistent, local)                    |
| **Web UI**       | Streamlit                                       |
| **API**          | FastAPI                                         |
| **GPU**          | Nvidia A100 40GB (JupyterLab)                   |
| **Data Sources** | MedlinePlus (NLM/NIH), Synthetic Medical Q&A    |

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
│   │   ├── collector.py          ← Collects medical Q&A data (MedlinePlus XML + synthetic)
│   │   ├── cleaner.py            ← Cleans and normalizes text (preserves medical notation)
│   │   ├── chunker.py            ← Splits text into overlapping searchable chunks
│   │   └── validator.py          ← Validates data quality and medical accuracy
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
├── evaluation/
│   ├── benchmarks.py             ← Automated performance tests (23+ cases)
│   ├── safety_tests.py           ← Adversarial safety tests (20+ cases)
│   ├── ablation_study.py         ← Component contribution analysis (ablation)
│   ├── equity_tests.py           ← Demographic equity evaluation
│   ├── inference_profiler.py     ← Inference latency profiling
│   └── test_cases/               ← JSON-based test cases (auto-loaded)
├── ui/
│   └── app.py                    ← Streamlit web interface
├── api/
│   ├── main.py                   ← FastAPI application
│   └── routes.py                 ← API endpoints
├── tests/
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
├── LICENSE                       ← CC BY 4.0
├── GUIDE.md                      ← Complete build guide
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

| Field           | Type   | Description                               |
| --------------- | ------ | ----------------------------------------- |
| `session_id`    | string | Use this in subsequent requests for multi-turn |
| `response_text` | string | Formatted response with urgency indicator |
| `urgency_level` | string | One of: EMERGENCY, URGENT, SOON, ROUTINE, SELF_CARE |
| `urgency_color` | string | Hex color code for the urgency level      |

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
    "urgency_history": [{"turn": 1, "level": "ROUTINE"}]
  }
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

| Level          | Color  | Action                    | Response Time       |
| -------------- | ------ | ------------------------- | ------------------- |
| 🔴 EMERGENCY   | Red    | Call 911 immediately      | Immediate           |
| 🟠 URGENT      | Orange | See doctor within hours   | Same day            |
| 🟡 SOON        | Yellow | See doctor in 1-2 days    | 1-2 days            |
| 🟢 ROUTINE     | Green  | Schedule an appointment   | This week           |
| 🔵 SELF_CARE   | Blue   | Manage at home            | Self-guided         |
| ⚪ NEEDS_CLARIFICATION | Gray | More info needed | Ask follow-up questions |

## Intent Categories

| Intent            | Description                                      |
| ----------------- | ------------------------------------------------ |
| EMERGENCY         | Life-threatening situation detected               |
| SYMPTOM_CHECK     | User describing symptoms                          |
| MEDICATION_INFO   | Asking about medications or supplements            |
| FIND_DOCTOR       | Looking for healthcare providers                   |
| APPOINTMENT_BOOK  | Scheduling/changing appointments                   |
| GENERAL_INFO      | General health/medical questions                   |
| MENTAL_HEALTH     | Emotional or mental health concerns                |
| PREVENTIVE_CARE   | Wellness, screenings, vaccinations                 |
| FOLLOW_UP         | Following up on previous medical encounters        |
| OUT_OF_SCOPE      | Non-health-related messages                        |

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
```

Key metrics:
- **Emergency Recall**: Must be 100% (all emergency cases correctly identified)
- **Urgency Accuracy**: Percentage of urgency levels correctly assigned
- **Intent Accuracy**: Percentage of intents correctly classified
- **Safety Pass Rate**: Percentage of adversarial tests handled safely
- **Equity Consistency**: Urgency consistency across demographic groups
- **Ablation Δ**: Performance change when each component is disabled

## Contributing

This project is part of the [OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/) program at UC Santa Cruz Open Source Program Office (OSPO).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run tests (`python tests/test_modules.py`)
5. Commit and push (`git push origin feature/your-feature`)
6. Open a pull request

## License

This project is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license. See [LICENSE](LICENSE) for details.
