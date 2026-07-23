"""R3.4.2.3 — Market expansion via Registry only (FR/NL/AT/ES)."""

from __future__ import annotations

import inspect

from app.factory.composer_engine import compose_landing
from app.factory.market_profile import list_market_codes, resolve
from app.factory.market_registry import DEFAULT_REGISTRY
from app.factory.package_features import resolve_package_features
from app.factory.analyzer import analyze

_EXPANDED = ("DE", "GB", "US", "UA", "FR", "NL", "AT", "ES")


def test_expanded_markets_registered():
    codes = list_market_codes()
    for code in _EXPANDED:
        assert code in codes
        assert DEFAULT_REGISTRY.get(code) is not None
        assert resolve(code).market_code == code


def test_new_markets_profile_fields():
    fr = resolve("FR")
    assert fr.language == "fr" and fr.currency == "EUR"
    assert fr.default_cta == "Prendre rendez-vous"
    assert fr.legal_footer_keys == ("mentions_legales", "confidentialite")

    nl = resolve("NL")
    assert nl.language == "nl" and nl.default_cta == "Afspraak maken"

    at = resolve("AT")
    assert at.language == "de" and at.locale == "de_AT"
    assert at.legal_footer_keys == ("impressum", "datenschutz")

    es = resolve("ES")
    assert es.language == "es" and es.default_cta == "Pedir cita"
    assert "privacidad.html" in es.legal_page_slugs


def test_expansion_did_not_change_composer_landing_footer_source():
    """Factory logic files must not gain country branches for FR/NL/AT/ES."""
    for mod_name in (
        "app.factory.composer_engine",
        "app.factory.landing_builder",
        "app.factory.layout_variants",
    ):
        src = inspect.getsource(__import__(mod_name, fromlist=["*"]))
        for needle in ('"FR"', '"NL"', '"AT"', '"ES"', "if market =="):
            # layout_variants may mention nothing; composer must not hardcode new markets
            if needle == "if market ==":
                assert needle not in src, mod_name
            elif mod_name != "app.factory.layout_variants":
                # allow no hardcoded new market codes in Composer/LB
                if needle in ('"FR"', '"NL"', '"AT"', '"ES"'):
                    assert needle not in src, f"{mod_name} must not hardcode {needle}"


def test_compose_landing_works_for_new_markets_via_profile_only():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    for code in ("FR", "NL", "AT", "ES"):
        p = resolve(code)
        result = compose_landing(analysis, features=features, market_code=code)
        assert result.plan.market_code == code
        assert result.plan.default_cta == p.default_cta
        assert result.plan.language == p.language
        assert p.default_cta in result.html or result.analysis.cta_label in result.html
        assert f'lang="{p.language}"' in result.html


def test_verify_table_eight_markets():
    rows = []
    for code in _EXPANDED:
        p = resolve(code)
        rows.append(
            {
                "market": code,
                "language": p.language,
                "locale": p.locale,
                "currency": p.currency,
                "cta": p.default_cta,
                "legal_keys": ", ".join(p.legal_footer_keys),
            }
        )
    assert len(rows) == 8
    assert {r["market"] for r in rows} == set(_EXPANDED)
