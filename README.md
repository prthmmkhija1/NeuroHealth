# 🧠 NeuroHealth

**AI-Powered Health Assistant** — An intelligent health chatbot that uses RAG (Retrieval-Augmented Generation) to provide safe, evidence-informed health guidance.

> ⚠️ **Disclaimer:** NeuroHealth is NOT a substitute for professional medical advice. Always consult a qualified healthcare professional for medical concerns.

---

## Features

- **Symptom Assessment** — Understands and extracts symptoms from natural language
- **Urgency Triage** — Classifies urgency (Emergency → Self-Care) using clinical principles
- **Medical Knowledge Retrieval** — RAG pipeline retrieves relevant medical information before responding
- **Safety Guardrails** — Every response is checked for dangerous advice before being shown
- **Multi-turn Conversations** — Remembers context across conversation turns
- **Appointment Recommendations** — Suggests appropriate specialists and timing

## Tech Stack

| Component      | Technology                                      |
| -------------- | ----------------------------------------------- |
| **LLM**        | Llama 3.1-8B-Instruct (local, zero API cost)    |
| **Embeddings** | all-MiniLM-L6-v2 (sentence-transformers, local) |
| **Vector DB**  | ChromaDB (persistent, local)                    |
| **Web UI**     | Streamlit                                       |
| **API**        | FastAPI                                         |
| **GPU**        | Nvidia A100 40GB (JupyterLab)                   |

## Project Structure

```
NeuroHealth/
├── src/
│   ├── llm_utils.py              ← Shared local Llama inference
│   ├── pipeline.py               ← Main pipeline (connects everything)
│   ├── data_pipeline/
│   │   ├── collector.py          ← Collects medical Q&A data
│   │   ├── cleaner.py            ← Cleans and normalizes text
│   │   └── chunker.py            ← Splits text into searchable chunks
│   ├── knowledge_base/
│   │   ├── embedder.py           ← Converts text to vector embeddings
│   │   └── vector_store.py       ← ChromaDB vector database
│   ├── rag/
│   │   ├── retriever.py          ← Finds relevant medical info
│   │   └── generator.py          ← Generates the final answer
│   └── modules/
│       ├── intent_recognizer.py  ← Classifies user intent
│       ├── symptom_extractor.py  ← Extracts structured symptoms
│       ├── urgency_assessor.py   ← Determines urgency level
│       ├── appointment_recommender.py ← Recommends specialists
│       ├── safety_guardrails.py  ← Safety checks on every response
│       ├── conversation_manager.py ← Session memory
│       └── response_formatter.py ← Formats final output
├── evaluation/
│   ├── benchmarks.py             ← Automated performance tests
│   ├── safety_tests.py           ← Adversarial safety tests
│   └── test_cases/               ← Test data
├── ui/
│   └── app.py                    ← Streamlit web interface
├── api/
│   ├── main.py                   ← FastAPI application
│   └── routes.py                 ← API endpoints
├── tests/                        ← Unit and integration tests
├── .env                          ← Environment variables (NOT in git)
├── .gitignore
├── requirements.txt
└── README.md
```

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

Create a `.env` file in the project root with:

```env
USE_LOCAL_LLM=true
MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
HUGGINGFACE_TOKEN=hf_YOUR_TOKEN_HERE
EMBEDDING_MODEL=all-MiniLM-L6-v2
VECTOR_DB_PATH=./data/vector_db
MAX_NEW_TOKENS=1024
TEMPERATURE=0.3
```

### 4. Build the Knowledge Base

Run these in order:

```bash
python src/data_pipeline/collector.py    # Collect medical data
python src/data_pipeline/cleaner.py      # Clean and normalize
python src/data_pipeline/chunker.py      # Split into chunks
python src/knowledge_base/embedder.py    # Generate embeddings
python src/knowledge_base/vector_store.py # Build vector DB
```

### 5. Run Tests

```bash
# Module tests (no GPU needed)
python tests/test_modules.py

# Data pipeline tests
python tests/test_data_pipeline.py

# RAG tests (needs vector store)
python tests/test_rag.py

# End-to-end tests (needs GPU + model)
python tests/test_pipeline.py
```

### 6. Launch the UI

```bash
streamlit run ui/app.py
# Opens at http://localhost:8501
```

### 7. Launch the API (optional)

```bash
uvicorn api.main:app --reload --port 8000
# API docs at http://localhost:8000/docs
```

## Environments

| Environment  | Machine                       | Use For                                    |
| ------------ | ----------------------------- | ------------------------------------------ |
| **HP-INT**   | HP 15s (Windows, Intel)       | Code writing, git, testing without LLM     |
| **JLAB-GPU** | JupyterLab (Nvidia A100 40GB) | Model inference, embeddings, full pipeline |

### Sync Between Environments

```bash
# On HP-INT: push code
git add -A && git commit -m "update" && git push

# On JLAB-GPU: pull and run
git pull && python src/pipeline.py
```

## Urgency Levels

| Level        | Color  | Action                  |
| ------------ | ------ | ----------------------- |
| 🔴 EMERGENCY | Red    | Call 911 immediately    |
| 🟠 URGENT    | Orange | See doctor within hours |
| 🟡 SOON      | Yellow | See doctor in 1-2 days  |
| 🟢 ROUTINE   | Green  | Schedule an appointment |
| 🔵 SELF_CARE | Blue   | Manage at home          |

## Safety

- Emergency keyword detection runs **before** the LLM (instant, reliable)
- Every LLM response passes through safety guardrails
- Emergency recall target: **100%** (never miss a life-threatening case)
- Responses never diagnose — only suggest possibilities
- Prescription medication is never specifically recommended

## License

This project is part of the OSRE 2026 program at UC Santa Cruz.
