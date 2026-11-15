import pytest

from smishguard.features.urls import extract_urls, parse_url


def hosts(text: str) -> list[str]:
    return [url.host for url in extract_urls(text)]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Tiklayin: https://ptt-kargo.xyz/takip?id=1", ["ptt-kargo.xyz"]),
        ("Defanged: hxxps://ptt-kargo[.]xyz/takip", ["ptt-kargo.xyz"]),
        ("www.turkiye.gov.tr adresinden", ["www.turkiye.gov.tr"]),
        ("Bare domain hgs-ceza.click/odeme ile ode.", ["hgs-ceza.click"]),
        ("IP link http://185.62.13.77/kargo", ["185.62.13.77"]),
        ("Kisaltma: bit.ly/3xArAs9!", ["bit.ly"]),
        ("GNCTEKLIF.COM adresine bak", ["gncteklif.com"]),
        ("iki link https://a-b.xyz ve www.c.com.tr", ["a-b.xyz", "www.c.com.tr"]),
    ],
)
def test_extract_urls_finds_links(text: str, expected: list[str]) -> None:
    assert hosts(text) == expected


@pytest.mark.parametrize(
    "text",
    [
        "Tarih 10.03.2011 saat 20.09",
        "Fiyat 1.401,67 TL",
        "Paket geldi.Bizi tercih ettiginiz icin tesekkurler",
        "ben de geldim.de bakalim",  # ".de" is a real TLD but not accepted for bare domains
        "mail adresim ali@example.com",
        "T.C. Saglik Bakanligi",
    ],
)
def test_extract_urls_ignores_non_links(text: str) -> None:
    assert extract_urls(text) == []


def test_duplicate_hosts_reported_once() -> None:
    assert hosts("https://a.xyz/1 ve https://a.xyz/2") == ["a.xyz"]


def test_parse_url_splits_hostname() -> None:
    url = parse_url("https://login.ptt-kargo.com.tr/x")
    assert url is not None
    assert (url.subdomain, url.domain, url.suffix) == ("login", "ptt-kargo", "com.tr")
    assert url.registered_domain == "ptt-kargo.com.tr"
    assert url.tld == "tr"


def test_parse_url_handles_ip_port_and_credentials() -> None:
    url = parse_url("http://user:pw@10.0.0.1:8080/a")
    assert url is not None and url.is_ip
    assert url.registered_domain == "10.0.0.1"


def test_parse_url_rejects_unknown_suffix() -> None:
    assert parse_url("http://intranet.localdomain123") is None
