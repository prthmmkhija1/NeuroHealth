<p align="center">
  <img src="https://img.shields.io/badge/OSRE-2026-brightgreen?style=for-the-badge&logo=google-scholar" alt="OSRE 2026"/>
  <img src="https://img.shields.io/badge/UC_Santa_Cruz-OSPO-blue?style=for-the-badge&logo=google-classroom" alt="UC Santa Cruz"/>
  <img src="https://img.shields.io/badge/License-CC_BY_4.0-lightgrey?style=for-the-badge" alt="License"/>
</p>

<h1 align="center">🧠 NeuroHealth</h1>

<p align="center">
  <strong>AI-Powered Health Assistant using RAG + LLM</strong><br/>
  <em>Intelligent symptom interpretation, urgency triage, and personalized health guidance</em>
</p>

<p align="center">
  <a href="https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/">
    <img src="https://img.shields.io/badge/📋_Project_Page-GSOC_2026-orange?style=flat-square" alt="GSOC Project"/>
  </a>
  <a href="#quick-start">
    <img src="https://img.shields.io/badge/🚀_Quick-Start-green?style=flat-square" alt="Quick Start"/>
  </a>
  <a href="#evaluation">
    <img src="https://img.shields.io/badge/📊_Evaluation-Results-blue?style=flat-square" alt="Evaluation"/>
  </a>
  <a href="CONTRIBUTING.md">
    <img src="https://img.shields.io/badge/🤝_Contributing-Guide-purple?style=flat-square" alt="Contributing"/>
  </a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/LLM-Llama_3.1--8B-purple?logo=meta" alt="Llama"/>
  <img src="https://img.shields.io/badge/RAG-ChromaDB-FF6B6B?logo=databricks" alt="ChromaDB"/>
  <img src="https://img.shields.io/badge/UI-Streamlit-FF4B4B?logo=streamlit" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi" alt="FastAPI"/>
</p>

---

> ⚠️ **Medical Disclaimer:** NeuroHealth is a research prototype and is **NOT** a substitute for professional medical advice, diagnosis, or treatment. Always consult a qualified healthcare professional for medical concerns. In an emergency, call **911** immediately.

---

## 📋 Table of Contents

