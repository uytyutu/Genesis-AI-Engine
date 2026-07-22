"""R3.4.1.3 — Footer consumes MarketProfile (no country if/else)."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.composer_engine import compose_landing
from app.factory.layout_variants import compose_footer
from app.factory.market_profile import legal_link_pairs, resolve
from app.factory.package_features import resolve_package_features


def test_compose_footer_from_profile_de_vs_gb():
    de = resolve("DE")
    gb = resolve("GB")
    de_html = compose_footer(
        variant="legal",
        business_name="Salon Mira",
        ui={},
        market_profile=de,
    )
    gb_html = compose_footer(
        variant="legal",
        business_name="Salon Mira",
        ui={},
        market_profile=gb,
    )
    assert 'data-legal-keys="impressum,datenschutz"' in de_html
    assert 'data-legal-keys="privacy,contact"' in gb_html
    assert "impressum.html" in de_html
    assert "datenschutz.html" in de_html
    assert "privacy.html" in gb_html
    assert "#contact" in gb_html
    assert "Impressum" in de_html
    assert "Privacy" in gb_html
    # Footer must not invent DE fallback when profile is GB
    assert "impressum.html" not in gb_html


def test_footer_accepts_composition_result_dict_without_resolve():
    profile = resolve("US").as_dict()
    html = compose_footer(
        variant="compact",
        business_name="Acme",
        ui={},
        market_profile=profile,
    )
    assert 'data-market="US"' in html
    assert "privacy.html" in html
    assert "terms.html" in html
    assert "Get Quote" not in html  # CTA is Composer chrome; footer uses legal keys


def test_legal_link_pairs_follow_profile_only():
    de_pairs = legal_link_pairs(resolve("DE"))
    gb_pairs = legal_link_pairs(resolve("GB"))
    assert [h for _, h in de_pairs] == ["impressum.html", "datenschutz.html"]
    assert [h for _, h in gb_pairs] == ["privacy.html", "#contact"]


def test_compose_landing_footer_differs_by_market_profile():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    de = compose_landing(analysis, features=features, market_code="DE")
    gb = compose_landing(analysis, features=features, market_code="GB")

    de_foot = re.search(r"<footer\b.*?</footer>", de.html, flags=re.I | re.S)
    gb_foot = re.search(r"<footer\b.*?</footer>", gb.html, flags=re.I | re.S)
    assert de_foot and gb_foot
    assert "impressum.html" in de_foot.group(0)
    assert "privacy.html" in gb_foot.group(0)
    assert de.market_profile["legal_footer_keys"] == ["impressum", "datenschutz"] or (
        tuple(de.market_profile["legal_footer_keys"]) == ("impressum", "datenschutz")
    )
    assert tuple(gb.market_profile["legal_footer_keys"]) == ("privacy", "contact")
    # Same profile object path: footer keys match CompositionResult.market_profile
    assert 'data-legal-keys="impressum,datenschutz"' in de_foot.group(0)
    assert 'data-legal-keys="privacy,contact"' in gb_foot.group(0)


def test_compose_footer_has_no_country_if_else():
    import ast
    import inspect
    from app.factory import layout_variants as lv

    src = inspect.getsource(lv.compose_footer) + "\n" + inspect.getsource(lv._footer_legal_html)
    assert 'market == "DE"' not in src
    assert "if market ==" not in src
    tree = ast.parse(src)
    calls = [
        n.func.id
        for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
    ]
    assert "resolve" not in calls
    assert "resolve_market_profile" not in calls
    assert "resolve_market_design" not in calls