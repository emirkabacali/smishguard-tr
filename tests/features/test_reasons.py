import dataclasses
import subprocess
import sys

import pytest

from smishguard import config
from smishguard.features.reasons import Reason, evaluate_rules, make_reason, rule_score

PTT_EXAMPLE = (
    "PTT: Kargonuz adres eksikligi nedeniyle bekliyor. "
    "24 saat icinde guncelleyin: hxxps://ptt-kargo-takip[.]xyz"
)


def test_plan_example_fires_expected_rules_sorted_by_weight() -> None:
    reasons = evaluate_rules(PTT_EXAMPLE)
    codes = [r.code for r in reasons]
    assert {"BRAND_IMPERSONATION", "SUSPICIOUS_TLD", "URGENCY_LANGUAGE", "ADDRESS_ISSUE"} <= set(
        codes
    )
    assert codes[0] == "BRAND_IMPERSONATION"
    weights = [r.weight for r in reasons]
    assert weights == sorted(weights, reverse=True)


def test_rule_score_is_capped_at_one() -> None:
    assert rule_score(evaluate_rules(PTT_EXAMPLE)) == pytest.approx(0.95)
    # Adding a money reference pushes the raw sum to 1.05, which is capped.
    assert rule_score(evaluate_rules(PTT_EXAMPLE + " Ucret 19 TL.")) == 1.0


def test_rule_score_sums_weights() -> None:
    reasons = [make_reason("SHORTENER", "bit.ly"), make_reason("MONEY_OR_FINE")]
    assert rule_score(reasons) == pytest.approx(0.30)
    assert rule_score([]) == 0.0


def test_legitimate_message_has_zero_rule_score() -> None:
    assert rule_score(evaluate_rules("Yarin saat 10'da toplanti var, unutma.")) == 0.0


def test_reason_is_immutable() -> None:
    reason = make_reason("PUNYCODE", "xn--a.com")
    with pytest.raises(dataclasses.FrozenInstanceError):
        reason.weight = 1.0  # type: ignore[misc]
    assert isinstance(reason, Reason)


def test_every_rule_has_weight_and_message() -> None:
    from smishguard.features.url_features import URL_RULES

    codes = set(URL_RULES) | set(config.TEXT_RULES)
    assert codes == set(config.RULE_WEIGHTS) == set(config.RULE_MESSAGES)
    assert all(0 < w <= 1 for w in config.RULE_WEIGHTS.values())


def test_rule_engine_does_not_need_the_ml_model() -> None:
    # Run in a fresh interpreter so that modules imported by other tests do not interfere.
    code = (
        "import sys\n"
        "from smishguard.features.reasons import evaluate_rules\n"
        "evaluate_rules('hxxps://ptt-kargo[.]xyz')\n"
        "assert not [m for m in sys.modules if m.startswith('smishguard.model')]\n"
        "assert 'sklearn' not in sys.modules\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)
