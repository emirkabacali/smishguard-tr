# Dataset card

## Overview

SmishGuard-TR is trained and evaluated on two sources that share one schema:

| Column     | Type | Meaning                                                                 |
|------------|------|-------------------------------------------------------------------------|
| `text`     | str  | SMS text (PII masked, links defanged in the curated file)               |
| `label`    | int  | `0` = legitimate, `1` = malicious (spam **and** smishing)               |
| `category` | str  | Topic, for analysis only: `cargo`, `e_government`, `toll_fine`, `bank`, `prize`, `investment`, `telecom`, `generic_spam`, `other` |
| `source`   | str  | `turkishsms`, `curated_real` or `synthetic`                             |

The task is binary. Spam and smishing are merged into one malicious class because the data is
too small for a reliable three-class model.

## Source A — TurkishSMS

- **Reference:** Uysal, A. K., Günal, S., Ergin, S., & Sora Günal, E. (2013). *The Impact of
  Feature Extraction and Selection on SMS Spam Filtering.* Elektronika ir Elektrotechnika,
  19(5), 67–72. doi:[10.5755/j01.eee.19.5.1829](https://doi.org/10.5755/j01.eee.19.5.1829)
- **Content:** 850 messages (420 spam, 430 legitimate), collected around 2010–2011.
- **License:** academic use only. The raw files are **not** part of this repository;
  `scripts/download_data.py` downloads them from the first author's Hugging Face mirror
  ([`akuysal/turkishSMS-ds`](https://huggingface.co/datasets/akuysal/turkishSMS-ds)), pinned to
  revision `66fde603` and verified with SHA-256 checksums.
- **Mapping:** `spam` → label 1 / category `generic_spam`; `legitimate` → label 0 / category `other`.

## Source B — Curated examples

`data/curated/smishing_tr_curated.csv` (`text,label,category,source,collected_at,notes`) adds
modern Turkish smishing patterns that the 2013 dataset lacks.

- **42 synthetic smishing messages** written for this project, covering every scam category:
  fake cargo / customs fees, e-Devlet refunds, HGS/OGS fines, bank account suspension, prizes,
  investment scams, telecom refunds. They use fictional domains, URL shorteners, an IP-address
  URL and a punycode domain so that every URL rule has examples.
- **20 synthetic hard negatives:** legitimate messages that look similar on the surface
  (official cargo notices, OTP codes, bank transaction notices, appointment reminders,
  personal messages mentioning cargo or tolls). They stop the model from learning shortcuts
  such as "the word *kargo* means scam".
- All links are **defanged** (`hxxps://example[.]xyz`), and phone numbers and names are
  replaced with `<PHONE>` and `<NAME>`. Tests enforce both rules.
- `curated_real` rows (real messages, anonymized) can be contributed; see `CONTRIBUTING.md`.

## Processing pipeline (`scripts/build_dataset.py`)

1. **Clean:** Unicode NFC, refang links, collapse whitespace (casing is kept).
2. **Mask PII:** e-mails → `<EMAIL>`, TR IBANs → `<IBAN>`, checksum-valid T.C. identity
   numbers → `<TCKN>`, phone numbers (mobile, landline, 0850/444, bare 7-digit, malformed
   10–12 digit numbers starting with 0) → `<PHONE>`.
3. **Deduplicate:** the duplicate key lowercases with Turkish rules, folds Turkish letters to
   ASCII, replaces every number with `0` and drops punctuation, so template messages that
   differ only in a price or code count as one. Groups with conflicting labels are dropped.
4. **Split:** real messages are split 70 / 15 / 15 (stratified by label, `random_state=42`).
   Synthetic messages are added to **train only**.

## Resulting splits

| Split | Rows | Legitimate | Malicious | Synthetic |
|-------|-----:|-----------:|----------:|----------:|
| train |  582 |        303 |       279 |        62 |
| val   |  112 |         61 |        51 |         0 |
| test  |  112 |         61 |        51 |         0 |

912 input rows → 806 after deduplication (2 rows dropped for conflicting labels).
Exploratory analysis is in [`notebooks/01_eda.ipynb`](notebooks/01_eda.ipynb).

## Known limitations

- **Small and old:** 112 test messages means every metric has a wide confidence interval.
  The real messages are from 2010–2011.
- **Spam, not smishing:** real malicious messages are mostly commercial advertising; only
  about 12% contain an explicit link. Modern phishing patterns are covered by synthetic data
  only, and that data is never used for evaluation.
- **Shortcut features:** malicious messages are much longer than legitimate ones (median 153
  vs 43 characters), and legitimate messages are mostly informal personal chat.
- **Synthetic data reflects its author's assumptions** about current scams.
- **PII masking is regex-based:** it may over-mask (e.g. a 7-digit order number) and cannot
  detect personal names automatically.
