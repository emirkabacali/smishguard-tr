import unicodedata

import pytest

from smishguard.data.normalize import (
    ascii_fold,
    clean_text,
    collapse_whitespace,
    defang,
    nfc,
    normalize_for_matching,
    refang,
    turkish_lower,
)


def test_turkish_lower_handles_dotted_and_dotless_i() -> None:
    assert turkish_lower("IŞIK İzmir") == "ışık izmir"


def test_builtin_lower_is_wrong_for_turkish() -> None:
    # Documents *why* turkish_lower exists.
    assert "I".lower() == "i"
    assert "İ".lower() != "i"


def test_nfc_composes_decomposed_dotted_capital_i() -> None:
    decomposed = "İstanbul"  # "I" + COMBINING DOT ABOVE
    assert nfc(decomposed) == "İstanbul"
    assert turkish_lower(nfc(decomposed)) == "istanbul"


def test_collapse_whitespace() -> None:
    assert collapse_whitespace("  merhaba \n\t dunya  ") == "merhaba dunya"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("ödeme", "odeme"),
        ("çğıöşü", "cgiosu"),
        ("kargonuz", "kargonuz"),
    ],
)
def test_ascii_fold(text: str, expected: str) -> None:
    assert ascii_fold(text) == expected


@pytest.mark.parametrize(
    ("defanged", "expected"),
    [
        ("hxxps://ptt-kargo[.]xyz/a", "https://ptt-kargo.xyz/a"),
        ("HXXP://a(.)b[dot]com", "http://a.b.com"),
        ("hxxps[:]//x[.]top", "https://x.top"),
    ],
)
def test_refang(defanged: str, expected: str) -> None:
    assert refang(defanged) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("link: https://ptt-kargo.xyz/takip?id=1", "link: hxxps://ptt-kargo[.]xyz/takip?id=1"),
        ("www.ornek.com.tr adresine gir", "www[.]ornek[.]com[.]tr adresine gir"),
        ("http://185.62.13.77/k", "hxxp://185[.]62[.]13[.]77/k"),
        ("no links here.", "no links here."),
    ],
)
def test_defang(text: str, expected: str) -> None:
    assert defang(text) == expected


def test_defang_is_idempotent_and_reversible() -> None:
    original = "Odeme: https://hgs-ceza.click/odeme"
    once = defang(original)
    assert defang(once) == once
    assert refang(once) == original


def test_clean_text_keeps_case_and_refangs() -> None:
    assert clean_text("  PTT:\n hxxps://a[.]xyz ") == "PTT: https://a.xyz"


def test_normalize_for_matching() -> None:
    text = unicodedata.normalize("NFD", "İADE  için TIKLA")
    assert normalize_for_matching(text) == "iade için tıkla"
