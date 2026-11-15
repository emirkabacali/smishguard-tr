import pytest

from smishguard.features.url_features import evaluate_url_rules
from smishguard.features.urls import extract_urls


def fired(text: str) -> set[str]:
    return {reason.code for reason in evaluate_url_rules(extract_urls(text))}


RULE_CASES = {
    "BRAND_IMPERSONATION": (
        [
            "hxxps://ptt-kargo-takip[.]xyz",
            "https://edevlet-tazminat.info/basvuru",
            "https://login.ziraat-guvenlik.com",
            "https://mngkargo-teslimat.click",
            "https://ptt.kargo-takip.top",  # brand in the subdomain
        ],
        [
            "https://gonderitakip.ptt.gov.tr",  # official zone
            "https://www.turkiye.gov.tr",
            "https://www.yurticikargo.com/tr",  # allowlisted brand domain
            "https://www.garantibbva.com.tr",
            "https://paraskargo.com",  # "aras" inside a word is not a brand match
        ],
    ),
    "SHORTENER": (
        ["bit.ly/3xArAs9", "https://tinyurl.com/abc", "https://cutt.ly/x"],
        ["https://bitly-fake.com", "https://www.ptt.gov.tr"],
    ),
    "SUSPICIOUS_TLD": (
        ["https://kargo.xyz", "hgs-ceza.click", "https://odeme.top/a"],
        ["https://example.com", "https://www.isbank.com.tr", "https://site.org"],
    ),
    "IP_IN_URL": (
        ["http://185.62.13.77/kargo", "https://10.0.0.1:8443/login"],
        ["https://185-62-13-77.com", "https://kargo.com/185.62.13.77"],
    ),
    "PUNYCODE": (
        ["https://xn--otoyol-gei-ihlal-zpb.com", "https://xn--pt-wka.xyz/a"],
        ["https://otoyol.com", "https://xnxn.com"],
    ),
    "EXCESSIVE_HYPHENS_DIGITS": (
        ["https://ptt-kargo-takip.com", "https://kargo2024123.com", "https://a-b-c.net"],
        ["https://ptt-kargo.com", "https://www.turkcell.com.tr", "http://185.62.13.77/a"],
    ),
}

POSITIVE = [(code, text) for code, (pos, _) in RULE_CASES.items() for text in pos]
NEGATIVE = [(code, text) for code, (_, neg) in RULE_CASES.items() for text in neg]


@pytest.mark.parametrize(("code", "text"), POSITIVE)
def test_rule_fires(code: str, text: str) -> None:
    assert code in fired(text)


@pytest.mark.parametrize(("code", "text"), NEGATIVE)
def test_rule_does_not_fire(code: str, text: str) -> None:
    assert code not in fired(text)


def test_every_url_rule_has_two_positive_and_two_negative_cases() -> None:
    for positives, negatives in RULE_CASES.values():
        assert len(positives) >= 2 and len(negatives) >= 2


def test_official_domains_raise_no_alarm_at_all() -> None:
    text = "Detaylar: https://gonderitakip.ptt.gov.tr ve https://www.turkiye.gov.tr"
    assert fired(text) == set()


def test_rule_fires_once_and_names_the_offending_link() -> None:
    reasons = evaluate_url_rules(extract_urls("https://a.xyz/1 https://b.xyz/2"))
    tld_reasons = [r for r in reasons if r.code == "SUSPICIOUS_TLD"]
    assert len(tld_reasons) == 1
    assert ".xyz" in tld_reasons[0].message


def test_brand_reason_message_names_the_brand() -> None:
    reasons = evaluate_url_rules(extract_urls("hxxps://ptt-kargo-takip[.]xyz"))
    brand = next(r for r in reasons if r.code == "BRAND_IMPERSONATION")
    assert "(ptt)" in brand.message
    assert brand.weight == 0.35
