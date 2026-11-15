"""Training utilities: cross-validation, validation comparison, persistence."""

from __future__ import annotations

import hashlib
import json
import logging
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from smishguard import __version__, config
from smishguard.metrics import classification_metrics

logger = logging.getLogger(__name__)

CV_SCORING = ("precision", "recall", "f1")


def cv_splits(
    train: pd.DataFrame, n_splits: int = config.CV_FOLDS, seed: int = config.SEED
) -> Iterator[tuple[np.ndarray, np.ndarray]]:
    """Yield stratified CV folds in which synthetic rows are always in the training part.

    This mirrors the train/val/test policy (synthetic data is never used for evaluation),
    so cross-validation scores are measured on real messages only.
    """
    positions = np.arange(len(train))
    is_synthetic = (train["source"] == config.SOURCE_SYNTHETIC).to_numpy()
    real_pos, synthetic_pos = positions[~is_synthetic], positions[is_synthetic]
    labels = train["label"].to_numpy()[real_pos]

    folds = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    for fit_idx, eval_idx in folds.split(real_pos, labels):
        yield np.concatenate([real_pos[fit_idx], synthetic_pos]), real_pos[eval_idx]


def cross_validate_pipeline(pipeline: Pipeline, train: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Run stratified k-fold CV and return the mean and standard deviation per metric."""
    scores = cross_validate(
        clone(pipeline),
        train["text"],
        train["label"],
        cv=list(cv_splits(train)),
        scoring=CV_SCORING,
    )
    return {
        metric: {
            "mean": round(float(scores[f"test_{metric}"].mean()), 4),
            "std": round(float(scores[f"test_{metric}"].std()), 4),
        }
        for metric in CV_SCORING
    }


def evaluate_pipeline(
    pipeline: Pipeline, data: pd.DataFrame, threshold: float = config.ML_DECISION_THRESHOLD
) -> dict[str, float | int]:
    """Evaluate a fitted pipeline on ``data`` with the given probability threshold."""
    proba = pipeline.predict_proba(data["text"])[:, 1]
    predictions = (proba >= threshold).astype(int)
    return classification_metrics(data["label"], predictions, proba)


def select_model(
    validation_f1: dict[str, float], tolerance: float = config.MODEL_SELECTION_TOLERANCE
) -> str:
    """Pick a model by validation F1, preferring earlier entries within ``tolerance``.

    Args:
        validation_f1: Model name -> validation F1, in preference order (dicts keep order).
        tolerance: Minimum F1 improvement a less preferred model needs to be chosen.

    Returns:
        The selected model name.
    """
    names = list(validation_f1)
    best = names[0]
    for name in names[1:]:
        if validation_f1[name] > validation_f1[best] + tolerance:
            best = name
    return best


def fit_pipeline(pipeline: Pipeline, train: pd.DataFrame) -> Pipeline:
    """Fit a fresh copy of ``pipeline`` on the training data and return it."""
    fitted = clone(pipeline)
    fitted.fit(train["text"], train["label"])
    return fitted


def file_sha256(path: Path) -> str:
    """Return the hex SHA-256 of a file (used to fingerprint the training data)."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_model(
    pipeline: Pipeline,
    model_name: str,
    data_summary: dict[str, object],
    validation_metrics: dict[str, float | int],
    model_path: Path = config.TEXT_MODEL_PATH,
    metadata_path: Path = config.MODEL_METADATA_PATH,
) -> dict[str, object]:
    """Persist the fitted pipeline with joblib and write a metadata JSON next to it."""
    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    metadata: dict[str, object] = {
        "model_name": model_name,
        "model_version": __version__,
        "trained_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "seed": config.SEED,
        "decision_threshold": config.ML_DECISION_THRESHOLD,
        "data": data_summary,
        "validation_metrics": validation_metrics,
    }
    metadata_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8", newline="\n")
    logger.info("Saved model to %s", model_path)
    return metadata
