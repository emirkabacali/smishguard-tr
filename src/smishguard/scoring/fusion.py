"""Combine the text model and the rule engine.

``risk = alpha * ml_probability + (1 - alpha) * rule_score``

``alpha`` controls how much the ML model is trusted relative to the rules. The risk score is
mapped to a level with two thresholds: below ``medium_threshold`` is *low*, below
``high_threshold`` is *medium*, otherwise *high*. A message is counted as malicious in the
metrics when its level is medium or high.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal

from smishguard import config

RiskLevel = Literal["low", "medium", "high"]


@dataclass(frozen=True)
class FusionParams:
    """Fusion weight and level thresholds."""

    alpha: float = config.DEFAULT_ALPHA
    medium_threshold: float = config.DEFAULT_MEDIUM_THRESHOLD
    high_threshold: float = config.DEFAULT_HIGH_THRESHOLD

    def __post_init__(self) -> None:
        if not 0.0 <= self.alpha <= 1.0:
            raise ValueError(f"alpha must be in [0, 1], got {self.alpha}")
        if not 0.0 < self.medium_threshold <= self.high_threshold <= 1.0:
            raise ValueError(
                "thresholds must satisfy 0 < medium <= high <= 1, got "
                f"{self.medium_threshold} / {self.high_threshold}"
            )


def fuse(ml_probability: float, rule_score: float, alpha: float) -> float:
    """Weighted average of the model probability and the rule score."""
    return alpha * ml_probability + (1.0 - alpha) * rule_score


def risk_level(score: float, params: FusionParams) -> RiskLevel:
    """Map a risk score to ``low`` / ``medium`` / ``high``."""
    if score >= params.high_threshold:
        return "high"
    if score >= params.medium_threshold:
        return "medium"
    return "low"


def is_flagged(score: float, params: FusionParams) -> bool:
    """Binary decision used for metrics: medium and high count as malicious."""
    return score >= params.medium_threshold


def save_fusion_params(params: FusionParams, path: Path = config.FUSION_PARAMS_PATH) -> None:
    """Write tuned parameters as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(params), indent=2) + "\n", encoding="utf-8", newline="\n")


def load_fusion_params(path: Path = config.FUSION_PARAMS_PATH) -> FusionParams:
    """Load tuned parameters, falling back to the defaults in ``config`` if none exist."""
    if not path.exists():
        return FusionParams()
    data = json.loads(path.read_text(encoding="utf-8"))
    return FusionParams(
        alpha=float(data["alpha"]),
        medium_threshold=float(data["medium_threshold"]),
        high_threshold=float(data["high_threshold"]),
    )
