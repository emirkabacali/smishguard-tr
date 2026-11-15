import pytest

from smishguard.data.anonymize import (
    MASK_EMAIL,
    MASK_IBAN,
    MASK_PHONE,
    MASK_TCKN,
    is_valid_tckn,
    mask_email,
    mask_honorific_names,
    mask_iban,
    mask_phone,
    mask_pii,
    mask_tckn,
)

# Test identity number generated to satisfy the checksum; it belongs to no one.
VALID_TCKN = "10000000146"


@pytest.mark.parametrize(
    "phone",
    [
        "05321234567",
        "0532 123 45 67",
        "0532-123-45-67",
        "+90 532 123 45 67",
        "+905321234567",
        "5321234567",
        "0 286 2132097",
        "0222 2312840",
        "02166517380",
        "0850 222 11 33",
        "444 0 562",
        "444 98 99",
        "4440900",
        "7551880",
        "0433232685",
        "031224738644",
        "002222330316",
    ],
)
def test_mask_phone_matches_turkish_formats(phone: str) -> None:
    assert mask_phone(f"Bizi arayin: {phone}.") == f"Bizi arayin: {MASK_PHONE}."


@pytest.mark.parametrize(
    "text",
    [
        "Tarih: 05.07.2011",
        "Fiyat 100TL ve uzeri",
        "BKR yaz 8073e gonder",
        "Kodunuz 482913",
        "12.90-29.90 TL arasi",
        "31.05.2011 22:00",
    ],
)
def test_mask_phone_ignores_dates_prices_and_short_codes(text: str) -> None:
    assert mask_phone(text) == text


@pytest.mark.parametrize(
    "iban",
    [
        "TR330006100519786457841326",
        "TR33 0006 1005 1978 6457 8413 26",
        "tr33 0006 1005 1978 6457 8413 26",
    ],
)
def test_mask_iban(iban: str) -> None:
    assert mask_iban(f"IBAN: {iban} ") == f"IBAN: {MASK_IBAN} "


def test_mask_iban_requires_full_length() -> None:
    text = "TR33 0006 1005"
    assert mask_iban(text) == text


def test_tckn_checksum() -> None:
    assert is_valid_tckn(VALID_TCKN)
    assert not is_valid_tckn("10000000147")  # wrong last digit
    assert not is_valid_tckn("01234567890")  # cannot start with 0
    assert not is_valid_tckn("123")


def test_mask_tckn_only_masks_valid_numbers() -> None:
    assert mask_tckn(f"TC: {VALID_TCKN}") == f"TC: {MASK_TCKN}"
    assert mask_tckn("Siparis 12345678901") == "Siparis 12345678901"


@pytest.mark.parametrize("email", ["ali.veli@example.com", "info+promo@firma.com.tr"])
def test_mask_email(email: str) -> None:
    assert mask_email(f"Mail: {email} adresine") == f"Mail: {MASK_EMAIL} adresine"


def test_mask_pii_combines_all_masks() -> None:
    text = f"IBAN TR330006100519786457841326, TC {VALID_TCKN}, tel 05321234567, a@b.com"
    assert mask_pii(text) == f"IBAN {MASK_IBAN}, TC {MASK_TCKN}, tel {MASK_PHONE}, {MASK_EMAIL}"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Sayın Ayşe Yılmaz. Siparişiniz hazır", "Sayın <NAME>. Siparişiniz hazır"),
        ("Sn. Ali Veli, randevunuz yarin", "Sn. <NAME>, randevunuz yarin"),
        ("Sevgili Mehmet bugun gel", "Sevgili <NAME> bugun gel"),
        ("Sn. Musterimiz. kargonuz geldi", "Sn. Musterimiz. kargonuz geldi"),
        ("Degerli musterimiz, fatura hazir", "Degerli musterimiz, fatura hazir"),
        ("Bugun Ankara'ya gidiyorum", "Bugun Ankara'ya gidiyorum"),
    ],
)
def test_mask_honorific_names(text: str, expected: str) -> None:
    assert mask_honorific_names(text) == expected


def test_mask_pii_is_idempotent() -> None:
    once = mask_pii("Tel: 0532 123 45 67")
    assert mask_pii(once) == once
