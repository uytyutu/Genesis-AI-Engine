"""Factory landing HTML language follows market_code (Mission 1 delivery quality).

R3.4.1.R: after R3.3 Navigation Gate, header is section links + one CTA only —
do not assert Reviews/Kundenstimmen in nav (those belong in body sections when enabled).
"""

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
    assert "Impressum" in html
    # Navigation Gate: marketing/review labels are not header chrome
    assert 'href="#reviews"' not in html.split('<nav class="topbar"', 1)[-1].split("</nav>", 1)[0]


def test_gb_landing_chrome_english() -> None:
    html = _html("GB", "Dental clinic in London, appointments and care")
    assert 'lang="en"' in html
    assert "Services" in html
    assert "Send request" in html
    assert "Privacy" in html
    assert "Leistungen" not in html
    assert "Anfrage senden" not in html
    nav = html.split('<nav class="topbar"', 1)[-1].split("</nav>", 1)[0]
    assert "Reviews" not in nav


def test_ua_landing_chrome_ukrainian() -> None:
    html = _html("UA", "Стоматологія Київ, запис на прийом")
    assert 'lang="uk"' in html
    assert "Послуги" in html
    assert "Надіслати" in html
    assert "Конфіденційність" in html
    nav = html.split('<nav class="topbar"', 1)[-1].split("</nav>", 1)[0]
    assert "Відгуки" not in nav


def test_ru_landing_chrome_russian() -> None:
    html = _html("RU", "Стоматология Москва, запись на приём")
    assert 'lang="ru"' in html
    assert "Услуги" in html
    assert "Отправить" in html
    nav = html.split('<nav class="topbar"', 1)[-1].split("</nav>", 1)[0]
    assert "Отзывы" not in nav


def test_ui_strings_required_keys() -> None:
    for lang in ("de", "en", "uk", "ru"):
        ui = ui_strings(lang)
        assert ui["services"]
        assert ui["contact"]
        assert ui["form_submit"]
        assert ui["legal_a"]
        assert ui["legal_b"]
