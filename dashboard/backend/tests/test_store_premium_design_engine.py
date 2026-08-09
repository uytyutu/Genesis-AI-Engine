"""AI Store Premium Generation — Design Engine bridge tests."""

from __future__ import annotations

from pathlib import Path

from app.factory.store_factory.composer import write_storefront
from app.factory.store_factory.design_bridge import (
    STORE_CATEGORY_TO_NICHE,
    store_category_to_niche_id,
    visual_preset_for_category,
)
from app.factory.store_factory.templates import StoreTemplateRegistry, _CATEGORY_THEMES


def _brief(category: str, **extra: object) -> dict:
    return {
        "store_name": f"Demo {category.title()}",
        "company_name": "Demo GmbH",
        "what_is_sold": "Quality products",
        "category": category,
        "style": "modern",
        "currency": "EUR",
        "language": "de",
        "market": "DE",
        "payments": ["stripe"],
        "shipping": ["dhl"],
        **extra,
    }


def test_store_category_to_niche_mapping():
    assert store_category_to_niche_id("clothing") == "fashion"
    assert store_category_to_niche_id("beauty") == "beauty"
    assert store_category_to_niche_id("auto") == "auto"
    assert store_category_to_niche_id("electronics") == "computer"
    assert store_category_to_niche_id("food") == "restaurant"
    assert store_category_to_niche_id("handwerk") == "handwerk"
    assert store_category_to_niche_id("unknown") == "generic"
    assert set(STORE_CATEGORY_TO_NICHE) >= {
        "clothing",
        "beauty",
        "auto",
        "food",
        "handwerk",
    }


def test_visual_presets_diverge():
    fashion = visual_preset_for_category("clothing")
    auto = visual_preset_for_category("auto")
    beauty = visual_preset_for_category("beauty")
    food = visual_preset_for_category("food")
    handwerk = visual_preset_for_category("handwerk")
    assert fashion.hero_layout == "editorial"
    assert fashion.card_preset == "fashion"
    assert auto.hero_layout == "tech"
    assert auto.show_specs is True
    assert beauty.hero_layout == "soft"
    assert food.hero_layout == "culinary"
    assert handwerk.hero_layout == "industrial"
    assert handwerk.show_certs is True
    assert fashion.card_media_ratio != auto.card_media_ratio


def test_resolved_template_carries_design_engine():
    reg = StoreTemplateRegistry()
    clothing = reg.resolve(_brief("clothing"))
    auto = reg.resolve(_brief("auto"))
    assert clothing.niche_id == "fashion"
    assert clothing.visual_preset is not None
    assert clothing.visual_preset.hero_layout == "editorial"
    assert auto.niche_id == "auto"
    assert clothing.colors["accent"] != auto.colors["accent"] or clothing.colors[
        "primary"
    ] != auto.colors["primary"]


def test_handwerk_is_first_class_category():
    assert "handwerk" in _CATEGORY_THEMES
    reg = StoreTemplateRegistry()
    resolved = reg.resolve(_brief("handwerk"))
    assert resolved.niche_id == "handwerk"
    assert resolved.template_id == "niche_handwerk"


def test_write_storefront_injects_design_engine(tmp_path: Path):
    reg = StoreTemplateRegistry()
    clothing = reg.resolve(_brief("clothing"))
    auto = reg.resolve(_brief("auto"))
    beauty = reg.resolve(_brief("beauty"))

    cloth_dir = tmp_path / "cloth"
    auto_dir = tmp_path / "auto"
    beauty_dir = tmp_path / "beauty"
    cloth_dir.mkdir()
    auto_dir.mkdir()
    beauty_dir.mkdir()

    write_storefront(cloth_dir, brief=_brief("clothing"), resolved=clothing)
    write_storefront(auto_dir, brief=_brief("auto"), resolved=auto)
    write_storefront(beauty_dir, brief=_brief("beauty"), resolved=beauty)

    cloth_html = (cloth_dir / "index.html").read_text(encoding="utf-8")
    auto_html = (auto_dir / "index.html").read_text(encoding="utf-8")
    beauty_html = (beauty_dir / "index.html").read_text(encoding="utf-8")
    cloth_css = (cloth_dir / "assets" / "store.css").read_text(encoding="utf-8")
    auto_css = (auto_dir / "assets" / "store.css").read_text(encoding="utf-8")

    assert 'data-niche="fashion"' in cloth_html
    assert 'data-hero-layout="editorial"' in cloth_html
    assert 'data-card="fashion"' in cloth_html
    assert "fonts.googleapis.com" in cloth_html
    assert "Cormorant" in cloth_html or "Cormorant" in cloth_css or "font-display" in cloth_css

    assert 'data-niche="auto"' in auto_html
    assert 'data-hero-layout="tech"' in auto_html
    assert "Barlow" in auto_html or "Barlow" in auto_css or "--font-display" in auto_css

    assert 'data-niche="beauty"' in beauty_html
    assert 'data-hero-layout="soft"' in beauty_html

    assert "Design Engine" in cloth_css
    assert "--store-accent:" in cloth_css
    assert "data-image-slot=\"hero\"" in cloth_html or 'data-image-slot="hero"' in cloth_html
    assert (cloth_dir / "assets" / "images" / "README_IMAGE_SLOTS.txt").is_file()

    # Niches must not share identical hero layout + card preset
    assert (
        'data-hero-layout="editorial"' in cloth_html
        and 'data-hero-layout="tech"' in auto_html
    )


def test_warm_backgrounds_still_hold_for_all_categories():
    reg = StoreTemplateRegistry()
    for cat in _CATEGORY_THEMES:
        colors = reg.resolve(_brief(cat)).colors
        bg = colors["background"].strip().lower()
        assert bg not in {"#fff", "#ffffff", "white"}
