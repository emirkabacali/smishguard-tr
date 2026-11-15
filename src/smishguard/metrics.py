"""Binary classification metrics shared by training and evaluation scripts."""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def classification_metrics(
    y_true: Sequence[int], y_pred: Sequence[int], y_score: Sequence[float] | None = None
) -> dict[str, float | int]:
    """Compute the metrics reported throughout the project (positive class = malicious).

    Args:
        y_true: Ground-truth labels.
        y_pred: Predicted labels.
        y_score: Optional scores / probabilities for the positive class (adds ROC AUC).

    Returns:
        precision, recall, F1, accuracy, false positive rate, confusion matrix counts and,
        when ``y_score`` is given, ROC AUC. Floats are rounded to 4 decimals.
    """
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
    result: dict[str, float | int] = {
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
        "accuracy": accuracy_score(y_true, y_pred),
        "false_positive_rate": fp / (fp + tn) if (fp + tn) else 0.0,
    }
    if y_score is not None and len(np.unique(y_true)) == 2:
        result["roc_auc"] = roc_auc_score(y_true, y_score)
    result = {k: round(float(v), 4) for k, v in result.items()}
    result.update({"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)})
    return result
