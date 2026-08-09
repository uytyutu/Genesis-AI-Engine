"""Digital Creative Studio — composition library + art director."""

from __future__ import annotations

from app.factory.design_dna.art_director import run_digital_creative_studio
from app.factory.design_dna.composition_library import (
    COMPOSITION_LIBRARY,
    is_predictable_funnel,
    list_compositions,
)


def test_composition_library_has_50_plus():
    assert len(COMPOSITION_LIBRARY) >= 50
    assert len(list_compositions()) >= 50


def test_predictable_funnel_detected():
    assert is_predictable_funnel(
        ("info", "stats", "services", "mid_cta", "benefits", "trust")
    )
    assert not is_predictable_funnel(
        ("about", "gallery", "mid_cta", "services", "trust", "contact")
    )


def test_premium_psychology_picks_anti_predictable():
    studio = run_digital_creative_studio(
        business_name="Praxis Klarheit",
        niche_id="psychology",
        package_id="premium",
        diversity_salt="unit-test-1",
    )
    assert studio.chosen is not None
    assert studio.owner_review == "PENDING_OWNER"
    assert studio.generation_status in ("OK_TO_BUILD", "FAIL_TEMPLATE", "REBUILD")
    assert not is_predictable_funnel(studio.layout_profile.section_order)
    assert studio.hero_layout in ("B", "D", "F")
    assert studio.dna is not None
    assert studio.dna.composition == studio.chosen.composition.id
    assert len(studio.variants_considered) >= 5
    assert "owner_preview" in studio.pipeline
    assert "creative_theme" in studio.pipeline
    assert studio.creative_identity is not None
    assert studio.creative_identity.title
    assert studio.brand_dna is not None
    assert studio.brand_dna.creative_theme
    assert "studio_era" in studio.philosophy or studio.era.startswith("Virtus Core Studio")
    assert studio.brand_dna is not None
    assert studio.observatory is not None
    assert studio.studio_approach is not None
    assert studio.taste is not None
    assert studio.law_1.get("action") in ("CONTINUE", "REBUILD")
    assert "why" in studio.why_hero_exists.lower() or "Hero" in studio.why_hero_exists
    assert studio.scene_sequence
    assert studio.creative_review in ("PASS_INTERNAL", "FAIL_REBUILD", "PENDING")
    assert studio.owner_review == "PENDING_OWNER"
    assert studio.product_noun.lower().startswith("digital experience")


def test_design_observatory_psychology():
    from app.factory.design_dna.design_observatory import observe_niche

    brief = observe_niche("psychology")
    assert brief.era.startswith("2026")
    text = brief.creative_brief().lower()
    assert "invent" in text or "original" in text
    assert "never copy" in text or "never copy pixels" in text
    assert brief.first_screen
    assert any("ladder" in n.lower() or "clone" in n.lower() or "constructor" in n.lower() for n in brief.never)


def test_taste_engine_rejects_constructor_ladder():
    from app.factory.design_dna.taste_engine import evaluate_taste

    bad = evaluate_taste(
        predictable_funnel=True,
        generation_status="FAIL_TEMPLATE",
        package_id="premium",
    )
    assert bad.rebuild is True
    assert bad.verdict == "FAIL_TASTE"


def test_studio_approaches_exist():
    from app.factory.design_dna.design_approaches import (
        DESIGN_APPROACHES,
        choose_studio_approach,
    )

    assert "luxury" in DESIGN_APPROACHES
    assert "scandinavian" in DESIGN_APPROACHES
    assert "editorial" in DESIGN_APPROACHES
    assert "tech_saas" in DESIGN_APPROACHES
    assert "boutique" in DESIGN_APPROACHES
    a = choose_studio_approach(niche_id="psychology", package_id="premium", diversity_salt="t")
    assert a.id in DESIGN_APPROACHES


def test_law_1_rebuild_on_regression():
    from app.factory.design_dna.studio_law import enforce_law_1

    v = enforce_law_1(
        taste_overall=50,
        prior_best_overall=80,
        template_like=False,
        constructor_like=False,
        below_studio_bar=False,
    )
    assert v.action == "REBUILD"


