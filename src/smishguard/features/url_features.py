"""URL-based smishing indicators.

Every rule looks at all links in a message and fires at most once, naming the first link
that triggered it.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

from smishguard import config
from smishguard.data.normalize import ascii_fold
from smishguard.features.reasons import Reason, make_reason
from smishguard.features.urls import ParsedUrl


def is_official(url: ParsedUrl) -> bool:
    """True if the link belongs to an allowlisted brand domain or a restricted official zone."""
    return (
        url.registered_domain in config.OFFICIAL_DOMAINS or url.suffix in config.OFFICIAL_SUFFIXES
    )


def find_brand(url: ParsedUrl) -> str | None:
    """Return the first brand keyword found in the link's hostname labels, if any."""
    if url.is_ip:
        return None
    labels = ascii_fold(f"{url.subdomain}.{url.domain}".strip(".")).split(".")
    for brand in config.BRAND_KEYWORDS:
        for label in labels:
            if len(brand) <= config.SHORT_BRAND_MAX_LENGTH:
                # Short brands must start or end a label: "ptt-kargo", "mngkargo", "kargo-hgs".
                if label.startswith(brand) or label.endswith(brand):
                    return brand
            elif brand in label:
                return brand
    return None


def check_brand_impersonation(url: ParsedUrl) -> str | None:
    """Brand name in the hostname, but the domain is not the brand's official one."""
    if is_official(url):
        return None
    return find_brand(url)


def check_shortener(url: ParsedUrl) -> str | None:
    """Link uses a known URL shortening service."""
    return url.registered_domain if url.registered_domain in config.URL_SHORTENERS else None


def check_suspicious_tld(url: ParsedUrl) -> str | None:
    """Link ends with a TLD frequently abused in scams."""
    return url.tld if url.tld in config.SUSPICIOUS_TLDS else None


def check_ip_in_url(url: ParsedUrl) -> str | None:
    """Link host is a raw IPv4 address."""
    return url.host if url.is_ip else None


def check_punycode(url: ParsedUrl) -> str | None:
    """A hostname label is punycode-encoded (``xn--``), typical for look-alike domains."""
    return url.host if any(label.startswith("xn--") for label in url.host.split(".")) else None


def check_excessive_hyphens_digits(url: ParsedUrl) -> str | None:
    """The registered domain label has many hyphens or digits (``ptt-kargo-takip``)."""
    if url.is_ip:
        return None
    hyphens = url.domain.count("-")
    digits = sum(ch.isdigit() for ch in url.domain)
    if hyphens >= config.MAX_DOMAIN_HYPHENS or digits >= config.MAX_DOMAIN_DIGITS:
        return url.registered_domain
    return None


URL_RULES: dict[str, Callable[[ParsedUrl], str | None]] = {
    "BRAND_IMPERSONATION": check_brand_impersonation,
    "IP_IN_URL": check_ip_in_url,
    "PUNYCODE": check_punycode,
    "SHORTENER": check_shortener,
    "SUSPICIOUS_TLD": check_suspicious_tld,
    "EXCESSIVE_HYPHENS_DIGITS": check_excessive_hyphens_digits,
}


def evaluate_url_rules(urls: Sequence[ParsedUrl]) -> list[Reason]:
    """Run every URL rule over all links; each rule fires at most once per message."""
    reasons = []
    for code, check in URL_RULES.items():
        for url in urls:
            detail = check(url)
            if detail is not None:
                reasons.append(make_reason(code, detail))
                break
    return reasons
