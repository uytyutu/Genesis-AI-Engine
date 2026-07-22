"""R3.3 — Section-Aware Content Gate (no LLM)."""

from __future__ import annotations

from app.factory.analyzer import AnalysisResult, analyze
from app.factory.content_gate import (
    evaluate_analysis,
    evaluate_navigation_html,
    nav_label_is_marketing,
    run_content_gate,
    sanitize_analysis,
)
from app.factory.compliance_engine import run_compliance


def _analysis(**kwargs) -> AnalysisResult:
    base = dict(
        niche="beauty",
        template_id="t",
        business_name="Salon Mira",
        headline="Salon Mira — Stil, der zu Ihnen passt",
        subtitle="Haarschnitt · Coloration · Styling",
        services=["Schnitt & Styling", "Coloration", "Maniküre"],
        service_descriptions=("", "", ""),
        cta_label="Termin buchen",
        trust_points=("Premium-Produkte", "Erfahrene Stylisten"),
        about_text="Salon",
        benefits=("Online-Termine", "Individuelle Beratung"),
        hours="Mo–Fr 9–18",
        phone="+491234",
        email="a@b.de",
    )
    base.update(kwargs)
    return AnalysisResult(**base)


def test_beauty_services_pass():
    r = evaluate_analysis(_analysis())
    assert r.passed
    assert all(c.ok for c in r.checks if c.section == "services")


def test_generic_services_fail_for_beauty():
    r = evaluate_analysis(
        _analysis(services=["Beratung", "Umsetzung", "Support", "Lösungen"])
    )
    assert not r.passed
    svc = next(c for c in r.checks if c.id == "services_niche")
    assert not svc.ok
    assert "generic" in svc.detail


def test_sanitize_swaps_niche_defaults():
    bad = _analysis(services=["Beratung", "Umsetzung", "Support"])
    fixed, repairs = sanitize_analysis(bad)
    assert repairs
    assert "Beratung" not in fixed.services
    assert evaluate_analysis(fixed).passed


def test_nav_marketing_forbidden():
    assert nav_label_is_marketing("Geprüft")
    assert nav_label_is_marketing("Lokal")
    assert nav_label_is_marketing("Zuverlässig")
    assert nav_label_is_marketing("Premium-Marken")
    assert not nav_label_is_marketing("Leistungen")
    assert not nav_label_is_marketing("FAQ")


def test_navigation_html_fails_on_marketing_links():
    html = """
    <div class="topbar-links">
      <a href="#x">Geprüft</a>
      <a href="#y">Lokal</a>
      <a class="btn" href="#contact">Termin</a>
    </div>
    """
    check = evaluate_navigation_html(html)
    assert not check.ok


def test_navigation_html_passes_section_links():
    html = """
    <div class="topbar-links">
      <a href="#services">Leistungen</a>
      <a href="#faq">FAQ</a>
      <a class="btn topbar-cta" href="#contact">Termin buchen</a>
    </div>
    """
    check = evaluate_navigation_html(html)
    assert check.ok


def test_dental_benefits_reject_beauty_terms():
    r = evaluate_analysis(
        _analysis(
            niche="dental",
            services=["Prophylaxe", "Füllungen"],
            benefits=("Maniküre inklusive",),
            trust_points=("Coloration",),
        )
    )
    assert not r.passed
    ben = next(c for c in r.checks if c.id == "benefits_niche")
    assert not ben.ok


def test_computer_generic_services_repaired_in_gate():
    bad = _analysis(
        niche="computer",
        headline="PC Neon — PC- & Laptop-Reparatur vor Ort",
        subtitle="Reparatur · Datenrettung",
        services=["Beratung", "Umsetzung", "Support"],
        benefits=("Schnelle Diagnose",),
        trust_points=("Ersatzteile vor Ort",),
    )
    result, fixed = run_content_gate(analysis=bad, auto_repair=True)
    assert fixed is not None
    assert "Beratung" not in fixed.services
    assert result.passed


def test_compliance_blocks_failed_content_gate():
    html = '<div class="topbar-links"><a href="#s">Leistungen</a></div>'
    meta = {
        "niche": "beauty",
        "content_gate": {
            "engine_id": "content_gate_v1",
            "passed": False,
            "failures": ["services:services_niche — generic_services:Beratung"],
        },
    }
    cr = run_compliance(html, meta=meta, assets_dir=None)
    assert not cr.passed
    assert any(c.id == "section_aware_content" and not c.ok for c in cr.checks)


def test_live_analyzer_niches_not_generic_services():
    specs = [
        ("auto", "Autowerkstatt Nord — Inspektion, Reifen, Diagnose in Hamburg"),
        ("beauty", "Salon Mira Berlin — Haarschnitt, Farbe, Pflege"),
        ("computer", "PC-Service Neon — Reparatur, Netzwerke in Düsseldorf"),
        ("dental", "SmileCare Berlin — Zahnarztpraxis, Prophylaxe"),
    ]
    for expect, desc in specs:
        analysis = analyze(desc)
        assert analysis.niche == expect, (expect, analysis.niche)
        result, fixed = run_content_gate(analysis=analysis, auto_repair=True)
        assert fixed is not None
        assert result.passed, (expect, result.failures)
        assert not any(
            s.lower() in {"beratung", "umsetzung", "support"} for s in fixed.services
        )
