# SmishGuard-TR

[![CI](https://github.com/emirkabacali/smishguard-tr/actions/workflows/ci.yml/badge.svg)](https://github.com/emirkabacali/smishguard-tr/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Explainable smishing (SMS phishing) risk analysis for Turkish messages — a hybrid of a
TF-IDF + Logistic Regression text model and an interpretable rule engine.

> **Work in progress.** The project is being built in small, reviewed phases. So far the
> repository scaffold and the data pipeline exist (see [DATA.md](DATA.md)); the model, rule
> engine, API and demo are not implemented yet.

## Planned

- Risk score (0–1), risk level (low / medium / high) and human-readable reasons per message
- URL analysis without ever visiting the link: shorteners, suspicious TLDs, brand impersonation
- REST API (FastAPI) and a small Streamlit demo

This is a research / portfolio project, not a production security product.

## Development

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest
```

## License

[MIT](LICENSE)
