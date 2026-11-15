"""The rule engine entry point: run every rule and turn the results into a score.

Each fired rule becomes a :class:`Reason` with a code, a weight and a human-readable message.
The rule score is the sum of the weights, capped at 1.0.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from smishguard import config


@dataclass(frozen=True)
class Reason:
    """One explanation for why a message looks suspicious."""

    code: str
    weight: float
    message: str


def make_reason(code: str, detail: str = "") -> Reason:
    """Create a :class:`Reason` using the configured weight and message template."""
    return Reason(
        code=code,
        weight=config.RULE_WEIGHTS[code],
        message=config.RULE_MESSAGES[code].format(detail=detail),
    )


def rule_score(reasons: Iterable[Reason]) -> float:
    """Sum of the weights of the fired rules, capped at 1.0."""
    return round(min(1.0, sum(reason.weight for reason in reasons)), 4)


def evaluate_rules(text: str) -> list[Reason]:
    """Run all URL and text rules on ``text``.

    Returns:
        The fired rules, highest weight first (ties keep rule order).
    """
    # Imported here to keep this module importable from the feature modules without cycles.
    from smishguard.features.text_features import evaluate_text_rules
    from smishguard.features.url_features import evaluate_url_rules
    from smishguard.features.urls import extract_urls

    reasons = evaluate_url_rules(extract_urls(text)) + evaluate_text_rules(text)
    return sorted(reasons, key=lambda reason: reason.weight, reverse=True)
