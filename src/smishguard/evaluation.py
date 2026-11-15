"""Threshold / fusion-weight tuning on validation data and uncertainty estimates.

Selection rule everywhere: highest F1, ties broken by lower false positive rate, then by the
order of the grids (earlier wins). Grids are iterated in a fixed order, so results are
deterministic.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import numpy as np

from smishguard import config
from smishguard.metrics import classification_metrics


@dataclass(frozen=True)
class TuningResult:
    """Best parameters found on validation data and the metrics they achieve there."""

    alpha: float | None
    threshold: float
    metrics: dict[str, float | int]


def _is_better(candidate: dict, best: dict | None) -> bool:
    if best is None:
        return True
    if candidate["f1"] != best["f1"]:
        return candidate["f1"] > best["f1"]
    return candidate["false_positive_rate"] < best["false_positive_rate"]


def tune_threshold(
    y_true: Sequence[int],
    scores: Sequence[float],
    grid: Sequence[float] = config.THRESHOLD_GRID,
) -> TuningResult:
    """Find the decision threshold on ``scores`` that maximizes F1."""
    y = np.asarray(y_true)
    s = np.asarray(scores, dtype=float)
    best: TuningResult | None = None
    for threshold in grid:
        metrics = classification_metrics(y, (s >= threshold).astype(int), s)
        if _is_better(metrics, best.metrics if best else None):
            best = TuningResult(alpha=None, threshold=float(threshold), metrics=metrics)
    assert best is not None, "threshold grid must not be empty"
    return best


def tune_fusion(
    y_true: Sequence[int],
    ml_probabilities: Sequence[float],
    rule_scores: Sequence[float],
    alpha_grid: Sequence[float] = config.ALPHA_GRID,
    threshold_grid: Sequence[float] = config.THRESHOLD_GRID,
) -> TuningResult:
    """Grid-search ``alpha`` and the decision threshold of the fused score."""
    ml = np.asarray(ml_probabilities, dtype=float)
    rules = np.asarray(rule_scores, dtype=float)
    best: TuningResult | None = None
    for alpha in alpha_grid:
        candidate = tune_threshold(y_true, alpha * ml + (1 - alpha) * rules, threshold_grid)
        if _is_better(candidate.metrics, best.metrics if best else None):
            best = TuningResult(
                alpha=float(alpha), threshold=candidate.threshold, metrics=candidate.metrics
            )
    assert best is not None, "alpha grid must not be empty"
    return best


def choose_high_threshold(
    y_true: Sequence[int],
    scores: Sequence[float],
    medium_threshold: float,
    grid: Sequence[float] = config.THRESHOLD_GRID,
    min_precision: float = config.HIGH_LEVEL_MIN_PRECISION,
    default: float = config.DEFAULT_HIGH_THRESHOLD,
) -> float:
    """Threshold for the "high" level: precise on validation and never below ``default``.

    "High" risk should mean "almost certainly malicious", so the threshold is the lowest grid
    value above ``medium_threshold`` whose precision reaches ``min_precision``. It is then
    raised to at least ``default`` so that the medium band keeps a meaningful width even when
    the model is very confident on validation data. Falls back to ``max(default,
    medium_threshold)`` if no grid value is precise enough.
    """
    y = np.asarray(y_true)
    s = np.asarray(scores, dtype=float)
    floor = float(max(default, medium_threshold))
    for threshold in sorted(t for t in grid if t > medium_threshold):
        flagged = s >= threshold
        if flagged.sum() == 0:
            break
        if y[flagged].mean() >= min_precision:
            return max(float(threshold), floor)
    return floor


def bootstrap_ci(
    y_true: Sequence[int],
    y_pred: Sequence[int],
    metric: Callable[[np.ndarray, np.ndarray], float],
    n_samples: int = config.BOOTSTRAP_SAMPLES,
    confidence: float = config.CONFIDENCE_LEVEL,
    seed: int = config.SEED,
) -> tuple[float, float]:
    """Percentile bootstrap confidence interval of ``metric`` (resampling messages)."""
    y = np.asarray(y_true)
    p = np.asarray(y_pred)
    rng = np.random.default_rng(seed)
    values = []
    for _ in range(n_samples):
        idx = rng.integers(0, len(y), len(y))
        values.append(metric(y[idx], p[idx]))
    tail = (1 - confidence) / 2 * 100
    low, high = np.percentile(values, [tail, 100 - tail])
    return round(float(low), 4), round(float(high), 4)
