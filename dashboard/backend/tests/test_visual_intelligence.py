"""Gen1 Visual Intelligence Engine — Style · Asset · Motion · Quality Gate ≥ 90."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.analyzer import analyze
from app.factory.compliance_engine import run_compliance
from app.factory.composer_engine import compose_landing
from app.factory.package_features import resolve_package_features
from app.factory.visual_intelligence import (
    VISUAL_QUALITY_THRESHOLD,
    AssetManager,
    resolve_style,
    resolve_visual_plan,
    run_visual_quality_gate,
    visual_intelligence_ready,
)
from app.factory.visual_intelligence.engine import apply_visual_plan_to_html
from app.factory.visual_intelligence.motion_engine import resolve_motion_tier
from app.factory.visual_intelligence.style_engine import components_for_surface
from app.integration.platform_global_analytics import build_gen1_readiness


def test_style_engine_niche_profiles():
    law = resolve_style("law")
    assert "corporate" in law.mood or "strict" in law.mood
    rest = resolve_style("restaurant")
    assert "warm" in rest.mood.lower() or "atmospheric" in rest.mood.lower()
    beauty = resolve_style("salon")  # alias
    assert beauty.niche_id == "beauty"
    auto = resolve_style("autoservice")
    assert auto.niche_id == "auto"
    dental = resolve_style("zahnarzt")
    assert dental.niche_id == "dental"
    fashion = resolve_style("clothing")
    assert fashion.niche_id == "fashion"
    it = resolve_style("it")
    assert it.niche_id == "computer"


def test_surface_components_differ():
    web = components_for_surface("website")
    store = components_for_surface("store")
    assert "services" in web and "team" in web
    assert "catalog" in store and "checkout" in store
    assert "services" not in store


def test_motion_tiers():
    basic = resolve_motion_tier(requested="basic", surface="website")
    assert basic.tier == "basic"
    assert "fade" in basic.features
    assert basic.allow_heavy_libs is False
    biz = resolve_motion_tier(requested="business", surface="website")
    assert "parallax" in biz.features
    prem = resolve_motion_tier(requested="premium", surface="website")
    assert prem.allow_heavy_libs is False  # client ZIP contract
    plat = resolve_motion_tier(requested="premium", surface="platform")
    assert plat.allow_heavy_libs is True


def test_asset_manager_quality_floor(tmp_path: Path):
    mgr = AssetManager(tmp_path)
    pick = mgr.pick(role="hero", niche_id="law")
    assert pick.quality_score >= 70
    assert pick.source in {"virtus_library", "licensed_free", "client_upload"}
    # Cache reuse
    again = mgr.pick(role="hero", niche_id="law")
    assert again.cached is True or again.id == pick.id


def test_visual_plan_and_quality_gate():
    plan = resolve_visual_plan(
        niche_id="dental", surface="website", package_id="business"
    )
    assert plan.engine_id.startswith("visual_intelligence")
    assert plan.style.niche_id == "dental"
    html = apply_visual_plan_to_html(
        """<!doctype html><html><head>
<meta name="viewport" content="width=device-width">
<link href="https://fonts.googleapis.com/css2?family=Fraunces&display=swap" rel="stylesheet">
<style>
:root { --p: #0ea5e9; --acc: #0369a1; --ink: #0f172a; --surface: #f8fafc; --font-display: Fraunces; }
@media (max-width: 768px) { .x { display:block } }
@media (prefers-reduced-motion: reduce) { * { animation: none } }
</style></head>
<body data-niche="dental" data-hero-layout="A">
<header class="hero"><h1>Clinic</h1></header>
<section class="section">A</section>
<section class="section">B</section>
<img src="a.jpg" alt="Care" loading="lazy">
</body></html>""",
        plan,
    )
    assert 'data-vie-engine="' in html
    assert "vie-motion-" in html
    result = run_visual_quality_gate(
        html,
        meta={
            "niche": "dental",
            "surface": "website",
            "primary": plan.tokens.primary,
            "accent": plan.tokens.accent,
            "ink": plan.tokens.ink,
            "surface_token": plan.tokens.surface,
            "visual_plan": True,
            "assets": [a.as_dict() for a in plan.assets if a.quality_score >= 70],
        },
    )
    assert result.score >= VISUAL_QUALITY_THRESHOLD
    assert result.passed


def test_compose_landing_passes_visual_compliance():
    html = compose_landing(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
        motion_level="css",
    ).html
    assert 'data-vie-engine="' in html
    result = run_compliance(
        html,
        meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
    )
    assert result.passed, result.failures
    assert result.visual_quality is not None
    assert result.visual_quality.passed
    assert result.visual_quality.score >= 90


def test_visual_intelligence_ready_and_gen1(tmp_path: Path):
    assert visual_intelligence_ready(tmp_path) is True
    ready = build_gen1_readiness(tmp_path)
    item = next(i for i in ready["items"] if i["id"] == "visual_engine")
    assert item["status"] == "done"
