"""Loading a trained text model, predicting probabilities and explaining it globally."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import joblib
import numpy as np
from sklearn.pipeline import Pipeline

from smishguard import config


def load_model(path: Path = config.TEXT_MODEL_PATH) -> Pipeline:
    """Load a pipeline saved by :func:`smishguard.model.train.save_model`.

    Raises:
        FileNotFoundError: If no model has been trained yet.
    """
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Run `python scripts/train.py` first.")
    return joblib.load(path)


def predict_proba(model: Pipeline, texts: Sequence[str]) -> np.ndarray:
    """Return the probability of the malicious class for each text."""
    return model.predict_proba(list(texts))[:, 1]


def top_ngrams(model: Pipeline, n: int = config.TOP_FEATURES_COUNT) -> dict[str, list[dict]]:
    """List the n-grams with the largest Logistic Regression coefficients per class.

    A positive coefficient pushes a message towards *malicious*, a negative one towards
    *legitimate*. Feature names are prefixed with their vectorizer (``char__`` / ``word__``).

    Raises:
        TypeError: If the classifier has no linear coefficients (e.g. Naive Bayes).
    """
    classifier = model.named_steps["classifier"]
    if not hasattr(classifier, "coef_"):
        raise TypeError(f"{type(classifier).__name__} has no coefficients to explain")
    names = model.named_steps["features"].get_feature_names_out()
    coefs = classifier.coef_[0]
    order = np.argsort(coefs)

    def describe(indices: np.ndarray) -> list[dict]:
        return [{"feature": str(names[i]), "weight": round(float(coefs[i]), 4)} for i in indices]

    return {"malicious": describe(order[::-1][:n]), "legitimate": describe(order[:n])}
