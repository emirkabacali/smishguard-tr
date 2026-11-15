# SmishGuard-TR

[![CI](https://github.com/emirkabacali/smishguard-tr/actions/workflows/ci.yml/badge.svg)](https://github.com/emirkabacali/smishguard-tr/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/dynamic/json?url=https%3A%2F%2Fraw.githubusercontent.com%2Femirkabacali%2Fsmishguard-tr%2Fmain%2Freports%2Fcoverage.json&query=%24.percent&suffix=%25&label=coverage&color=brightgreen)](reports/coverage.json)
[![Python](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](pyproject.toml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Explainable smishing (SMS phishing) risk analysis for Turkish messages — a hybrid of a
TF-IDF + Logistic Regression text model and an interpretable rule engine.

> **Work in progress.** The project is being built in small, reviewed phases. The data
> pipeline ([DATA.md](DATA.md)), text model, rule engine, score fusion, evaluation
> ([reports/](reports/)), REST API, Docker image and demo UI exist; final documentation
> follows.

This is a research / portfolio project, not a production security product.

## Demo

![Streamlit demo analyzing a fake cargo message](docs/assets/demo.png)

```bash
pip install -e ".[demo]"
streamlit run app/streamlit_app.py
```

## Quickstart

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"            # API only: pip install -e .   scripts: add [data]

python scripts/download_data.py     # TurkishSMS (academic license, not in the repo)
python scripts/build_dataset.py     # clean, mask PII, deduplicate, split
python scripts/train.py             # train + compare models on validation
uvicorn smishguard.api.main:app --reload
```

Interactive API documentation: <http://localhost:8000/docs>

## API

`POST /v1/analyze` — analyze one message (1–1000 characters):

```bash
curl -X POST http://localhost:8000/v1/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. 24 saat icinde guncelleyin: hxxps://ptt-kargo-takip[.]xyz"}'
```

```json
{
  "risk_score": 0.7879,
  "risk_level": "high",
  "ml_probability": 0.7699,
  "rule_score": 0.95,
  "reasons": [
    {"code": "BRAND_IMPERSONATION", "weight": 0.35,
     "message": "Domain imitates a known brand (ptt) but is not an official domain."},
    {"code": "SUSPICIOUS_TLD", "weight": 0.2,
     "message": "Link uses a TLD frequently abused in scams (.xyz)."},
    {"code": "URGENCY_LANGUAGE", "weight": 0.15,
     "message": "Message pressures the reader to act quickly."},
    {"code": "ADDRESS_ISSUE", "weight": 0.15,
     "message": "Message claims a delivery or address problem."},
    {"code": "EXCESSIVE_HYPHENS_DIGITS", "weight": 0.1,
     "message": "Domain contains many hyphens or digits (ptt-kargo-takip.xyz)."}
  ],
  "model_version": "0.5.0"
}
```

`GET /health` returns `200` when the model is loaded and `503` otherwise. Invalid input
(empty, whitespace-only or longer than 1000 characters) returns `422`. Message texts are
never logged.

## Docker

The image contains only the code and pinned core dependencies (`requirements-lock.txt`);
the trained model is mounted at runtime because it is derived from academically licensed
data.

```bash
docker build -t smishguard .
docker run -p 8000:8000 -v "$(pwd)/models:/app/models:ro" smishguard
```

No dataset at hand? `python scripts/train_demo_model.py --output demo-models` trains a tiny
demo model on the test fixture (for smoke tests only; its predictions are not meaningful).
Mount `demo-models` instead of `models`.

## Development

```bash
ruff check . && ruff format --check .
pytest --cov=smishguard              # runs without the licensed dataset; CI requires >= 80%
```

## License

[MIT](LICENSE)
