# Contributing to NeuroHealth

Thank you for your interest in contributing to NeuroHealth! This project is part of the [OSRE 2026](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/) program at the UC Santa Cruz Open Source Program Office.

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/NeuroHealth.git
   cd NeuroHealth
   ```
3. **Set up** your development environment:
   ```bash
   conda create -n neurohealth python=3.11 -y
   conda activate neurohealth
   pip install -r requirements.txt
   ```
4. **Create a branch** for your work:
   ```bash
   git checkout -b feature/your-feature-name
   ```

## Development Workflow

### Code Style

- Follow **PEP 8** for Python code
- Use type hints where practical
- Write docstrings for all public functions and classes
- Keep functions focused and reasonably sized

### Testing

Before submitting a pull request, run the relevant tests:

```bash
# Unit tests (no GPU required)
pytest tests/test_modules.py
pytest tests/test_data_pipeline.py

# RAG tests (requires vector store built)
pytest tests/test_rag.py

# Full pipeline tests (requires GPU + model)
pytest tests/test_pipeline.py
```

When adding new features:

- Add corresponding unit tests
- Ensure existing tests still pass
- For safety-critical changes, add cases to `evaluation/safety_tests.py`

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add pediatric symptom patterns to urgency assessor
fix: correct emergency keyword matching for chest pain variants
docs: update API reference with new session endpoint
test: add equity test cases for elderly demographics
```

### Pull Request Process

1. Ensure all tests pass locally
2. Update documentation if your change affects user-facing behavior
3. Add a clear description of what your PR does and why
4. Reference any related issues

## Project Structure

- `src/` — Core pipeline and modules
- `evaluation/` — Benchmarks, safety tests, and evaluation tools
- `tests/` — Unit and integration tests
- `api/` — FastAPI endpoints
- `ui/` — Streamlit web interface
- `data/` — Runtime data (git-ignored)

## Safety Guidelines

NeuroHealth deals with health information. When contributing:

- **Never** add code that provides definitive medical diagnoses
- **Never** recommend specific prescription medications with dosages
- **Always** maintain the emergency detection pathway (100% recall target)
- **Always** include medical disclaimers in health-related responses
- **Test** safety guardrails after any change to response generation
- **Report** any safety concerns immediately via GitHub Issues

## Areas for Contribution

- Expanding the medical knowledge base with additional data sources
- Improving intent recognition accuracy
- Adding support for additional languages
- Enhancing the evaluation framework
- Improving documentation and tutorials
- Accessibility improvements for the web UI
- Performance optimization for inference latency

## License

By contributing to NeuroHealth, you agree that your contributions will be licensed under the [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) license.

## Questions?

Open a GitHub Issue or reach out through the [OSRE 2026 project page](https://ucsc-ospo.github.io/project/osre26/nelbl/neurohealth/).
