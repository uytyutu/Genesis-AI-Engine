"""Factory niche quality: no partner-chrome; client services feed into build."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.content_gate import evaluate_analysis, run_content_gate
from app.factory.package_features import apply_order_services, normalize_services_list


def test_generic_preset_never_partner_vor_ort():
    analysis = analyze("Firma Nordlicht — regionale Dienstleistungen in Hamburg")
    assert "partner vor ort" not in analysis.headline.lower()
    assert "helfen ihrem" not in analysis.headline.lower()
    result, fixed = run_content_gate(analysis=analysis, auto_repair=True)
    assert fixed is not None
    assert "partner vor ort" not in fixed.headline.lower()
    assert result.passed


def test_partner_headline_fails_gate_even_for_generic():
    from app.factory.analyzer import AnalysisResult

    bad = AnalysisResult(
        niche="generic",
        template_id="t",
        business_name="Nordlicht",
        headline="Nordlicht — Ihr Partner vor Ort",
        subtitle="Wir helfen Ihrem Unternehmen.",
        services=["Erstgespräch", "Leistungsangebot"],
        service_descriptions=("", ""),
        cta_label="Anfrage senden",
        trust_points=("Schnell",),
        about_text="x",
        benefits=("Klar", "Fair"),
        hours="Mo–Fr",
        phone="+49",
        email="a@b.de",
    )
    r = evaluate_analysis(bad)
    voice = next(c for c in r.checks if c.id == "hero_niche_voice")
    assert not voice.ok


def test_apply_order_services_overrides_titles():
    base = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege")
    assert base.niche == "beauty"
    updated = apply_order_services(
        base,
        ["Balayage", "Damenhaarschnitt", "Wimpernlifting", "Brautstyling"],
    )
    assert updated.services[0] == "Balayage"
    assert "Damenhaarschnitt" in updated.services
    assert len(updated.services) == 4


def test_normalize_services_list_from_string():
    assert normalize_services_list("Ölwechsel\nDiagnose\nReifen") == [
        "Ölwechsel",
        "Diagnose",
        "Reifen",
    ]


def test_niche_hint_when_description_generic():
    analysis = analyze(
        "Firma Helios — Kunden in München",
        niche_hint="dental",
    )
    assert analysis.niche == "dental"
    assert "zahn" in analysis.headline.lower() or "prophylaxe" in " ".join(analysis.services).lower()


def test_fashion_not_partner_chrome():
    analysis = analyze("Atelier Mira Boutique Mode Berlin — Kleider und Styling")
    assert analysis.niche == "fashion"
    assert "partner vor ort" not in analysis.headline.lower()
    result, fixed = run_content_gate(analysis=analysis, auto_repair=True)
    assert result.passed
    assert fixed is not None
    assert fixed.niche == "fashion"
