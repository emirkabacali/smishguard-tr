import pytest

from smishguard.scoring.fusion import (
    FusionParams,
    fuse,
    is_flagged,
    load_fusion_params,
    risk_level,
    save_fusion_params,
)


@pytest.mark.parametrize(
    ("ml", "rules", "alpha", "expected"),
    [(0.8, 0.2, 0.5, 0.5), (0.8, 0.2, 1.0, 0.8), (0.8, 0.2, 0.0, 0.2), (0.9, 1.0, 0.7, 0.93)],
)
def test_fuse_is_weighted_average(ml: float, rules: float, alpha: float, expected: float) -> None:
    assert fuse(ml, rules, alpha) == pytest.approx(expected)


@pytest.mark.parametrize(
    ("score", "level"),
    [
        (0.0, "low"),
        (0.3499, "low"),
        (0.35, "medium"),
        (0.6499, "medium"),
        (0.65, "high"),
        (1.0, "high"),
    ],
)
def test_risk_level_uses_default_thresholds(score: float, level: str) -> None:
    assert risk_level(score, FusionParams()) == level


def test_is_flagged_counts_medium_and_high() -> None:
    params = FusionParams(alpha=0.7, medium_threshold=0.4, high_threshold=0.7)
    assert not is_flagged(0.39, params)
    assert is_flagged(0.4, params)
    assert is_flagged(0.9, params)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"alpha": 1.5},
        {"alpha": -0.1},
        {"medium_threshold": 0.7, "high_threshold": 0.5},
        {"medium_threshold": 0.0},
    ],
)
def test_invalid_params_are_rejected(kwargs: dict) -> None:
    with pytest.raises(ValueError):
        FusionParams(**kwargs)


def test_params_roundtrip_and_default_fallback(tmp_path) -> None:
    path = tmp_path / "fusion.json"
    assert load_fusion_params(path) == FusionParams()  # missing file -> defaults
    params = FusionParams(alpha=0.8, medium_threshold=0.45, high_threshold=0.7)
    save_fusion_params(params, path)
    assert load_fusion_params(path) == params
