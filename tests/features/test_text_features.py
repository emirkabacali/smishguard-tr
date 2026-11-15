import pytest

from smishguard.features.text_features import fired_text_rules

RULE_CASES = {
    "URGENCY_LANGUAGE": (
        [
            "24 saat icinde odemezseniz ceza uygulanacak",
            "Son gun bugun!",
            "HEMEN arayin",
            "Hesabiniz askiya alinmistir",
            "Aksi halde hattiniz kapatilacaktir",
        ],
        ["Yarin saat 10'da gorusuruz", "Hemenlik bir sey yok, sakin ol", "Gunaydin, iyi gunler"],
    ),
    "MONEY_OR_FINE": (
        [
            "Trafik cezaniz islenmistir",
            "Borcunuzu odeyin",
            "Toplam 19,90 TL",
            "Vergi iadeniz hazir",
        ],
        ["Aksam yemege gel", "Odev teslimi yarin", "Tlf numarani at"],
    ),
    "CREDENTIAL_REQUEST": (
        [
            "Sifrenizi girerek blokeyi kaldirin",
            "Kart bilgilerinizi guncelleyin",
            "Size gelen dogrulama kodunu paylasin",
            "TC kimlik numaranizla basvurun",
        ],
        [
            "Dogrulama kodunuz 482913. Bu kodu kimseyle paylasmayin.",
            "Onay kodunuz 1234, kimse ile paylasmayiniz",
            "Kartinizla 120 TL harcama yapildi",
        ],
    ),
    "PRIZE_CLAIM": (
        ["TEBRIKLER! iPhone kazandiniz", "Hediye ceki sizi bekliyor", "Cekilis sonucu aciklandi"],
        ["Maci kazandik!", "Kazanc raporunu gonder", "Sinavi gectin, tebrikler"],
    ),
    "ADDRESS_ISSUE": (
        [
            "Kargonuz adres eksikligi nedeniyle bekliyor",
            "Gonderiniz teslim edilemedi",
            "Paketiniz gumrukte bekliyor",
            "Adresinizi guncelleyin",
        ],
        ["Yeni adresim Kadikoy", "Kargonuz teslim edildi", "Adres: Ataturk Cad. No 5"],
    ),
}

POSITIVE = [(code, text) for code, (pos, _) in RULE_CASES.items() for text in pos]
NEGATIVE = [(code, text) for code, (_, neg) in RULE_CASES.items() for text in neg]


@pytest.mark.parametrize(("code", "text"), POSITIVE)
def test_rule_fires(code: str, text: str) -> None:
    assert code in fired_text_rules(text)


@pytest.mark.parametrize(("code", "text"), NEGATIVE)
def test_rule_does_not_fire(code: str, text: str) -> None:
    assert code not in fired_text_rules(text)


def test_every_text_rule_has_two_positive_and_two_negative_cases() -> None:
    for positives, negatives in RULE_CASES.values():
        assert len(positives) >= 2 and len(negatives) >= 2


@pytest.mark.parametrize("text", ["ÖDEMENİZİ YAPIN", "ödemenizi yapın", "odemenizi yapin"])
def test_matching_ignores_case_and_turkish_letters(text: str) -> None:
    assert "MONEY_OR_FINE" in fired_text_rules(text)


def test_plain_personal_message_fires_nothing() -> None:
    assert fired_text_rules("cnm eve gelirken ekmek alir misin") == []
