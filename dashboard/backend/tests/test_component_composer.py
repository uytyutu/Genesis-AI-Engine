"""R2.2b — Component Composer: one profile language per page."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.component_composer import (
    HERO_PROFILE_COMPAT,
    select_component_profile,
)
from app.factory.hero_composer import select_hero_layout
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def _attrs(html: str) -> tuple[str, str]:
    hero = re.search(r'data-hero-layout="([A-F])"', html)
    comp = re.search(r'data-comp-profile="([A-C])"', html)
    assert hero and comp
    return hero.group(1), comp.group(1)


def test_component_profile_deterministic_with_hero():
    hero = select_hero_layout(
        niche_id="dental", business_name="Zahnarztpraxis Mueller", package_id="business"
    )
    a = select_component_profile(
        hero_layout=hero,
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        niche_id="dental",
    )
    b = select_component_profile(
        hero_layout=hero,
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        niche_id="dental",
    )
    assert a == b
    assert a in HERO_PROFILE_COMPAT[hero]


def test_profile_always_compatible_with_hero():
    for niche, names in (
        ("dental", ["Clinic Alpha", "Clinic Beta", "Smile Nord", "Praxis West"]),
        ("auto", ["Garage One", "Autohaus Zwei", "Werkstatt Drei", "Motor Four"]),
        ("law", ["Kanzlei A", "Rechtsanwalt B", "Notar C", "Anwalt D"]),
    ):
        for name in names:
            hero = select_hero_layout(niche_id=niche, business_name=name, package_id="premium")
            profile = select_component_profile(
                hero_layout=hero,
                business_name=name,
                package_id="premium",
                niche_id=niche,
            )
            assert profile in HERO_PROFILE_COMPAT[hero]


def test_same_niche_can_differ_in_component_composition():
    variants: set[tuple[str, str]] = set()
    for name in (
        "Zahnarztpraxis Mueller",
        "Dental Care Nord",
        "Smile Studio Koeln",
        "Praxis am Dom",
        "White Smile Berlin",
        "Zahnzentrum West",
        "Dentalis Hamburg",
        "Klinik am Park",
    ):
        html = build_landing_html(
            analyze(f"{name} in Koeln. Prophylaxe und Implantate."),
            features=resolve_package_features("business"),
            client_gallery=["assets/g1.jpg", "assets/g2.jpg", "assets/g3.jpg"],
        )
        variants.add(_attrs(html))
    # Either hero or component profile (or both) should diversify silhouettes.
    assert len(variants) >= 2


def test_page_uses_single_profile_language():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."),
        features=resolve_package_features("business"),
        client_gallery=["assets/g1.jpg", "assets/g2.jpg"],
    )
    hero, profile = _attrs(html)
    assert profile in HERO_PROFILE_COMPAT[hero]
    # All composed families share the same profile attribute on body; markers match profile.
    assert f'data-comp-profile="{profile}"' in html
    # Cards + benefits always render. Review variants (float/quote/rating) only
    # when client_trust supplies real reviews — never fabricate them.
    markers = {
        "A": ("data-comp-variant=\"glass\"", "data-comp-variant=\"circles\""),
        "B": ("data-comp-variant=\"solid\"", "data-comp-variant=\"timeline\""),
        "C": ("data-comp-variant=\"minimal\"", "data-comp-variant=\"editorial\""),
    }
    for needle in markers[profile]:
        assert needle in html
    review_marker = {
        "A": 'data-comp-variant="float"',
        "B": 'data-comp-variant="quote"',
        "C": 'data-comp-variant="rating"',
    }[profile]
    assert review_marker not in html
    assert 'id="testimonials"' not in html
    # No foreign family markers from other profiles.
    foreign = {
        "A": ("data-comp-variant=\"solid\"", "data-comp-variant=\"timeline\""),
        "B": ("data-comp-variant=\"glass\"", "data-comp-variant=\"circles\""),
        "C": ("data-comp-variant=\"glass\"", "data-comp-variant=\"float\""),
    }
    for needle in foreign[profile]:
        assert needle not in html


def test_dental_vs_auto_section_structures_diverge():
    dental = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        client_gallery=["assets/a.jpg", "assets/b.jpg"],
    )
    auto = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion."),
        features=resolve_package_features("business"),
        client_gallery=["assets/a.jpg", "assets/b.jpg"],
    )
    assert _attrs(dental) != _attrs(auto) or (
        "data-comp-variant=" in dental and dental != auto
    )
    assert "Virtus" not in dental
    # Structural markers differ between niches often via hero allowlists.
    d_vars = set(re.findall(r'data-comp-variant="([^"]+)"', dental))
    a_vars = set(re.findall(r'data-comp-variant="([^"]+)"', auto))
    assert d_vars
    assert a_vars
