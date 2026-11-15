# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Data pipeline: reproducible TurkishSMS download (pinned revision + SHA-256), loaders with
  schema validation, Turkish-aware normalization, PII masking, deduplication and a
  leakage-safe stratified split (`scripts/build_dataset.py`)
- Curated dataset with 42 synthetic smishing messages and 20 hard negatives (defanged)
- Dataset card (`DATA.md`) and exploratory analysis notebook
- Baseline text model: TF-IDF char (2–5) + word (1–2) n-grams with Logistic Regression,
  Multinomial Naive Bayes for comparison, 5-fold CV, validation comparison, model persistence
  with metadata, top n-gram explanation (`scripts/train.py`)
- Explainable rule engine: offline URL extraction with `tldextract`, six URL indicators
  (brand impersonation, shortener, suspicious TLD, IP address, punycode, many hyphens/digits)
  and five Turkish text indicators (urgency, money/fine, credential request, prize, address
  issue), each producing a weighted, human-readable reason

## [0.1.0] - 2026-11-15

### Added

- Repository scaffold with `src` layout and `pyproject.toml` (setuptools)
- Ruff (lint + format) and pytest configuration, smoke test
- GitHub Actions CI on Python 3.11, 3.12 and 3.13
- README skeleton, MIT license, pull request template and decision log

[Unreleased]: https://github.com/emirkabacali/smishguard-tr/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/emirkabacali/smishguard-tr/releases/tag/v0.1.0
