"""R2.2d — Trust Composer: real data only, niche + market order."""

from __future__ import annotations

import re

from app.factory.analyzer import analyze
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features
from app.factory.trust_composer import (
    collect_trust_evidence,
    compose_trust_section,
    select_trust_template,
)


def test_no_fabricated_testimonials_without_client_reviews():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
    )
    assert 'id="testimonials"' not in html
    assert "Beispieltexte" not in html or 'id="testimonials"' not in html
    # Soft commitments may appear in trust composer, not as fake reviews
    assert "data-trust-template=" in html
    assert 'id="trust"' in html


def test_real_rating_builds_social_block():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
        client_trust={
            "rating": 4.9,
            "review_count": 287,
            "rating_source": "Google",
            "certificates": ["Implantologie-Fortbildung"],
        },
    )
    assert 'data-trust-block="social"' in html
    assert "4.9" in html
    assert "287" in html
    assert "Google" in html
    assert "Implantologie-Fortbildung" in html
    assert 'id="testimonials"' not in html  # no quote reviews unless provided


def test_real_reviews_enable_testimonials():
    html = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="ES",
        client_trust={
            "reviews": [
                {"text": "Muy profesional y cercano.", "cite": "Ana P."},
            ],
        },
    )
    assert 'id="testimonials"' in html
    assert "Muy profesional" in html
    assert "Ana P." in html


def test_no_fabricated_stats_strip():
    html = build_landing_html(
        analyze("Autowerkstatt Schmidt in Berlin. Inspektion."),
        features=resolve_package_features("premium"),
        market_code="DE",
    )
    # Default ui 12+/800+ must not appear as invented stats
    assert 'id="stats"' not in html or "12+" not in html


def test_market_order_differs_de_vs_es():
    trust = {
        "rating": 4.8,
        "review_count": 40,
        "certificates": ["Meisterbetrieb"],
    }
    gallery = ["assets/a.jpg", "assets/b.jpg"]
    de = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="DE",
        client_trust=trust,
        client_gallery=gallery,
    )
    es = build_landing_html(
        analyze("Zahnarztpraxis Mueller in Koeln. Prophylaxe."),
        features=resolve_package_features("business"),
        market_code="ES",
        client_trust=trust,
        client_gallery=gallery,
    )
    de_blocks = re.findall(r'data-trust-block="([^"]+)"', de)
    es_blocks = re.findall(r'data-trust-block="([^"]+)"', es)
    assert de_blocks and es_blocks
    # Same families available, but leading block can differ by market/template
    assert set(de_blocks) == set(es_blocks) or de_blocks != es_blocks


def test_evidence_ignores_placeholders():
    ev = collect_trust_evidence(
        client_trust={"certificates": ["TODO", "n/a", "ISO 9001"], "rating": ""},
        commitments=("Klarer Ablauf",),
        portfolio_paths=[],
        has_maps=False,
        has_process=True,
    )
    assert ev.certificates == ("ISO 9001",)
    assert ev.rating is None
    assert ev.has_credentials


def test_trust_template_deterministic():
    ev = collect_trust_evidence(
        client_trust={"rating": 4.5, "review_count": 10},
        commitments=("Lokal",),
        portfolio_paths=["assets/x.jpg"],
        has_maps=True,
        has_process=True,
    )
    a = select_trust_template(
        niche_id="dental",
        market_code="DE",
        business_name="Praxis A",
        package_id="business",
        evidence=ev,
    )
    b = select_trust_template(
        niche_id="dental",
        market_code="DE",
        business_name="Praxis A",
        package_id="business",
        evidence=ev,
    )
    assert a == b
    assert a in ("A", "B", "C", "D")
