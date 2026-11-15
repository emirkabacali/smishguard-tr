"""Load the TurkishSMS dataset and the curated CSV into one common schema.

Common schema: ``text`` (str), ``label`` (0 = legitimate, 1 = malicious),
``category`` (see :data:`smishguard.config.CATEGORIES`) and ``source``.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from smishguard import config

logger = logging.getLogger(__name__)

CURATED_COLUMNS = ("text", "label", "category", "source", "collected_at", "notes")


def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Check that ``df`` follows the common schema and return only the schema columns.

    Raises:
        ValueError: If a column is missing or a value is outside the allowed set.
    """
    missing = set(config.SCHEMA_COLUMNS) - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    out = df.loc[:, list(config.SCHEMA_COLUMNS)].copy()
    out["text"] = out["text"].astype(str)
    out["label"] = out["label"].astype(int)

    checks = {
        "label": config.LABELS,
        "category": config.CATEGORIES,
        "source": config.SOURCES,
    }
    for column, allowed in checks.items():
        invalid = sorted(set(out[column]) - set(allowed))
        if invalid:
            raise ValueError(f"Invalid values in '{column}': {invalid}")
    if (out["text"].str.strip() == "").any():
        raise ValueError("Empty text values found")
    return out.reset_index(drop=True)


def load_turkishsms(raw_dir: Path = config.RAW_DIR) -> pd.DataFrame:
    """Load the TurkishSMS parquet files and map them to the common schema.

    The published train/validation files are merged: this project makes its own
    deduplicated, stratified split.

    Raises:
        FileNotFoundError: If the raw files have not been downloaded yet.
    """
    frames = []
    for filename in config.TURKISHSMS_FILES:
        path = raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(
                f"{path} not found. Run `python scripts/download_data.py` first."
            )
        frames.append(pd.read_parquet(path, columns=["text", "label"]))

    df = pd.concat(frames, ignore_index=True)
    unknown = sorted(set(df["label"]) - set(config.TURKISHSMS_LABEL_MAP))
    if unknown:
        raise ValueError(f"Unexpected TurkishSMS labels: {unknown}")

    df["label"] = df["label"].map(config.TURKISHSMS_LABEL_MAP)
    # TurkishSMS has no topic annotation; spam is mostly commercial advertising.
    df["category"] = df["label"].map(
        {config.LABEL_LEGITIMATE: "other", config.LABEL_MALICIOUS: "generic_spam"}
    )
    df["source"] = config.SOURCE_TURKISHSMS
    logger.info("Loaded %d TurkishSMS messages", len(df))
    return validate_schema(df)


def load_curated(path: Path = config.CURATED_CSV) -> pd.DataFrame:
    """Load the curated CSV (synthetic + manually collected examples).

    Raises:
        ValueError: If the CSV header does not match :data:`CURATED_COLUMNS`.
    """
    df = pd.read_csv(
        path, dtype={"text": str, "category": str, "source": str}, keep_default_na=False
    )
    if tuple(df.columns) != CURATED_COLUMNS:
        raise ValueError(f"Curated CSV columns must be {CURATED_COLUMNS}, got {tuple(df.columns)}")
    logger.info("Loaded %d curated messages from %s", len(df), path.name)
    return validate_schema(df)
