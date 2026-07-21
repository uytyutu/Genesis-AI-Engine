"""R2.2b-intl — International Design Engine for Path A markets."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.landing_builder import build_landing_html
from app.factory.landing_i18n import landing_lang_for_market, ui_strings
from app.factory.market_design import (
    MARKET_DESIGN_PROFILES,
    assert_localization_hygiene,
    resolve_market_design,
)
from app.factory.package_features import resolve_package_features


def test_market_design_profiles_diverge():
    de = resolve_market_design("DE")
    es = resolve_market_design("ES")
    fr = resolve_market_design("FR")
    assert de.density != fr.density or de.measure_ch != fr.measure_ch
    assert de.accent_filter != es.accent_filter
    assert de.phone_placeholder.startswith("+49")
    assert es.phone_placeholder.startswith("+34")
    assert set(MARKET_DESIGN_PROFILES) >= {"DE", "AT", "FR", "ES", "NL"}


def test_fr_es_nl_use_native_chrome_not_english():
    assert landing_lang_for_market("FR") == "fr"
    assert landing_lang_for_market("ES") == "es"
    assert landing_lang_for_market("NL") == "nl"
    fr = ui_strings("fr")
    es = ui_strings("es")
    assert fr["contact"] == "Contact"
    assert "Contacto" in es["contact"] or es["contact"] == "Contacto"
    assert "Services" in fr["services"] or fr["services"] == "Services"
    assert "Lorem" not in fr["mid_cta_btn"]
    assert fr["legal_a"] == "Mentions légales"
    assert es["legal_a"] == "Aviso legal"


def test_de_vs_es_html_differs_in_language_and_design():
    brief = "Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."
    de_html = build_landing_html(
        analyze(brief),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    es_html = build_landing_html(
        analyze(brief),
        features=resolve_package_features("business"),
        market_code="ES",
    )
    assert 'data-market="DE"' in de_html
    assert 'data-market="ES"' in es_html
    assert 'data-density="compact"' in de_html
    assert 'lang="de"' in de_html
    assert 'lang="es"' in es_html
    assert "hreflang=\"de-DE\"" in de_html
    assert "hreflang=\"es-ES\"" in es_html
    assert "og:locale" in de_html and "de_DE" in de_html
    assert "og:locale" in es_html and "es_ES" in es_html
    assert "--market-measure:" in de_html
    assert de_html.split("--market-measure:")[1].split(";")[0].strip() != es_html.split(
        "--market-measure:"
    )[1].split(";")[0].strip() or de_html.split("--market-section-pad:")[1].split(";")[
        0
    ].strip() != es_html.split("--market-section-pad:")[1].split(";")[0].strip()
    # Spanish chrome / niche, not English stubs
    assert "Contacto" in es_html or "Pedir cita" in es_html or "Servicios" in es_html
    assert "Leistungen" in de_html or "Kontakt" in de_html
    assert_localization_hygiene(de_html)
    assert_localization_hygiene(es_html)


def test_market_rebuild_is_deterministic():
    brief = "Autowerkstatt Schmidt in Berlin. Inspektion."
    a = build_landing_html(
        analyze(brief),
        features=resolve_package_features("business"),
        market_code="FR",
    )
    b = build_landing_html(
        analyze(brief),
        features=resolve_package_features("business"),
        market_code="FR",
    )
    assert a == b
    assert 'data-market="FR"' in a
    assert 'lang="fr"' in a
    assert "Prendre" in a or "Services" in a or "Contact" in a


def test_at_uses_german_language_with_warm_design():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Wien. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="AT",
    )
    assert 'data-market="AT"' in html
    assert 'lang="de"' in html
    assert "#faf7f2" in html or "Austria" in html or "--market-surface:" in html
