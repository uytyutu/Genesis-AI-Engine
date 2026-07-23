"""Commercial UI Audit — no empty heroes, niche CTAs for launch niches × packages."""

from __future__ import annotations

import re

import pytest

from app.factory.analyzer import analyze
from app.factory.composer_engine import compose_landing
from app.factory.hero_integrity import hero_html_has_empty_blocks
from app.factory.package_features import resolve_package_features

_LAUNCH_BRIEFS = (
    (
        "cleaning",
        "Clean Profi Dresden — Gebäudereinigung und Büroreinigung für Firmen.",
        ("Kostenloses Angebot", "Reinigung anfragen", "Angebot"),
        ("Termin buchen", "Записаться на приём", "Book appointment"),
    ),
    (
        "auto_ankauf",
        "Auto Ankauf Nord — wir kaufen Ihr Auto, Autoankauf mit fairer Bewertung.",
        ("Kostenlose Bewertung", "Fahrzeug verkaufen", "Bewertung"),
        ("Termin buchen", "Записаться на приём", "Termin vereinbaren"),
    ),
    (
        "law",
        "Steuerkanzlei Weber — Steuerberater für Selbstständige und GmbH.",
        ("Beratung anfragen", "Beratung", "Erstgespräch"),
        ("Termin buchen", "Записаться на приём"),
    ),
)

_PACKAGES = ("basic", "business", "premium")


@pytest.mark.parametrize("pkg", _PACKAGES)
@pytest.mark.parametrize("niche_key,brief,cta_ok,cta_bad", _LAUNCH_BRIEFS)
def test_commercial_ui_audit_nine_combos(niche_key, brief, cta_ok, cta_bad, pkg):
    analysis = analyze(brief)
    assert analysis.niche == niche_key
    composed = compose_landing(
        analysis,
        features=resolve_package_features(pkg),
        market_code="DE",
    )
    html = composed.html
    assert composed.analysis is not None

    issues = hero_html_has_empty_blocks(html)
    assert not issues, f"{niche_key}/{pkg}: {issues}"

    h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.I | re.S)
    assert h1 and h1.group(1).strip(), f"{niche_key}/{pkg}: empty h1"
    lead = re.search(r'<p[^>]*class="[^"]*lead[^"]*"[^>]*>(.*?)</p>', html, re.I | re.S)
    assert lead and lead.group(1).strip(), f"{niche_key}/{pkg}: empty subtitle"

    cta = composed.analysis.cta_label
    assert cta and cta.strip()
    assert any(tok.lower() in cta.lower() for tok in cta_ok), (
        f"{niche_key}/{pkg}: CTA {cta!r} not niche-specific"
    )
    for bad in cta_bad:
        assert bad.lower() not in cta.lower(), f"{niche_key}/{pkg}: forbidden CTA {bad!r} in {cta!r}"
        assert bad not in html

    # Service titles must appear as real copy, not empty shells
    import html as html_lib

    for svc in composed.analysis.services[:4]:
        assert svc.strip()
        assert svc in html or html_lib.escape(svc) in html


def test_hero_integrity_fills_empty_analysis():
    from dataclasses import replace

    from app.factory.hero_integrity import ensure_analysis_hero

    bare = replace(
        analyze("Clean Profi Reinigung Berlin"),
        headline="",
        subtitle="",
        cta_label="",
        services=[],
    )
    filled = ensure_analysis_hero(bare)
    assert filled.headline.strip()
    assert filled.subtitle.strip()
    assert filled.cta_label.strip()
    assert filled.services
