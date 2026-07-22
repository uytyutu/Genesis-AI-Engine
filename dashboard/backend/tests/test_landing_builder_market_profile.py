"""R3.4.1.4 — Landing Builder consumes MarketProfile from Composer."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.composer_engine import compose_landing
from app.factory.landing_builder import build_landing_html
from app.factory.market_profile import resolve
from app.factory.package_features import resolve_package_features


def test_landing_builder_uses_profile_cta_and_footer():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    de_p = resolve("DE")
    gb_p = resolve("GB")
    # Simulate Composer: CTA already from profile
    from dataclasses import replace

    de_a = replace(analysis, cta_label=de_p.default_cta)
    gb_a = replace(analysis, cta_label=gb_p.default_cta)
    de_html = build_landing_html(
        de_a, features=features, market_code="DE", market_profile=de_p
    )
    gb_html = build_landing_html(
        gb_a, features=features, market_code="GB", market_profile=gb_p
    )
    assert "Termin buchen" in de_html
    assert "Book Now" in gb_html
    assert "Contact us" not in gb_html  # localize_analysis must not win over profile CTA
    assert "impressum.html" in de_html
    assert "privacy.html" in gb_html
    assert 'lang="de"' in de_html
    assert 'lang="en"' in gb_html
    assert 'data-legal-keys="impressum,datenschutz"' in de_html
    assert 'data-legal-keys="privacy,contact"' in gb_html


def test_compose_landing_no_footer_post_replace_needed():
    """Composer must not re.sub footer after build — LB emits profile footer."""
    import inspect
    from app.factory import composer_engine as ce

    src = inspect.getsource(ce.compose_landing)
    assert "re.sub" not in src
    assert "market_profile=profile" in src

    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    features = resolve_package_features("business")
    de = compose_landing(analysis, features=features, market_code="DE")
    gb = compose_landing(analysis, features=features, market_code="GB")
    assert de.analysis is not None and de.analysis.cta_label == "Termin buchen"
    assert gb.analysis is not None and gb.analysis.cta_label == "Book Now"
    assert "Termin buchen" in de.html
    assert "Book Now" in gb.html
    de_foot = re.search(r"<footer\b.*?</footer>", de.html, flags=re.I | re.S)
    gb_foot = re.search(r"<footer\b.*?</footer>", gb.html, flags=re.I | re.S)
    assert de_foot and gb_foot
    assert "impressum.html" in de_foot.group(0)
    assert "privacy.html" in gb_foot.group(0)
    assert de.plan.locale == "de_DE"
    assert gb.plan.locale == "en_GB"
    assert de.plan.currency == "EUR"
    assert gb.plan.currency == "GBP"


def test_landing_builder_legacy_without_profile_still_works():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    html = build_landing_html(
        analysis, features=resolve_package_features("basic"), market_code="DE"
    )
    assert "<footer" in html
    assert "impressum.html" in html or "Impressum" in html


def test_landing_builder_profile_path_has_no_resolve_call():
    import ast
    import inspect
    from app.factory import landing_builder as lb

    src = inspect.getsource(lb.build_landing_html)
    tree = ast.parse(src)
    # Must not call market_profile.resolve inside LB
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "resolve":
                raise AssertionError("build_landing_html must not call resolve()")
            if isinstance(node.func, ast.Attribute) and node.func.attr in (
                "resolve_market_profile",
            ):
                raise AssertionError("LB must not re-resolve MarketProfile")
