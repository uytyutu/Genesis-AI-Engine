"""Studio Renderer 2.0 — niche WebGL policy + Premium media floor."""

from __future__ import annotations

from app.factory.creative_direction import recommends_webgl_3d
from app.factory.studio_renderer_v2 import (
    decide_webgl,
    plan_studio_experience,
    premium_media_slot_names,
)


def test_psychology_no_heavy_webgl():
    d = decide_webgl("family_psychology", "premium")
    assert d.enabled is False
    assert d.mode == "cinematic"
    assert recommends_webgl_3d("family_psychology", "premium") is False


def test_autohaus_amplifies_webgl():
    d = decide_webgl("car_dealership", "premium")
    assert d.enabled is True
    assert d.mode == "amplify"
    assert "Showroom" in d.sell_reason or "showroom" in d.sell_reason.lower()
    assert recommends_webgl_3d("car_dealership", "premium") is True
    assert recommends_webgl_3d("car_dealership", "business") is False


def test_no_sell_reason_blocks_webgl():
    d = decide_webgl("restaurant", "premium")
    assert d.enabled is False
    assert d.sell_reason == ""


def test_gallery_stories_are_unique_labels():
    from app.factory.studio_renderer_v2 import gallery_story_for

    stories = [gallery_story_for("car_dealership", i) for i in range(1, 13)]
    assert len(set(stories)) == 12


def test_nail_soft_glass_not_gimmick():
    d = decide_webgl("nail_studio", "premium")
    assert d.enabled is True
    assert d.mode == "soft"


def test_premium_media_slots_cover_experience():
    slots = premium_media_slot_names(package_id="premium")
    assert "hero.jpg" in slots
    assert "gallery_12.jpg" in slots
    assert "section_story.jpg" in slots
    assert "section_contact.jpg" in slots
    assert len(slots) >= 20


def test_experience_plan_motion_stack():
    plan = plan_studio_experience(niche_id="car_dealership", package_id="premium")
    assert "lenis" in plan.motion
    assert plan.gallery_min == 12
    assert plan.webgl.hero_media == "webgl"
