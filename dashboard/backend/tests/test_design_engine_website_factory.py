"""Website Factory Design Engine — niche tokens, fonts, allowlists."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.design_engine import (
    emit_css_vars,
    font_link_tags,
    font_pack_for_niche,
    resolve_for_niche,
)
from app.factory.hero_composer import NICHE_LAYOUT_ALLOWLIST, select_hero_layout
from app.factory.landing_builder import build_landing_html
from app.factory.landing_tier_css import apply_tier_palette
from app.factory.niche_profiles import known_niche_ids, resolve_niche_profile
from app.factory.package_features import resolve_package_features


def test_restaurant_is_not_generic():
    profile = resolve_niche_profile("restaurant")
    assert profile.niche_id == "restaurant"
    assert profile.style.primary != resolve_niche_profile("generic").style.primary
    assert "Fraunces" in profile.style.font_display or "serif" in profile.style.font_display.casefold()


def test_handwerk_is_full_design_system():
    hw = resolve_niche_profile("handwerk").style
    generic = resolve_niche_profile("generic").style
    assert hw.card_radius != generic.card_radius or hw.btn_radius != generic.btn_radius
    assert hw.btn_weight == "700"
    assert "Oswald" in hw.font_display or hw.radius == "4px"


def test_design_engine_emit_contains_fonts_and_vars():
    tokens = resolve_for_niche("restaurant")
    css = emit_css_vars(tokens)
    assert "Design Engine" in css
    assert "Niche Design System: restaurant" in css
    assert "--p:" in css
    assert "--font-body:" in css
    assert "--font-display:" in css
    assert "Fraunces" in css or "font-display" in css
    pack = font_pack_for_niche("restaurant")
    links = font_link_tags(pack)
    assert "fonts.googleapis.com" in links
    assert "Fraunces" in links or "family=Fraunces" in links


def test_hero_allowlist_covers_studio_niches():
    for niche in (
        "restaurant",
        "handwerk",
        "fashion",
        "accounting",
        "photography",
        "fitness",
        "realestate",
        "law",
        "beauty",
        "dental",
    ):
        assert niche in NICHE_LAYOUT_ALLOWLIST
        layout = select_hero_layout(
            niche_id=niche,
            business_name=f"Demo {niche}",
            package_id="business",
        )
        assert layout in NICHE_LAYOUT_ALLOWLIST[niche]


def test_restaurant_html_uses_design_engine_and_fonts():
    html = build_landing_html(
        analyze(
            "Restaurant Bella Vista in München. Italienische Küche, Pizza und Pasta."
        ),
        features=resolve_package_features("business"),
        motion_level="css",
        market_code="DE",
    )
    assert 'data-niche="restaurant"' in html
    assert "Design Engine" in html or "Niche Design System: restaurant" in html
    assert "fonts.googleapis.com" in html
    assert "--card-radius:" in html
    assert html.split("--p:")[1].split(";")[0].strip().lower() == "#c2410c"


def test_handwerk_html_diverges_from_restaurant():
    restaurant = build_landing_html(
        analyze("Restaurant Bella Vista München. Italienische Küche."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    handwerk = build_landing_html(
        analyze("Tischlerei Holzmeister in Köln. Möbel und Renovierung."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    assert 'data-niche="restaurant"' in restaurant
    assert 'data-niche="handwerk"' in handwerk
    r_p = restaurant.split("--p:")[1].split(";")[0].strip()
    h_p = handwerk.split("--p:")[1].split(";")[0].strip()
    assert r_p != h_p
    assert "Oswald" in handwerk or "handwerk" in handwerk


def test_premium_keeps_niche_primary_hue():
    style = resolve_niche_profile("law").style
    p, pd, acc, grad = apply_tier_palette(style, "premium")
    assert p == style.primary
    assert pd == style.primary_dark
    assert acc == "#c5a572"
    assert style.primary_dark in grad or style.primary in grad


def test_all_known_niches_resolve_full_tokens():
    for nid in known_niche_ids():
        tokens = resolve_for_niche(nid)
        assert tokens.niche_id == nid or (
            nid not in known_niche_ids() and tokens.niche_id == "generic"
        )
        assert tokens.primary.startswith("#")
        assert tokens.font_pack.body
        assert tokens.card_radius.endswith("px")
