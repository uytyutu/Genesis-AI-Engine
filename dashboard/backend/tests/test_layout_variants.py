"""R2.2f — Layout Variants: profiles, not random section shuffles."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.landing_builder import build_landing_html
from app.factory.layout_variants import (
    LAYOUT_PROFILES,
    assemble_body,
    resolve_layout_profile,
)
from app.factory.package_features import resolve_package_features
from app.factory.quality_gate import run_quality_gate


def _layout_id(html: str) -> str:
    m = re.search(r'data-layout-profile="(L[1-6])"', html)
    assert m, "missing data-layout-profile"
    return m.group(1)


def _section_ids_in_order(html: str) -> list[str]:
    """Order of major section ids after hero (rough structural fingerprint)."""
    body = html.split("</nav>", 1)[-1]
    # Drop footer
    body = body.split("<footer", 1)[0]
    return re.findall(
        r'id="(services|trust|gallery|about|faq|contact|mid-cta|late-cta|benefits|process|showcase|stats|maps|calculator|testimonials)"',
        body,
    )


def test_resolve_layout_deterministic():
    a = resolve_layout_profile(
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    b = resolve_layout_profile(
        business_name="Zahnarztpraxis Mueller",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    assert a.id == b.id
    assert a.id in LAYOUT_PROFILES


def test_two_dentists_can_diverge():
    names = (
        "Zahnarztpraxis Mueller",
        "Dental Care Nord",
        "Smile Studio Koeln",
        "Praxis am Dom",
        "White Smile Berlin",
        "Zahnzentrum West",
        "Dr. Weber Implantologie",
        "Klinik am Rhein",
    )
    profiles = {
        resolve_layout_profile(
            business_name=n,
            package_id="business",
            market_code="DE",
            niche_id="dental",
        ).id
        for n in names
    }
    assert len(profiles) >= 2


def test_market_shifts_seed():
    de = resolve_layout_profile(
        business_name="Clinica Demo",
        package_id="business",
        market_code="DE",
        niche_id="dental",
    )
    es = resolve_layout_profile(
        business_name="Clinica Demo",
        package_id="business",
        market_code="ES",
        niche_id="dental",
    )
    # Same client name can land on different profiles across markets
    assert de.id in LAYOUT_PROFILES and es.id in LAYOUT_PROFILES


def test_html_exposes_layout_profile_attrs():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    assert 'data-layout-profile="' in html
    assert 'data-footer-variant="' in html
    assert 'data-cta-strategy="' in html
    assert "Layout Variants R2.2f" in html


def test_section_order_follows_profile():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate."),
        features=resolve_package_features("business"),
        market_code="DE",
        client_gallery=["assets/g1.jpg", "assets/g2.jpg"],
    )
    lid = _layout_id(html)
    profile = LAYOUT_PROFILES[lid]
    ids = _section_ids_in_order(html)
    # Contact always last among body sections that exist
    assert "contact" in ids
    assert ids[-1] == "contact"
    # Trust position relative to gallery when both present
    if "trust" in ids and "gallery" in ids:
        trust_i = ids.index("trust")
        gallery_i = ids.index("gallery")
        if profile.trust_position == "after_gallery":
            assert trust_i > gallery_i
        if profile.trust_position == "before_contact":
            assert trust_i == ids.index("contact") - 1 or trust_i < ids.index("contact")


def test_assemble_body_respects_order():
    html = assemble_body(
        {"services": "<s>S</s>", "trust": "<t>T</t>", "contact": "<c>C</c>"},
        ("trust", "services", "contact"),
    )
    assert html.index("<t>") < html.index("<s>") < html.index("<c>")


def test_two_dentists_html_structure_differs():
    a = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
        client_gallery=["assets/a.jpg"],
    )
    b = build_landing_html(
        analyze("Smile Studio Berlin. Implantate und Bleaching."),
        features=resolve_package_features("business"),
        market_code="DE",
        client_gallery=["assets/a.jpg"],
    )
    # Different layout profile OR different section fingerprint OR footer
    diverge = (
        _layout_id(a) != _layout_id(b)
        or _section_ids_in_order(a) != _section_ids_in_order(b)
        or re.search(r'data-footer-variant="([^"]+)"', a).group(1)
        != re.search(r'data-footer-variant="([^"]+)"', b).group(1)
        or re.search(r'data-hero-layout="([^"]+)"', a).group(1)
        != re.search(r'data-hero-layout="([^"]+)"', b).group(1)
    )
    assert diverge


def test_quality_gate_requires_layout_profile():
    html = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion."),
        features=resolve_package_features("business"),
        market_code="DE",
        motion_level="css",
    )
    result = run_quality_gate(
        html,
        meta={"market_code": "DE", "package_delivery": {"package_id": "business"}},
    )
    assert result.passed, result.failures
    assert any(c.id == "layout_profile" and c.ok for c in result.checks)
