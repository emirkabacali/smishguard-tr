"""Text-based scam indicators for Turkish SMS (urgency, money, credentials, prizes, delivery).

Patterns live in :data:`smishguard.config.TEXT_RULES` and are matched on text that is
Turkish-lowercased and folded to ASCII, so "ÖDEME", "ödeme" and "odeme" all match.
"""

from __future__ import annotations

import re
from functools import lru_cache

from smishguard import config
from smishguard.data.normalize import ascii_fold, normalize_for_matching
from smishguard.features.reasons import Reason, make_reason


@lru_cache(maxsize=1)
def _compiled_rules() -> dict[str, tuple[re.Pattern[str], re.Pattern[str] | None]]:
    compiled = {}
    for code, spec in config.TEXT_RULES.items():
        include = re.compile("|".join(spec["patterns"]))
        exclude = re.compile("|".join(spec["exclude"])) if spec["exclude"] else None
        compiled[code] = (include, exclude)
    return compiled


def prepare(text: str) -> str:
    """Normalize text for keyword matching (NFC, refang, Turkish lowercase, ASCII fold)."""
    return ascii_fold(normalize_for_matching(text))


def fired_text_rules(text: str) -> list[str]:
    """Return the codes of the text rules that match ``text``."""
    prepared = prepare(text)
    fired = []
    for code, (include, exclude) in _compiled_rules().items():
        if include.search(prepared) and not (exclude and exclude.search(prepared)):
            fired.append(code)
    return fired


def evaluate_text_rules(text: str) -> list[Reason]:
    """Run all text rules and return a :class:`Reason` for each one that fired."""
    return [make_reason(code) for code in fired_text_rules(text)]
