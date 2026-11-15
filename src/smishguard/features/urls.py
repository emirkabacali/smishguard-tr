"""Extract links from SMS text and split their hostnames into parts.

Links are only *parsed*, never visited. Hostnames are split with ``tldextract`` using the
public suffix list snapshot bundled with the package (no network access, works in CI):
``login.ptt-kargo.com.tr`` -> subdomain ``login``, domain ``ptt-kargo``, suffix ``com.tr``.
"""

from __future__ import annotations

import ipaddress
import re
from dataclasses import dataclass
from functools import lru_cache

import tldextract

from smishguard import config
from smishguard.data.normalize import refang

# A link with a scheme or "www.", or a bare domain such as "ptt-kargo.xyz/takip".
_SCHEME_OR_WWW_RE = re.compile(r"(?:https?://|www\.)[^\s<>\"']+", re.IGNORECASE)
_BARE_DOMAIN_RE = re.compile(
    r"(?<![\w@./-])(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z]{2,}(?:/[^\s<>\"']*)?",
    re.IGNORECASE,
)
_TRAILING_PUNCTUATION = ".,;:!?)]}'\""


@dataclass(frozen=True)
class ParsedUrl:
    """A link found in a message, with its hostname split into parts."""

    raw: str
    host: str
    subdomain: str
    domain: str
    suffix: str
    is_ip: bool

    @property
    def registered_domain(self) -> str:
        """Domain + public suffix, e.g. ``ptt-kargo.com.tr`` (the part someone registered)."""
        if self.is_ip:
            return self.host
        return f"{self.domain}.{self.suffix}" if self.suffix else self.domain

    @property
    def tld(self) -> str:
        """Last label of the suffix, e.g. ``tr`` for ``com.tr``."""
        return self.suffix.rsplit(".", 1)[-1] if self.suffix else ""


@lru_cache(maxsize=1)
def _extractor() -> tldextract.TLDExtract:
    # suffix_list_urls=() + cache_dir=None: use the bundled snapshot, never the network.
    return tldextract.TLDExtract(suffix_list_urls=(), cache_dir=None)


def _host_of(link: str) -> str:
    without_scheme = re.sub(r"^https?://", "", link, flags=re.IGNORECASE)
    host = re.split(r"[/?#]", without_scheme, maxsplit=1)[0]
    host = host.rsplit("@", 1)[-1]  # drop "user:pass@"
    host = host.split(":", 1)[0]  # drop ":port"
    return host.lower().rstrip(".")


def _is_ipv4(host: str) -> bool:
    try:
        ipaddress.IPv4Address(host)
    except ValueError:
        return False
    return True


def parse_url(link: str) -> ParsedUrl | None:
    """Parse a single link. Returns None if it has no valid public suffix or IP host."""
    host = _host_of(link)
    if not host:
        return None
    if _is_ipv4(host):
        return ParsedUrl(raw=link, host=host, subdomain="", domain=host, suffix="", is_ip=True)
    parts = _extractor()(host)
    if not parts.suffix or not parts.domain:
        return None
    return ParsedUrl(
        raw=link,
        host=host,
        subdomain=parts.subdomain,
        domain=parts.domain,
        suffix=parts.suffix,
        is_ip=False,
    )


def _strip_trailing(link: str) -> str:
    return link.rstrip(_TRAILING_PUNCTUATION)


def extract_urls(text: str) -> list[ParsedUrl]:
    """Find all links in ``text`` (defanged links are refanged first).

    Links with ``http(s)://`` or ``www.`` are always considered. Bare domains are only
    accepted when their TLD is in :data:`smishguard.config.BARE_DOMAIN_TLDS`.
    Duplicate hosts are reported once.
    """
    text = refang(text)
    candidates: list[tuple[str, bool]] = []
    for match in _SCHEME_OR_WWW_RE.finditer(text):
        candidates.append((_strip_trailing(match.group(0)), False))
    remaining = _SCHEME_OR_WWW_RE.sub(" ", text)
    for match in _BARE_DOMAIN_RE.finditer(remaining):
        candidates.append((_strip_trailing(match.group(0)), True))

    urls: list[ParsedUrl] = []
    seen_hosts: set[str] = set()
    for link, is_bare in candidates:
        parsed = parse_url(link)
        if parsed is None or parsed.host in seen_hosts:
            continue
        if is_bare and parsed.tld not in config.BARE_DOMAIN_TLDS:
            continue
        seen_hosts.add(parsed.host)
        urls.append(parsed)
    return urls
