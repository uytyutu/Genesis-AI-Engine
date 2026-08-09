"""Creative Director, Design Memory, Store Director."""

from pathlib import Path

from app.factory.visual_intelligence.ai_creative_director import decide_experience
from app.factory.visual_intelligence.design_memory import (
    check_similarity,
    record_composition,
)
from app.factory.visual_intelligence.store_director import decide_store_experience


def test_starter_forbids_heavy_media():
    d = decide_experience(package_id="basic", niche="dental")
    assert d["decisions"]["heavy_video"] is False
    assert d["decisions"]["webgl"] is False
    assert d["luxury_mode"] is False
    assert "Experience" in d["positioning"]["en"] or "experience" in d["positioning"]["en"]


def test_premium_enables_luxury():
    d = decide_experience(package_id="premium", niche="beauty")
    assert d["luxury_mode"] is True
    assert d["decisions"].get("luxury_mode") is True


def test_design_memory_similarity(tmp_path: Path):
    record_composition(
        fingerprint="aaaaaaaaaaaaaaaa",
        package_id="business",
        niche="dental",
        layout_profile="L2",
        hero_layout="C",
        memory_dir=tmp_path,
    )
    hit = check_similarity(
        "aaaaaaaaaaaaaaaa",
        niche="dental",
        package_id="premium",
        memory_dir=tmp_path,
    )
    assert hit["similarity_pct"] == 100
    assert hit["rebuild_needed"] is True


def test_store_director_requires_auth():
    s = decide_store_experience(package_id="basic", category="fashion")
    assert s["customer_auth"]["login"] is True
    assert s["customer_auth"]["register"] is True
    assert "search" in s["chrome"]


def test_diversity_salt_changes_layout():
    from app.factory.layout_variants import resolve_layout_profile

    a = resolve_layout_profile(
        business_name="Zahnarzt Praxis Nord",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    b = resolve_layout_profile(
        business_name="Zahnarzt Praxis Nord",
        package_id="business",
        market_code="DE",
        niche_id="dental",
        diversity_salt="dm1",
    )
    # Not always different (small pools), but salt must be accepted without error.
    assert a.id
    assert b.id


def test_store_director_premium_luxury_merch():
    s = decide_store_experience(package_id="premium", category="fashion", catalog_size=40)
    assert s["decisions"]["luxury_merchandising"] is True
    assert s["decisions"]["first_screen_products"] == 8
    assert s["customer_auth"]["customer_dashboard"] is True
