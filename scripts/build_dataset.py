"""Build the processed train / val / test splits from raw TurkishSMS + curated data.

Steps: load -> clean text + mask PII -> deduplicate -> stratified split -> write CSVs.

Usage:
    python scripts/build_dataset.py
"""

from __future__ import annotations

import json
import logging
import sys

import pandas as pd

from smishguard import config
from smishguard.data.anonymize import mask_pii
from smishguard.data.loader import load_curated, load_turkishsms
from smishguard.data.normalize import clean_text
from smishguard.data.split import deduplicate, split_dataset

logger = logging.getLogger("build_dataset")


def summarize(splits: dict[str, pd.DataFrame]) -> dict[str, dict[str, int]]:
    """Count rows per split, label and source (used for logging and the dataset summary)."""
    summary: dict[str, dict[str, int]] = {}
    for name, part in splits.items():
        summary[name] = {
            "rows": len(part),
            "legitimate": int((part["label"] == config.LABEL_LEGITIMATE).sum()),
            "malicious": int((part["label"] == config.LABEL_MALICIOUS).sum()),
            **{f"source_{k}": int(v) for k, v in part["source"].value_counts().items()},
        }
    return summary


def main() -> int:
    """Entry point. Returns a process exit code."""
    try:
        turkishsms = load_turkishsms()
    except FileNotFoundError as exc:
        logger.error("%s", exc)
        return 1
    curated = load_curated()

    df = pd.concat([turkishsms, curated], ignore_index=True)
    # Processed text keeps its original casing: lowercasing happens inside the model pipeline
    # and the rule engine, so both always see the same input as at inference time.
    df["text"] = df["text"].map(clean_text).map(mask_pii)

    splits = split_dataset(deduplicate(df))

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    for name, part in splits.items():
        path = config.PROCESSED_DIR / f"{name}.csv"
        part.to_csv(path, index=False, encoding="utf-8")
        logger.info("Wrote %s (%d rows)", path.relative_to(config.PROJECT_ROOT), len(part))

    summary = summarize(splits)
    (config.PROCESSED_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    for name, counts in summary.items():
        logger.info("%-5s %s", name, counts)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    sys.exit(main())