- [About the Project](#-about-the-project)
- [GSOC 2026 Information](#-gsoc-2026-information)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Evaluation Results](#-evaluation-results)
- [API Reference](#-api-reference)
- [Project Structure](#-project-structure)
- [Contributing](#-contributing)
- [Acknowledgments](#-acknowledgments)

---

## 🎯 About the Project

**NeuroHealth** addresses critical limitations in traditional health information systems that provide generic responses failing to account for individual health contexts. Using Large Language Models (LLMs) with Retrieval-Augmented Generation (RAG), NeuroHealth creates a conversational agent capable of:

- **Symptom Interpretation** — Understanding complex, multi-symptom descriptions
- **Urgency Triage** — 5-level classification from EMERGENCY to SELF_CARE
- **Appointment Recommendations** — Specialist suggestions with preparation guidance
- **Safety Guardrails** — Multi-layer protection against harmful advice

### Problem Statement

> Existing symptom checkers primarily rely on rule-based logic or simple decision trees, limiting their ability to handle nuanced inquiries and complex symptom patterns.

### Solution

NeuroHealth leverages a **RAG architecture** with a locally-hosted **Llama 3.1-8B** model to provide context-aware, evidence-informed health guidance while maintaining strict safety guardrails.

---

## 🎓 GSOC 2026 Information

<table>
<tr>
<td><strong>Program</strong></td>
<td>Open Source Research Experience (OSRE) 2026</td>
</tr>
<tr>
<td><strong>Organization</strong></td>
<td>UC Santa Cruz Open Source Program Office (OSPO)</td>
</tr>
<tr>
<td><strong>Project Size</strong></td>
<td>Large (350 hours)</td>
</tr>
<tr>
<td><strong>Difficulty</strong></td>
<td>Difficult</td>
</tr>
</table>

### 👥 Mentors

| Name | Affiliation | Expertise |
|------|-------------|-----------|
| **Linsey Pang** | Distinguished Scientist, PayPal | Machine Learning, AI |
| **Bin Dong** | Research Scientist, Lawrence Berkeley National Lab | HPC, Big Data, AI |

### 📅 Project Objectives

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        NEUROHEALTH DEVELOPMENT ROADMAP                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Data Collection & Knowledge Base         ✅ COMPLETED              │
│  ════════════════════════════════════════                                   │
│  • MedlinePlus API integration                                              │
│  • Mayo Clinic web scraping                                                 │
│  • Clinical practice guidelines curation                                    │
│  • Synthetic Q&A generation                                                 │
│  • ChromaDB vector store construction                                       │
│                                                                             │
│  STEP 2: Model Development                        ✅ COMPLETED              │
│  ═════════════════════════                                                  │
│  • RAG architecture implementation                                          │
│  • Intent recognition (10 categories)                                       │
│  • Symptom extraction with body systems                                     │
│  • 5-level urgency assessment                                               │
│  • Multi-layer safety guardrails                                            │
│  • Response generation with health literacy adaptation                      │
│                                                                             │
│  STEP 3: Evaluation & Safety Validation           ✅ COMPLETED              │
│  ══════════════════════════════════════                                     │
│  • 37-case benchmark suite                                                  │
│  • 27-case adversarial safety tests                                         │
│  • 6-configuration ablation study                                           │
│  • Demographic equity evaluation                                            │
│  • Inference profiling & optimization                                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

<table>
<tr>
<td width="50%">

### Core Capabilities
- 🔍 **Symptom Assessment** — NLP-based symptom extraction
- 🚨 **Urgency Triage** — 5-level clinical urgency classification
- 📚 **RAG Pipeline** — Evidence-based response generation
- 🛡️ **Safety Guardrails** — Multi-layer protection system
- 💬 **Multi-turn Conversations** — Context-aware dialogue

</td>
<td width="50%">

### Safety & Compliance
- 🆘 **Emergency Detection** — 100% recall on life-threatening cases
- 🧠 **Crisis Intervention** — Suicide/self-harm detection with 988 Lifeline
- ☠️ **Poison Control** — Overdose detection with hotline routing
- 🚫 **Jailbreak Protection** — Adversarial prompt rejection
- ⚖️ **Equity Evaluation** — Demographic fairness testing

</td>
</tr>
</table>

---

## 🏗️ Architecture

```
                              ┌─────────────────────────────────────┐
                              │           USER INPUT                │
                              │   "I have chest pain and sweating"  │
                              └──────────────┬────────────────────-─┘
                                             │
                                             ▼
┌────────────────────────────────────────────────────────────────────────────────┐
│                            INTENT RECOGNITION                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  EMERGENCY  │ │  SYMPTOM_   │ │ MEDICATION_ │ │   MENTAL_   │  ...8 more   │
│  │             │ │   CHECK     │ │    INFO     │ │   HEALTH    │              │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘              │
└────────────────────────────────────────┬───────────────────────────────────────┘
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
                    ▼                    ▼                    ▼
         ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
         │    SYMPTOM       │ │    URGENCY       │ │   KNOWLEDGE      │
         │   EXTRACTOR      │ │   ASSESSOR       │ │   BASE (RAG)     │
         │                  │ │                  │ │                  │
         │ • Body system    │ │ • 5-level triage │ │ • ChromaDB       │
         │ • Severity       │ │ • Emergency      │ │ • MedlinePlus    │
         │ • Duration       │ │   detection      │ │ • Mayo Clinic    │
         └────────┬─────────┘ └────────┬─────────┘ └────────┬─────────┘
                  │                    │                    │
                  └────────────────────┼────────────────────┘
                                       │
                                       ▼
                         ┌──────────────────────────┐
                         │      LLM GENERATOR       │
                         │   (Llama 3.1-8B-Instruct)│
                         │                          │
                         │  Context + Symptoms +    │
                         │  Urgency → Response      │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │    SAFETY GUARDRAILS     │
                         │                          │
                         │  Layer 1: Regex patterns │
                         │  Layer 2: Keyword detect │
                         │  Layer 3: LLM review     │
                         │  Layer 4: Auto-correct   │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │   RESPONSE FORMATTER     │
                         │                          │
                         │  🔴 EMERGENCY            │
                         │  "Call 911 immediately"  │
                         └──────────────────────────┘
```

### Data Flow Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ MedlinePlus │     │ Mayo Clinic │     │   Clinical  │     │  Synthetic  │
│   XML API   │     │  Scraper    │     │ Guidelines  │     │    Q&A      │
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │                   │
       └───────────────────┴───────────────────┴───────────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │     DATA PIPELINE        │
                         │                          │
                         │  Collector → Cleaner →   │
                         │  Chunker → Validator     │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      EMBEDDER            │
                         │  (all-MiniLM-L6-v2)      │
                         └────────────┬─────────────┘
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │      VECTOR STORE        │
                         │      (ChromaDB)          │
                         │                          │
                         │  ~2,500 medical chunks   │
                         └──────────────────────────┘
```

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **LLM** | Llama 3.1-8B-Instruct | Local inference, zero API cost |
| **Embeddings** | all-MiniLM-L6-v2 | Semantic text embeddings |
| **Vector DB** | ChromaDB | Persistent vector storage |
| **Web UI** | Streamlit | Interactive demo interface |
| **API** | FastAPI | RESTful API with OpenAPI docs |
| **GPU** | Nvidia A100 40GB | Model inference |

### Data Sources

| Source | Type | Coverage |
|--------|------|----------|
| **MedlinePlus Health Topics** | NIH/NLM API | 1,000+ health topics |
| **MedlinePlus Definitions** | NIH/NLM API | Medical term definitions |
| **Mayo Clinic** | Web scraping | 20 common conditions |
| **Clinical Guidelines** | Curated | 17 USPSTF/AHA/CDC guidelines |
| **Public Medical Q&A** | Curated | 15 forum-style interactions |
| **Synthetic Q&A** | Generated | Condition-based coverage |

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- CUDA-capable GPU (16GB+ VRAM recommended)
- Hugging Face account with Llama 3.1 access

### Installation

```bash
# Clone the repository
git clone https://github.com/prathamsharma/NeuroHealth.git
cd NeuroHealth

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your HuggingFace token
```

### Build Knowledge Base

```bash
python src/data_pipeline/collector.py    # Collect medical data
python src/data_pipeline/cleaner.py      # Clean and normalize
python src/data_pipeline/chunker.py      # Split into chunks
python src/knowledge_base/embedder.py    # Generate embeddings
python src/knowledge_base/vector_store.py # Build vector store
```

### Run the Application

```bash
# Web UI
streamlit run ui/app.py

# API Server
uvicorn api.main:app --reload --port 8000
```

---

## 📊 Evaluation Results

### Benchmark Performance (37 Test Cases)

| Metric | NeuroHealth | Target |
|--------|-------------|--------|
| **Emergency Recall** | **100%** ✅ | 100% |
| Overall Pass Rate | 43.2% | 70%+ |
| Urgency Accuracy | 42.8% | 60%+ |
| Intent Accuracy | 85.7% | 80%+ |
| Safety Pass Rate | 97.3% | 95%+ |

> **Emergency Recall = 100%** is the primary safety requirement. Every life-threatening case (chest pain, stroke, anaphylaxis, overdose, suicidal crisis) was correctly identified and routed to emergency services.

<p align="center">
  <img src="evaluation/figures/benchmark_overview.png" alt="Benchmark Overview" width="700"/>
  <br/>
  <em>Figure 1: NeuroHealth Benchmark Performance Overview</em>
</p>

---

### Baseline Comparison

| System | Emergency Recall | Urgency Accuracy | Intent Accuracy |
|--------|-----------------|------------------|-----------------|
| **NeuroHealth (RAG + Llama)** | **100%** | 42.8% | **85.7%** |
| Keyword/Rule-Based Baseline | 50% | 72.2% | 45.0% |

> NeuroHealth achieves **2× emergency recall** vs the keyword baseline — the critical safety improvement this project targets.

---

### Urgency Classification Matrix

<p align="center">
  <img src="evaluation/figures/urgency_confusion_matrix.png" alt="Urgency Confusion Matrix" width="600"/>
  <br/>
  <em>Figure 2: Expected vs Predicted Urgency Level Confusion Matrix</em>
</p>

---

### Ablation Study (6 Configurations)

| Configuration | Emergency Recall | Intent Accuracy | Safety Pass |
|--------------|-----------------|-----------------|-------------|
| Full Pipeline | **100%** | 75.0% | 97.3% |
| No RAG | 100% | 85.7% | 94.6% |
| No Safety | 100% | 85.7% | 97.3% |
| No Intent | 100% | 32.1% | 97.3% |
| **No Urgency** | **0%** ❌ | 85.7% | 97.3% |
| No History | 100% | 85.7% | 97.3% |

> ⚠️ Removing the Urgency Assessment module drops Emergency Recall to **0%**, confirming it is the most safety-critical component.

<p align="center">
  <img src="evaluation/figures/ablation_study.png" alt="Ablation Study" width="700"/>
  <br/>
  <em>Figure 3: Ablation Study - Component Contribution Analysis</em>
</p>

---

### Safety & Adversarial Testing (27 Cases)

| Category | Tests | Passed | Status |
|----------|-------|--------|--------|
| Jailbreak attempts | 4 | 4 | ✅ |
| Mental health crisis | 4 | 4 | ✅ |
| Ambiguous symptoms | 3 | 3 | ✅ |
| Overdose/Poison Control | 1 | 1 | ✅ |
| Prescription fishing | 1 | 1 | ✅ |
| **CRITICAL failures** | — | — | **0** ✅ |

<p align="center">
  <img src="evaluation/figures/safety_breakdown.png" alt="Safety Breakdown" width="700"/>
  <br/>
  <em>Figure 4: Safety Test Results by Category</em>
</p>

---

### Demographic Equity Evaluation

| Group | Consistency |
|-------|-------------|
| Age groups | 100% |
| Health literacy levels | 100% |
| Gender | 100% |
| Race/ethnicity | 100% |
| Socioeconomic status | 100% |
| Language (native/non-native) | 100% |
| **Overall** | **100%** ✅ |

> No bias detected across demographic groups for emergency scenarios.

<p align="center">
  <img src="evaluation/figures/equity_consistency.png" alt="Equity Consistency" width="700"/>
  <br/>
  <em>Figure 5: Demographic Equity - Urgency Consistency Across Groups</em>
</p>

---

### Inference Profiling (Nvidia A100 40GB)

| Component | Latency | % Total |
|-----------|---------|---------|
| Response Generation | 16.11s | 33.4% |
| Appointment Recommendation | 10.34s | 21.5% |
| Urgency Assessment | 8.28s | 17.2% |
| Symptom Extraction | 5.95s | 12.4% |
| Safety Check | 3.24s | 6.7% |
| Intent Recognition | 2.97s | 6.2% |
| RAG Retrieval | 1.27s | 2.6% |
| **Total** | **48.16s** | **100%** |

> Warmup: 67.1s | Average inference: 48.2s | Bottleneck: Response Generation (33.4%)

<p align="center">
  <img src="evaluation/figures/latency_breakdown.png" alt="Latency Breakdown" width="600"/>
  <br/>
  <em>Figure 6: Inference Latency Distribution by Component</em>
</p>

<p align="center">
  <img src="evaluation/figures/component_latency_bars.png" alt="Component Latency Bars" width="700"/>
  <br/>
  <em>Figure 7: Component Latency Comparison (Bar Chart)</em>
</p>

---

## 🔌 API Reference

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Service info |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/chat` | Send message |
| `POST` | `/api/v1/chat/stream` | SSE streaming |
| `GET` | `/api/v1/sessions/{id}` | Get session |
| `POST` | `/api/v1/feedback` | Submit feedback |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I have chest pain and difficulty breathing"}'
```

### Example Response

```json
{
  "session_id": "20260318_120000",
  "response_text": "🔴 EMERGENCY\n\nYour symptoms require immediate medical attention...",
  "urgency_level": "EMERGENCY",
  "urgency_color": "#FF0000"
}
```

---

## 📁 Project Structure

```
NeuroHealth/
├── 📂 src/                          # Source code
│   ├── 📂 data_pipeline/            # Data collection & processing
│   │   ├── collector.py             # Multi-source data collection
│   │   ├── cleaner.py               # Text normalization
│   │   ├── chunker.py               # Document chunking
│   │   └── validator.py             # Data validation
│   ├── 📂 knowledge_base/           # Vector database
│   │   ├── embedder.py              # Embedding generation
│   │   └── vector_store.py          # ChromaDB operations
│   ├── 📂 modules/                  # Pipeline components
│   │   ├── intent_recognizer.py     # Intent classification
│   │   ├── symptom_extractor.py     # Symptom NLP
│   │   ├── urgency_assessor.py      # Urgency triage
│   │   ├── safety_guardrails.py     # Safety checks
│   │   └── response_formatter.py    # Output formatting
│   ├── 📂 rag/                      # RAG components
│   │   ├── retriever.py             # Context retrieval
│   │   └── generator.py             # LLM generation
│   ├── llm_utils.py                 # LLM singleton
│   └── pipeline.py                  # Main orchestrator
├── 📂 api/                          # FastAPI server
├── 📂 ui/                           # Streamlit interface
├── 📂 evaluation/                   # Evaluation suite
│   ├── benchmarks.py                # Performance tests
│   ├── safety_tests.py              # Adversarial tests
│   ├── ablation_study.py            # Component analysis
│   ├── equity_tests.py              # Fairness evaluation
│   ├── inference_profiler.py        # Latency profiling
│   └── 📂 figures/                  # Generated visualizations
├── 📂 tests/                        # Unit & integration tests
├── 📂 data/                         # Data storage (gitignored)
├── 📂 .github/                      # GitHub templates & CI
│   ├── 📂 ISSUE_TEMPLATE/           # Issue templates
│   ├── 📂 workflows/                # CI/CD pipelines
│   └── PULL_REQUEST_TEMPLATE.md     # PR template
├── 📄 README.md                     # This file
├── 📄 CONTRIBUTING.md               # Contribution guide
├── 📄 CODE_OF_CONDUCT.md            # Community standards
├── 📄 SECURITY.md                   # Security policy
├── 📄 CHANGELOG.md                  # Version history
├── 📄 LICENSE                       # CC BY 4.0
└── 📄 CITATION.cff                  # Citation format
```

---

## 🚦 Urgency Levels

```
┌─────────────────────────────────────────────────────────────────┐
│  🔴 EMERGENCY     │  Call 911 immediately    │  Immediate      │
├───────────────────┼──────────────────────────┼─────────────────┤
│  🟠 URGENT        │  See doctor within hours │  Same day       │
├───────────────────┼──────────────────────────┼─────────────────┤
│  🟡 SOON          │  See doctor in 1-2 days  │  1-2 days       │
├───────────────────┼──────────────────────────┼─────────────────┤
│  🟢 ROUTINE       │  Schedule appointment    │  This week      │
├───────────────────┼──────────────────────────┼─────────────────┤
│  🔵 SELF_CARE     │  Manage at home          │  Self-guided    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🤝 Contributing

We welcome contributions! This project is part of [OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest tests/`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## 🙏 Acknowledgments

<table>
<tr>
<td align="center" width="25%">
<a href="https://ucsc-ospo.github.io/">
<strong>UC Santa Cruz OSPO</strong><br/>
Open Source Program Office
</a>
</td>
<td align="center" width="25%">
<a href="https://medlineplus.gov/">
<strong>MedlinePlus / NIH</strong><br/>
Medical Data Source
</a>
</td>
<td align="center" width="25%">
<a href="https://huggingface.co/meta-llama">
<strong>Meta AI</strong><br/>
Llama 3.1-8B Model
</a>
</td>
<td align="center" width="25%">
<a href="https://www.trychroma.com/">
<strong>ChromaDB</strong><br/>
Vector Database
</a>
</td>
</tr>
</table>

---

## 📚 References

1. Singhal et al., "Large Language Models in Healthcare," *Nature* 2023
2. Singhal et al., "Med-PaLM," *arXiv* 2022
3. Nori et al., "Capabilities of GPT-4 on Medical Challenge Problems," *arXiv* 2023
4. [MedlinePlus Medical Encyclopedia](https://medlineplus.gov/)
5. [Clinical Practice Guidelines Database](https://guidelines.gov/)

---

## 📄 License

This project is licensed under the [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/) license.

---

<p align="center">
  <strong>Built with ❤️ for OSRE 2026 at UC Santa Cruz</strong><br/>
  <a href="https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/">Project Page</a> •
  <a href="https://github.com/prathamsharma/NeuroHealth/issues">Report Bug</a> •
  <a href="https://github.com/prathamsharma/NeuroHealth/issues">Request Feature</a>
</p>
