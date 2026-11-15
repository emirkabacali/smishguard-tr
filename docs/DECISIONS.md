# Decision Log

Lightweight records of technical decisions: what was decided, which alternatives were
considered and why. Newest entries at the bottom.

---

## D-001: Supported Python versions

- **Date:** 2026-11-15
- **Decision:** Support Python 3.11+ (`requires-python = ">=3.11"`). CI runs on 3.11, 3.12
  and 3.13; local development uses 3.13.
- **Alternatives:** Pin to 3.11/3.12 only (as originally planned); also test 3.14.
- **Rationale:** 3.11 is the oldest version with the typing and performance features we rely
  on. The development machine has 3.13, so it is added to the CI matrix to keep "works on my
  machine" and "works in CI" identical. 3.14 is left out until all scientific dependencies
  ship stable wheels for it.

## D-002: Build backend and project layout

- **Date:** 2026-11-15
- **Decision:** `src/` layout with setuptools as the build backend, configured entirely in
  `pyproject.toml`. Runtime dependencies are added only in the phase that first needs them.
- **Alternatives:** Flat layout; Poetry / Hatch / uv as project managers.
- **Rationale:** The `src/` layout forces tests to import the *installed* package, which
  catches packaging mistakes early. setuptools + `pip install -e` is the most widely known
  toolchain and needs no extra tool on a fresh machine.

## D-003: TurkishSMS download source

- **Date:** 2026-11-15
- **Decision:** Download from the first author's Hugging Face mirror (`akuysal/turkishSMS-ds`)
  pinned to a commit SHA with SHA-256 verification; fall back to the latest revision (checksum
  mismatch only logged). The original university pages are listed for manual download.
- **Alternatives:** Scraping the original `ceng.eskisehir.edu.tr` / `ceng.anadolu.edu.tr`
  pages first; committing the data.
- **Rationale:** At implementation time the first university page returned HTTP 500 and the
  second domain no longer resolved, and neither offers a direct file link. Pinning the
  revision makes every download byte-identical. Committing the data is not allowed by its
  academic-only license.

## D-004: Aggressive duplicate key

- **Date:** 2026-11-15
- **Decision:** Duplicates are detected on a key that masks PII, lowercases with Turkish
  rules, folds to ASCII, maps every number to `0` and drops punctuation. Groups with
  conflicting labels are removed.
- **Alternatives:** Exact string match; fuzzy (edit-distance / MinHash) matching.
- **Rationale:** Spam campaigns resend the same template with a different price or code. An
  exact match would let near-copies land in both train and test (data leakage) and inflate
  metrics. Fuzzy matching would be more thorough but adds complexity and a threshold to tune
  for an 850-message dataset.

## D-005: Synthetic data is train-only

- **Date:** 2026-11-15
- **Decision:** `source=synthetic` rows are always added to the training split; validation
  and test consist of real messages only.
- **Alternatives:** Split synthetic rows like real ones.
- **Rationale:** Synthetic messages were written by us and share our phrasing and patterns.
  Evaluating on them would measure how well the model learned our writing style, not how it
  performs on real messages. The price is that the test set barely contains modern smishing;
  this is reported as a limitation instead of being hidden.

## D-006: Prefer over-masking PII

- **Date:** 2026-11-15
- **Decision:** Phone masking also covers bare 7-digit numbers and 10–12 digit runs starting
  with `0`; T.C. identity numbers are masked only when their checksum is valid.
- **Alternatives:** Mask only well-formed mobile numbers.
- **Rationale:** The raw data contains real (if old) phone numbers in irregular formats.
  Masking an occasional order number costs almost nothing, while leaking a personal number is
  a privacy violation. The checksum keeps random 11-digit numbers readable.

## D-007: Character n-grams + word n-grams for Turkish

- **Date:** 2026-11-15
- **Decision:** The text model concatenates TF-IDF over `char_wb` 2–5-grams and word 1–2-grams
  (`sublinear_tf=True`). Before vectorizing, text is PII-masked, lowercased with Turkish rules
  and folded to ASCII.
- **Alternatives:** Word n-grams only; stemming with a Turkish morphological analyzer (e.g.
  Zemberek); transformer embeddings (BERTurk).
- **Rationale:** Turkish is agglutinative: *kargo, kargonuz, kargonuzu, kargoya* are four
  different words but share character n-grams. Character n-grams capture stems and suffixes
  without a stemmer, and they tolerate typos, abbreviations (*slm, cnm*) and missing Turkish
  letters, all common in SMS. Word n-grams add whole-phrase signals (*hemen arayin*). ASCII
  folding merges *ödeme* and *odeme*, which matters with only ~600 training messages. A
  stemmer adds a Java dependency, and BERTurk is kept as an optional experiment (Phase 9).

## D-008: Model selection and cross-validation policy

- **Date:** 2026-11-15
- **Decision:** Candidates are ordered by preference (Logistic Regression, then Multinomial
  Naive Bayes). A less preferred model is selected only if its validation F1 is higher by more
  than 0.01. Cross-validation folds evaluate real messages only; synthetic rows are added to
  every fit fold.
- **Alternatives:** Plain "highest validation F1 wins"; standard k-fold over all training rows.
- **Rationale:** On the first run NB scored F1 0.9615 versus 0.9608 for LogReg on 112
  validation messages, a difference smaller than one message. LogReg had higher CV F1, lower
  false positive rate and higher ROC AUC, and it provides two things the rest of the system
  needs: interpretable coefficients and better-calibrated probabilities for score fusion
  (NB probabilities are typically pushed towards 0 or 1). Evaluating CV folds on real messages
  only keeps the D-005 policy consistent inside cross-validation.
