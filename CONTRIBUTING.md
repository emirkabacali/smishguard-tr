# Contributing

Thanks for your interest! This is a research / portfolio project, so contributions that make
it more accurate, more honest or easier to understand are especially welcome.

## Development setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check .
pytest --cov=smishguard
```

Tests do not need the licensed dataset: they use `tests/fixtures/sms_fixture.csv`.

## Workflow

1. Create a branch: `feat/<short-description>`, `fix/...`, `docs/...`.
2. Make small commits with [Conventional Commits](https://www.conventionalcommits.org/):
   `feat(features): add ...`, `fix(api): ...`, `docs: ...`, `test: ...`, `data: ...`.
3. Keep `ruff` and `pytest` green; coverage must stay at or above 80%.
4. Open a pull request using the template (Summary, Changes, How to test, Checklist).
5. Record non-obvious technical decisions in `docs/DECISIONS.md` and user-visible changes in
   `CHANGELOG.md` under `[Unreleased]`.

## Adding curated messages

`data/curated/smishing_tr_curated.csv` has the columns
`text,label,category,source,collected_at,notes`.

- **Real messages** (`source=curated_real`): only messages you received yourself or that a
  bank / institution published as a public warning. Never add messages from other people's
  phones without consent.
- **Anonymize everything:** replace phone numbers with `<PHONE>`, IBANs with `<IBAN>`,
  identity numbers with `<TCKN>`, personal names with `<NAME>`.
- **Defang every link:** `https://scam.xyz/a` → `hxxps://scam[.]xyz/a`
  (`smishguard.data.normalize.defang` does this).
- `label`: `1` for spam / smishing, `0` for legitimate. `category`: one of `cargo`,
  `e_government`, `toll_fine`, `bank`, `prize`, `investment`, `telecom`, `generic_spam`, `other`.
- `collected_at`: `YYYY-MM-DD`; `notes`: one short phrase describing the pattern.
- Synthetic examples must use `source=synthetic`; they are only ever used for training.

`tests/data/test_loader.py` checks the schema, defanging and PII masking of this file.

## Evaluation rules

- Tune anything (thresholds, weights, keywords) on the **validation** split only.
- `python scripts/evaluate.py --no-test` shows validation results without touching the test set.
- Every number in the README must come from a file in `reports/`;
  `tests/test_readme.py` checks the results table against `reports/metrics_test.json`.

## Dependencies and the Docker lock file

Core (API) dependencies live in `[project.dependencies]`; scripts need the `data` extra.
After changing core dependencies, regenerate `requirements-lock.txt` inside the image's base:

```bash
docker run --rm -v "$(pwd):/src:ro" python:3.13-slim sh -c \
  "cp -r /src/pyproject.toml /src/README.md /src/LICENSE /src/src /tmp/ && cd /tmp && \
   pip install -q . && pip freeze --exclude smishguard-tr"
```

Paste the output below the two comment lines of `requirements-lock.txt`, and retrain the
model with the same scikit-learn version so that the pickled model loads in the container.
