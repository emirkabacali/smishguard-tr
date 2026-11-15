"""Turkish-aware text normalization and URL (de)fanging.

Python's ``str.lower()`` follows English casing rules: ``"I".lower()`` returns ``"i"`` instead
of the Turkish dotless ``"ı"``, and ``"İ".lower()`` returns ``"i"`` followed by a combining dot.
:func:`turkish_lower` fixes both cases.
"""

from __future__ import annotations

import re
import unicodedata

_WHITESPACE_RE = re.compile(r"\s+")

# Turkish letters -> closest ASCII letter. Applied *after* lowercasing.
_ASCII_FOLD_TABLE = str.maketrans(
    {"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"}
)

# Defanged notations seen in threat-intel writing: hxxp(s), [.], (.), [dot], [:]
_REFANG_PATTERNS = (
    (re.compile(r"\bhxxp(s?)", re.IGNORECASE), r"http\1"),
    (re.compile(r"\[\.\]|\(\.\)|\[dot\]", re.IGNORECASE), "."),
    (re.compile(r"\[:\]"), ":"),
)

# A link that starts with a scheme or "www." and runs until whitespace.
_LINK_RE = re.compile(r"\b(?:https?://|www\.)[^\s]+", re.IGNORECASE)


def nfc(text: str) -> str:
    """Return the Unicode NFC (composed) form of ``text``.

    Composing first matters for Turkish: a decomposed ``"I" + U+0307`` becomes ``"İ"``.
    """
    return unicodedata.normalize("NFC", text)


def collapse_whitespace(text: str) -> str:
    """Replace runs of whitespace (including newlines) with a single space and strip."""
    return _WHITESPACE_RE.sub(" ", text).strip()


def turkish_lower(text: str) -> str:
    """Lowercase text using Turkish casing rules (I -> ı, İ -> i)."""
    return text.replace("I", "ı").replace("İ", "i").lower()


def ascii_fold(text: str) -> str:
    """Map Turkish-specific letters to ASCII (``ödeme`` -> ``odeme``).

    SMS senders often type without Turkish characters, so rule matching is done on a folded
    copy. Expects already lowercased text.
    """
    return text.translate(_ASCII_FOLD_TABLE)


def refang(text: str) -> str:
    """Turn defanged links back into their normal form (``hxxps://a[.]xyz`` -> ``https://a.xyz``)."""
    for pattern, replacement in _REFANG_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def _defang_link(match: re.Match[str]) -> str:
    link = match.group(0)
    scheme, sep, rest = link.partition("://")
    if not sep:  # "www.example.com/..." has no scheme
        scheme, rest = "", link
    host, slash, path = rest.partition("/")
    host = host.replace(".", "[.]")
    scheme = re.sub(r"^http", "hxxp", scheme, flags=re.IGNORECASE)
    return f"{scheme}{sep}{host}{slash}{path}"


def defang(text: str) -> str:
    """Make links non-clickable: ``https://a.xyz/p`` -> ``hxxps://a[.]xyz/p``.

    Only links that start with a scheme or ``www.`` are handled; idempotent on defanged text.
    """
    return _LINK_RE.sub(_defang_link, refang(text))


def clean_text(text: str) -> str:
    """Normalize Unicode, refang links and collapse whitespace. Keeps the original casing."""
    return collapse_whitespace(refang(nfc(text)))


def normalize_for_matching(text: str) -> str:
    """Full normalization used for matching: :func:`clean_text` + Turkish lowercase."""
    return turkish_lower(clean_text(text))
