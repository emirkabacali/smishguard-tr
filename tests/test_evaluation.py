import numpy as np
import pytest
from sklearn.metrics import f1_score

from smishguard.evaluation import bootstrap_ci, choose_high_threshold, tune_fusion, tune_threshold

Y = [0, 0, 0, 0, 1, 1, 1, 1]


def test_tune_threshold_finds_separating_value() -> None:
    scores = [0.1, 0.2, 0.3, 0.45, 0.55, 0.7, 0.8, 0.9]
    result = tune_threshold(Y, scores, grid=[0.25, 0.5, 0.75])
    assert result.threshold == 0.5
    assert result.metrics["f1"] == 1.0
    assert result.alpha is None


def test_tune_threshold_breaks_ties_by_fpr_then_grid_order() -> None:
    scores = [0.1, 0.2, 0.3, 0.4, 0.6, 0.7, 0.8, 0.9]
    # 0.45 and 0.5 both separate perfectly -> the earlier grid value wins.
    assert tune_threshold(Y, scores, grid=[0.45, 0.5]).threshold == 0.45


def test_tune_fusion_uses_rules_when_they_help() -> None:
    ml = [0.1, 0.2, 0.6, 0.3, 0.4, 0.7, 0.8, 0.9]  # one legit message looks risky to ML
    rules = [0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0]  # rules separate perfectly
    result = tune_fusion(Y, ml, rules, alpha_grid=[0.9, 0.5], threshold_grid=[0.3, 0.5, 0.7])
    assert result.alpha == 0.5
    assert result.metrics["f1"] == 1.0


def test_choose_high_threshold_respects_precision_and_floor() -> None:
    y = [0, 0, 1, 0, 1, 1, 1, 1]
    scores = [0.1, 0.2, 0.5, 0.55, 0.6, 0.8, 0.9, 0.95]
    # 0.6 is the first precise threshold, but the floor (default) raises it to 0.65.
    assert choose_high_threshold(y, scores, 0.5, grid=[0.55, 0.6, 0.7], default=0.65) == 0.65
    assert choose_high_threshold(y, scores, 0.5, grid=[0.55, 0.7], default=0.6) == 0.7


def test_choose_high_threshold_falls_back_when_nothing_is_precise() -> None:
    y = [1, 0, 1, 0]
    scores = [0.9, 0.95, 0.8, 0.99]
    assert choose_high_threshold(y, scores, 0.5, grid=[0.6, 0.9], default=0.65) == 0.65


def test_bootstrap_ci_contains_point_estimate_and_is_deterministic() -> None:
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 200)
    pred = np.where(rng.random(200) < 0.85, y, 1 - y)
    point = f1_score(y, pred)
    low, high = bootstrap_ci(y, pred, f1_score, n_samples=300)
    assert low <= point <= high
    assert (low, high) == bootstrap_ci(y, pred, f1_score, n_samples=300)
    assert high - low == pytest.approx(high - low) and 0 < high - low < 0.3