def test_law_2_reality_over_architecture():
    from app.factory.design_dna.studio_law import (
        CLIENT_SEES,
        ERA_NEXT_PROGRAM,
        LAW_2,
        check_law_2_client_visible,
    )

    assert "клиенту" in LAW_2
    assert CLIENT_SEES == ("first_screen", "time_to_result", "quality_of_result")
    assert ERA_NEXT_PROGRAM == "Studio Intelligence"
    unfinished = check_law_2_client_visible(
        first_impression_change="Architecture improved, nothing visible yet"
    )
    assert unfinished.ok is False
    assert unfinished.action == "CONTINUE_WORK"
    visible = check_law_2_client_visible(
        first_impression_change="Premium hero now reads as cinematic dark glass on first screen"
    )
    assert visible.ok is True
    assert visible.action == "CLIENT_VISIBLE"


def test_fabricate_living_company():
    from app.factory.company_fabrication import fabricate_company

    c = fabricate_company(
        niche_id="restaurant",
        city="Köln",
        package_id="premium",
        diversity_salt="owner-fail-1",
    )
    assert c.brand_name
    assert c.founded_year >= 2016
    assert len(c.services) >= 8
    assert c.mission
    assert c.history
    assert len(c.team) >= 3
    assert len(c.faq) >= 4
    assert all("Demo" in cite or "Demo-" in cite for _, cite in c.reviews)
    assert "5" in str(c.founded_year) or c.founded_year < 2025


def test_design_concept_before_html():
    from app.factory.design_dna.concept_gate import (
        REALITY_BENCHMARK_STATUS,
        SITE_HTML_EXPORT_FROZEN,
        should_export_marketing_html,
    )
    from app.factory.design_dna.creative_identity import (
        check_creative_conflict,
        invent_creative_identity,
    )
    from app.factory.design_dna.creative_identity import CREATIVE_THEMES

    assert REALITY_BENCHMARK_STATUS == "FAIL"
    assert SITE_HTML_EXPORT_FROZEN is True
    assert should_export_marketing_html() is False
    identity = invent_creative_identity(
        business_name="Praxis Klarheit",
        niche_id="psychology",
        package_id="premium",
        surface="site",
        diversity_salt="a",
    )
    assert identity.title  # named theme e.g. Silent Forest
    assert identity.idea
    assert identity.human.get("founder_name")
    assert identity.core_emotion
    assert identity.creative_theme
    assert identity.html_export_allowed is False
    forest = next(t for t in CREATIVE_THEMES if t.id == "silent_forest")
    bad = check_creative_conflict(forest, approach_id="tech_saas", motion_hint="gaming")
    assert bad.ok is False
    assert bad.action == "FAIL"


def test_agency_os_manifest_chain():
    from app.factory.design_dna.agency_os import (
        AGENCY_ROLES,
        DIGITAL_SIGNATURE,
        ECOSYSTEM_SURFACES,
        RIGHT_FRAME,
        build_agency_review,
    )

    assert len(AGENCY_ROLES) >= 12
    assert AGENCY_ROLES[-1].id == "owner_review"
    assert "купил" in AGENCY_ROLES[-1].question.lower() or "Buy" in AGENCY_ROLES[-1].question
    assert "strong" in DIGITAL_SIGNATURE.aim.lower()
    assert len(ECOSYSTEM_SURFACES) >= 8
    assert "digital business" in RIGHT_FRAME.lower()
    review = build_agency_review(niche_id="psychology", business_name="Praxis Klarheit")
    assert review.owner_review == "PENDING_OWNER"
    assert len(review.roles) == len(AGENCY_ROLES)


def test_typography_engine_niche_divergence():
    from app.factory.design_dna.typography_engine import (
        catalog_size,
        resolve_type_pair,
    )

    assert catalog_size() >= 80
    psych = resolve_type_pair(niche_id="psychology", emotion="calm", package_id="premium")
    auto = resolve_type_pair(niche_id="auto", emotion="energy", package_id="business")
    assert psych.id != auto.id or psych.display != auto.display
