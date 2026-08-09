"""Business Visual Pack + Visual Quality Gate auditor."""

from __future__ import annotations

from app.factory.visual_intelligence.business_visual_pack import (
    SSOT_RULE,
    audit_html_visual_slots,
    ensure_business_kpi_ui,
)


def test_ssot_rule_mentions_empty_zones():
    assert "empty decorative zones" in SSOT_RULE.lower() or "empty decorative" in SSOT_RULE


def test_business_kpi_fill_qualitative():
    ui = ensure_business_kpi_ui({}, package_id="business", niche="law")
    assert ui["stats_v1"]
    assert "Jahre" not in ui["stats_v1"]  # no fabricated years
    assert ensure_business_kpi_ui({}, package_id="basic") == {}


def test_audit_empty_hero_orb_fails():
    html = """
    <header class="hero hero-layout-E" data-hero-layout="E">
      <figure class="hero-E-orb"><span class="hero-E-ring"></span></figure>
    </header>
    """
    report = audit_html_visual_slots(html, package_id="business")
    assert report.ok is False
    assert any(f.slot == "hero_media" for f in report.findings)


def test_audit_filled_hero_with_kpi_passes():
    html = """
    <header class="hero hero-layout-E has-photo" data-hero-layout="E">
      <figure class="hero-E-orb">
        <img src="assets/hero.jpg" alt="x">
      </figure>
      <div class="trust-row"><span class="trust-pill">Lokal</span></div>
      <aside aria-label="stats">
        <div class="hero-kpi"><strong>Klar</strong><span>Angebot</span></div>
      </aside>
    </header>
    """
    report = audit_html_visual_slots(html, package_id="business")
    assert report.ok is True
    assert report.score >= 90


def test_basic_skips_gate():
    html = '<header class="hero"><figure class="hero-E-orb"></figure></header>'
    report = audit_html_visual_slots(html, package_id="basic")
    assert report.ok is True
