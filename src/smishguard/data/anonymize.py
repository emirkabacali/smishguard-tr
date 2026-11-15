"""Mask personal data (PII) in SMS text: IBANs, T.C. identity numbers, phone numbers, e-mails.

The masks are applied both when building the dataset and at inference time, so the model sees
placeholder tokens such as ``<PHONE>`` instead of real numbers. Over-masking (e.g. a 7-digit
order number) is preferred to leaking a real phone number.
"""

from __future__ import annotations

import re

MASK_IBAN = "<IBAN>"
MASK_TCKN = "<TCKN>"
MASK_PHONE = "<PHONE>"
MASK_EMAIL = "<EMAIL>"

_SEP = r"[\s.\-]?"  # optional single separator between digit groups

# TR IBAN: "TR" + 24 digits, optionally grouped in blocks of four.
_IBAN_RE = re.compile(rf"\bTR{_SEP}\d{{2}}(?:{_SEP}\d{{4}}){{5}}{_SEP}\d{{2}}\b", re.IGNORECASE)

# Candidate T.C. identity number: exactly 11 digits, first digit non-zero (checksum verified).
_TCKN_RE = re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)")

_PHONE_RES = (
    # Optional +90 / 0090 / 0 prefix, 3-digit area or operator code (2xx-5xx, 8xx) + 7 digits.
    # Matches 0532 123 45 67, +90 532 1234567, 0 286 2132097, 0850 222 11 33, 5321234567.
    re.compile(
        rf"(?<![\d+])(?:(?:\+90|0090|0){_SEP})?[2-58]\d{{2}}{_SEP}\d{{3}}{_SEP}\d{{2}}{_SEP}\d{{2}}(?!\d)"
    ),
    # Nationwide business numbers: 444 0 562, 444 98 99, 4440900.
    re.compile(rf"(?<!\d)444{_SEP}(?:\d{_SEP}\d{{3}}|\d{{2}}{_SEP}\d{{2}})(?!\d)"),
    # Bare 7-digit local numbers without area code: 7551880.
    re.compile(r"(?<!\d)[2-9]\d{6}(?!\d)"),
    # Fallback for malformed numbers: any 10-12 digit run starting with 0 (0312247386440).
    re.compile(r"(?<!\d)0\d{9,11}(?!\d)"),
)

_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")


def is_valid_tckn(digits: str) -> bool:
    """Check the official T.C. identity number checksum.

    Args:
        digits: An 11-character string of digits.

    Returns:
        True if both check digits (10th and 11th) are correct.
    """
    if len(digits) != 11 or not digits.isdigit() or digits[0] == "0":
        return False
    d = [int(c) for c in digits]
    tenth = ((d[0] + d[2] + d[4] + d[6] + d[8]) * 7 - (d[1] + d[3] + d[5] + d[7])) % 10
    eleventh = sum(d[:10]) % 10
    return d[9] == tenth and d[10] == eleventh


def mask_iban(text: str) -> str:
    """Replace Turkish IBANs with ``<IBAN>``."""
    return _IBAN_RE.sub(MASK_IBAN, text)


def mask_tckn(text: str) -> str:
    """Replace 11-digit numbers that pass the T.C. checksum with ``<TCKN>``."""
    return _TCKN_RE.sub(lambda m: MASK_TCKN if is_valid_tckn(m.group(0)) else m.group(0), text)


def mask_phone(text: str) -> str:
    """Replace Turkish phone numbers (mobile, landline, 0850/444, bare local) with ``<PHONE>``."""
    for pattern in _PHONE_RES:
        text = pattern.sub(MASK_PHONE, text)
    return text


def mask_email(text: str) -> str:
    """Replace e-mail addresses with ``<EMAIL>``."""
    return _EMAIL_RE.sub(MASK_EMAIL, text)


MASK_NAME = "<NAME>"

_UPPER = "A-ZÇĞİÖŞÜ"
_LOWER = "a-zçğıöşü"
# Honorific followed by one to three capitalized words: "Sayın Ayşe Yılmaz", "Sn. Ali Veli".
_HONORIFIC_NAME_RE = re.compile(
    rf"\b(Sayın|Sayin|SAYIN|Sn\.?|Sevgili|Değerli|Degerli|Bay|Bayan)(\s+)"
    rf"([{_UPPER}][{_LOWER}]+(?:\s+[{_UPPER}][{_LOWER}]+){{0,2}})"
)
# Capitalized words after an honorific that are forms of address, not names.
_NOT_NAMES = frozenset(
    {"Müşterimiz", "Musterimiz", "Abonemiz", "AboneMiz", "Üyemiz", "Uyemiz", "Kullanıcı"}
)


def mask_honorific_names(text: str) -> str:
    """Replace personal names that follow a Turkish honorific with ``<NAME>``.

    Personal names cannot be detected reliably with regular expressions; this only covers the
    most common SMS pattern ("Sayın Ad Soyad"). Used for report excerpts.
    """

    def replace(match: re.Match[str]) -> str:
        honorific, space, words = match.groups()
        if words.split()[0] in _NOT_NAMES:
            return match.group(0)
        return f"{honorific}{space}{MASK_NAME}"

    return _HONORIFIC_NAME_RE.sub(replace, text)


def mask_pii(text: str) -> str:
    """Apply all masks. Order matters: IBAN and TCKN contain long digit runs, so they go first."""
    for masker in (mask_email, mask_iban, mask_tckn, mask_phone):
        text = masker(text)
    return text
