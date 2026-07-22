"""R3.4.1.2 — Composer uses Market Profile SSOT."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.composer_engine import compose_landing, resolve_composition_plan
from app.factory.market_profile import resolve
from app.factory.package_features import resolve_package_features


def test_resolve_composition_plan_uses_market_profile():
    de = resolve_composition_plan(
        business_name="Salon Mira",
        package_id="business",
        market_code="DE",
        niche_id="beauty",
    )
    gb = resolve_composition_plan(
        business_name="Salon Mira",
        package_id="business",
        market_code="GB",
        niche_id="beauty",
    )
    assert de.market_code == "DE"
    assert gb.market_code == "GB"
    assert de.currency == "EUR" and gb.currency == "GBP"
    assert de.language == "de" and gb.language == "en"
    assert de.default_cta == resolve("DE").default_cta
    assert gb.default_cta == resolve("GB").default_cta
    assert de.default_cta != gb.default_cta
    assert de.locale == "de_DE" and gb.locale == "en_GB"


def test_compose_landing_de_vs_gb_via_profile_only():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    de = compose_landing(analysis, features=features, market_code="DE")
    gb = compose_landing(analysis, features=features, market_code="GB")

    assert de.market_profile["market_code"] == "DE"
    assert gb.market_profile["market_code"] == "GB"
    assert de.market_profile["currency"] == "EUR"
    assert gb.market_profile["currency"] == "GBP"
    assert de.market_profile["default_cta"] == "Termin buchen"
    assert gb.market_profile["default_cta"] == "Book Now"
    assert de.plan.currency == de.market_profile["currency"]
    assert gb.plan.currency == gb.market_profile["currency"]
    # Composer applies profile CTA onto analysis (Landing Builder may still
    # localize chrome in R3.4.1.4 — HTML CTA is not this slice's contract).
    assert de.analysis is not None and de.analysis.cta_label == "Termin buchen"
    assert gb.analysis is not None and gb.analysis.cta_label == "Book Now"
    assert de.plan.default_cta != gb.plan.default_cta
    assert de.plan.locale != gb.plan.locale
    # Market code reaches HTML chrome path without Composer inventing country rules
    assert 'data-market="DE"' in de.html or 'lang="de"' in de.html
    assert 'data-market="GB"' in gb.html or 'lang="en"' in gb.html

def test_composer_has_no_resolve_market_design_import():
    import app.factory.composer_engine as ce
    import inspect

    src = inspect.getsource(ce)
    assert "resolve_market_design" not in src
    assert "resolve_market_profile" in src or "market_profile" in src
