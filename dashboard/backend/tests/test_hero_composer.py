"""R2.2a — Hero Composer: distinct HTML compositions, deterministic seed."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.hero_composer import (
    LAYOUT_IDS,
    NICHE_LAYOUT_ALLOWLIST,
    select_hero_layout,
)
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def _hero_layout(html: str) -> str:
    m = re.search(r'data-hero-layout="([A-F])"', html)
    assert m, "missing data-hero-layout"
    return m.group(1)


def _hero_markers(html: str) -> set[str]:
    markers = {
        "A": "hero-A-grid",
        "B": "hero-B-kpis",
        "C": "hero-C-portrait",
        "D": "hero-D-float",
        "E": "hero-E-orb",
        "F": "hero-F-rail",
    }
    return {k for k, needle in markers.items() if needle in html}


def test_select_hero_layout_is_deterministic():
    a = select_hero_layout(
        niche_id="dental", business_name="Zahnarztpraxis Mueller", package_id="business"
    )
    b = select_hero_layout(
        niche_id="dental", business_name="Zahnarztpraxis Mueller", package_id="business"
    )
    assert a == b
    assert a in NICHE_LAYOUT_ALLOWLIST["dental"]


def test_niche_allowlist_separates_dental_and_auto():
    dental = {
        select_hero_layout(niche_id="dental", business_name=f"Clinic {i}", package_id="business")
        for i in range(40)
    }
    auto = {
        select_hero_layout(niche_id="auto", business_name=f"Garage {i}", package_id="business")
        for i in range(40)
    }
    assert dental <= set(NICHE_LAYOUT_ALLOWLIST["dental"])
    assert auto <= set(NICHE_LAYOUT_ALLOWLIST["auto"])
    assert dental.isdisjoint(auto)


def test_same_niche_can_pick_different_layouts():
    layouts = {
        select_hero_layout(
            niche_id="dental",
            business_name=name,
            package_id="business",
        )
        for name in (
            "Zahnarztpraxis Mueller",
            "Dental Care Nord",
            "Smile Studio Koeln",
            "Praxis am Dom",
            "White Smile Berlin",
            "Zahnzentrum West",
        )
    }
    assert len(layouts) >= 2


def test_dental_vs_auto_html_structure_differs():
    dental_html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."),
        features=resolve_package_features("business"),
        motion_level="css",
    )
    auto_html = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion und Reifenwechsel."),
        features=resolve_package_features("business"),
        motion_level="css",
    )
    d_layout = _hero_layout(dental_html)
    a_layout = _hero_layout(auto_html)
    assert d_layout in NICHE_LAYOUT_ALLOWLIST["dental"]
    assert a_layout in NICHE_LAYOUT_ALLOWLIST["auto"]
    assert d_layout != a_layout
    assert _hero_markers(dental_html) == {d_layout}
    assert _hero_markers(auto_html) == {a_layout}
    assert "Virtus" not in dental_html
    assert "tier-switch" not in dental_html.casefold()


def test_all_layouts_render_unique_markers(monkeypatch):
    """Each layout id produces a unique structural marker in HTML."""
    import app.factory.landing_builder as lb

    base = analyze("Lokalgeschäft Test in Berlin. Service und Beratung.")
    for lid in LAYOUT_IDS:
        monkeypatch.setattr(
            lb,
            "resolve_hero_for_layout",
            lambda _profile, lid=lid, **_kwargs: lid,
        )
        html = build_landing_html(
            base,
            features=resolve_package_features("premium"),
        )
        markers = _hero_markers(html)
        assert markers == {lid}, (lid, markers)
        assert f'data-hero-layout="{lid}"' in html
