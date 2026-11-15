"""Deduplication and leakage-safe train / validation / test splitting.

Rules:
1. Near-identical messages are removed *before* splitting, so the same message can never be
   in both train and test.
2. Synthetic messages go to the training set only; validation and test contain real
   messages exclusively, so reported metrics are not inflated by our own examples.
3. The split of real messages is stratified by label with a fixed seed.
"""

from __future__ import annotations

import logging
import re

import pandas as pd
from sklearn.model_selection import train_test_split

from smishguard import config
from smishguard.data.anonymize import mask_pii
from smishguard.data.normalize import ascii_fold, normalize_for_matching

logger = logging.getLogger(__name__)

_DIGITS_RE = re.compile(r"\d+")
_NON_WORD_RE = re.compile(r"[^\w<>]+")

# When the same message appears in several sources, keep the most trustworthy copy.
_SOURCE_PRIORITY = {
    config.SOURCE_TURKISHSMS: 0,
    config.SOURCE_CURATED_REAL: 1,
    config.SOURCE_SYNTHETIC: 2,
}


def dedup_key(text: str) -> str:
    """Build the key used to detect duplicates.

    Masks PII, lowercases (Turkish rules), folds Turkish letters to ASCII, replaces every
    number with ``0`` and drops punctuation, so template messages that differ only in a
    code, price or date are treated as the same message.
    """
    key = ascii_fold(normalize_for_matching(mask_pii(text)))
    key = _DIGITS_RE.sub("0", key)
    return _NON_WORD_RE.sub(" ", key).strip()


def deduplicate(df: pd.DataFrame) -> pd.DataFrame:
    """Remove duplicate messages.

    Groups whose copies carry *different* labels are ambiguous and dropped entirely.
    Otherwise the first copy by source priority is kept.
    """
    work = df.assign(
        _key=df["text"].map(dedup_key),
        _priority=df["source"].map(_SOURCE_PRIORITY),
    )
    label_counts = work.groupby("_key")["label"].transform("nunique")
    conflicting = work[label_counts > 1]
    if not conflicting.empty:
        logger.warning(
            "Dropping %d rows in %d groups with conflicting labels",
            len(conflicting),
            conflicting["_key"].nunique(),
        )
    work = work[label_counts == 1]

    work = work.sort_values("_priority", kind="stable")
    deduped = work.drop_duplicates("_key", keep="first").sort_index()
    logger.info("Deduplication: %d -> %d rows", len(df), len(deduped))
    return deduped.drop(columns=["_key", "_priority"]).reset_index(drop=True)


def split_dataset(df: pd.DataFrame, seed: int = config.SEED) -> dict[str, pd.DataFrame]:
    """Split a deduplicated dataset into train / val / test.

    Args:
        df: Data in the common schema, already deduplicated.
        seed: Random seed for the stratified split.

    Returns:
        A dict with keys ``"train"``, ``"val"`` and ``"test"``.
    """
    is_synthetic = df["source"] == config.SOURCE_SYNTHETIC
    real, synthetic = df[~is_synthetic], df[is_synthetic]

    train_val, test = train_test_split(
        real,
        test_size=config.TEST_RATIO,
        stratify=real["label"],
        random_state=seed,
    )
    # VAL_RATIO is relative to the full real set, so rescale it to the remaining part.
    val_share = config.VAL_RATIO / (config.TRAIN_RATIO + config.VAL_RATIO)
    train, val = train_test_split(
        train_val,
        test_size=val_share,
        stratify=train_val["label"],
        random_state=seed,
    )
    train = pd.concat([train, synthetic])

    splits = {"train": train, "val": val, "test": test}
    return {name: part.reset_index(drop=True) for name, part in splits.items()}
