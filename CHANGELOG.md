# Changelog

All notable changes to NeuroHealth will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-03-18

### Added

- **Core Pipeline**
  - Intent recognition module with 8 health-related intent categories
  - Symptom extraction using LLM-based NLP
  - 5-level urgency assessment (EMERGENCY, URGENT, SOON, ROUTINE, SELF_CARE)
  - Appointment recommendation generation
  - Response formatting with structured JSON output

- **RAG System**
  - ChromaDB vector store integration
  - Sentence-transformer embeddings (all-MiniLM-L6-v2)
  - Context-aware retrieval with relevance scoring
  - Medical knowledge base from validated sources

- **Safety Guardrails**
  - Emergency detection and escalation
  - Jailbreak/prompt injection protection
  - Crisis intervention triggers (suicide, self-harm)
  - Medical misinformation prevention
  - Out-of-scope request handling

- **Data Pipeline**
  - Multi-source medical data collection
  - Document chunking with overlap
  - Entity schema for symptoms, conditions, urgency
  - Data validation and cleaning

- **Evaluation Framework**
  - Comprehensive benchmark suite (37 test cases)
  - Safety and adversarial testing
  - Ablation study across 6 configurations
  - Equity evaluation across demographics
  - Inference profiling and latency analysis
  - Visualization generation

- **Interfaces**
  - Streamlit web UI for interactive demos
  - FastAPI REST API with OpenAPI documentation
  - Conversation history management

- **Documentation**
  - Comprehensive README with architecture diagrams
  - Contributing guidelines
  - Kaggle deployment guide
  - API documentation

### Security

- Implemented medical safety guardrails
- Added jailbreak detection
- Crisis intervention protocols
- Input sanitization

## [0.1.0] - 2026-02-01

### Added

- Initial project structure
- Basic LLM integration with Hugging Face
- Prototype symptom checker
- Initial documentation

---

## Future Roadmap

### [1.1.0] - Planned

- Multi-language support
- Voice input integration
- Enhanced pediatric/geriatric modules
- Real-time symptom tracking

### [2.0.0] - Planned

- HIPAA compliance framework
- EHR integration capabilities
- Clinical decision support extensions
- Mobile application
