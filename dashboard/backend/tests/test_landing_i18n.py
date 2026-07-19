"""Factory landing HTML language follows market_code (Mission 1 delivery quality)."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.landing_builder import build_landing_html
from app.factory.landing_i18n import landing_lang_for_market, ui_strings
from app.factory.package_features import resolve_package_features


def _html(market: str, niche: str = "Zahnarztpraxis in Berlin, Termine und Behandlungen") -> str:
    analysis = analyze(niche)
    features = resolve_package_features("business")
    return build_landing_html(
        analysis,
        features=features,
        whatsapp="+491701234567",
        city="Berlin",
        street="Hauptstraße 1",
        market_code=market,
    )


def test_landing_lang_map() -> None:
    assert landing_lang_for_market("DE") == "de"
    assert landing_lang_for_market("AT") == "de"
    assert landing_lang_for_market("GB") == "en"
    assert landing_lang_for_market("UA") == "uk"
    assert landing_lang_for_market("RU") == "ru"
    assert landing_lang_for_market("PL") == "en"


def test_de_landing_chrome_german() -> None:
    html = _html("DE")
    assert 'lang="de"' in html
    assert "Leistungen" in html
    assert "Anfrage senden" in html
    assert "Kundenstimmen" in html
    assert "Impressum" in html


def test_gb_landing_chrome_english() -> None:
    html = _html("GB", "Dental clinic in London, appointments and care")
    assert 'lang="en"' in html
    assert "Services" in html
    assert "Send request" in html
    assert "Reviews" in html
    assert "Privacy" in html
    assert "Leistungen" not in html
    assert "Anfrage senden" not in html


def test_ua_landing_chrome_ukrainian() -> None:
    html = _html("UA", "Стоматологія Київ, запис на прийом")
    assert 'lang="uk"' in html
    assert "Послуги" in html
    assert "Надіслати" in html
    assert "Відгуки" in html
    assert "Конфіденційність" in html


def test_ru_landing_chrome_russian() -> None:
    html = _html("RU", "Стоматология Москва, запись на приём")
    assert 'lang="ru"' in html
    assert "Услуги" in html
    assert "Отправить" in html
    assert "Отзывы" in html


def test_ui_strings_required_keys() -> None:
    for lang in ("de", "en", "uk", "ru"):
        ui = ui_strings(lang)
        assert ui["services"]
        assert ui["contact"]
        assert ui["form_submit"]
        assert ui["legal_a"]
        assert ui["legal_b"]
