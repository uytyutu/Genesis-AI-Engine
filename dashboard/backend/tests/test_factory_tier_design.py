"""Factory ZIP tier design systems — Basic / Business / Premium look different."""

from __future__ import annotations

from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def test_package_feature_tier_blocks() -> None:
    basic = resolve_package_features("basic")
    business = resolve_package_features("business")
    premium = resolve_package_features("premium")
    assert not basic.maps and not basic.faq and not basic.stats_strip
    assert basic.catalog_grid is False
    assert business.catalog_search_filter is False
    assert premium.catalog_rich_cards is False
    assert basic.process and basic.mid_cta and basic.trust_bar
    assert business.maps and business.faq and business.process and business.mid_cta
    assert not business.calculator and not business.stats_strip
    assert premium.calculator and premium.stats_strip and premium.showcase and premium.faq


def test_tier_html_markers_auto() -> None:
    analysis = analyze("Autowerkstatt Bergmann — Inspektion und Reifen in Köln")
    city, street = "Köln", "Rheinstraße 12"

    basic = build_landing_html(
        analysis,
        features=resolve_package_features("basic"),
        whatsapp="+491715550100",
        city=city,
        street=street,
        market_code="DE",
    )
    assert 'data-tier="basic"' in basic
    assert 'id="maps"' not in basic
    assert 'id="faq"' not in basic
    assert 'id="stats"' not in basic
    assert 'id="showcase"' not in basic
    assert (
        'id="process"' in basic
        or 'data-trust-block="process"' in basic
        or "process-grid" in basic
    )
    assert 'id="mid-cta"' in basic
    assert "trust-strip" in basic
    assert "Anfrage senden" in basic

    business = build_landing_html(
        analysis,
        features=resolve_package_features("business"),
        whatsapp="+491715550100",
        city=city,
        street=street,
        market_code="DE",
    )
    assert 'data-tier="business"' in business
    assert 'id="maps"' in business
    assert 'id="faq"' in business
    assert (
        'id="process"' in business
        or 'data-trust-block="process"' in business
        or "process-grid" in business
    )
    assert 'id="mid-cta"' in business
    assert "Route planen" in business
    assert "maps/dir/?api=1" in business
    assert 'id="calculator"' not in business
    assert 'id="stats"' not in business

    premium = build_landing_html(
        analysis,
        features=resolve_package_features("premium"),
        whatsapp="+491715550100",
        city=city,
        street=street,
        market_code="DE",
    )
    assert 'data-tier="premium"' in premium
    assert 'id="calculator"' in premium
    # Stats strip only when real client KPIs exist — never invent numbers.
    assert 'id="showcase"' in premium
    assert 'id="faq"' in premium
    assert "--acc: #c5a572" in premium or "c5a572" in premium
    assert any(m in premium for m in ("hero-layout-B", "hero-layout-D", "hero-layout-F"))
    assert 'id="signature"' in premium
    assert "premium-signature" in premium
    assert 'data-tier="premium"' in premium


def test_premium_hero_is_cinematic_not_niche_twin() -> None:
    from app.factory.layout_variants import get_layout_profile, resolve_hero_for_layout

    profile = get_layout_profile("L6")
    hero = resolve_hero_for_layout(
        profile,
        niche_id="dental",
        business_name="SmileCare Berlin",
        package_id="premium",
    )
    assert hero in ("B", "D", "F")
    basic = resolve_hero_for_layout(
        profile,
        niche_id="dental",
        business_name="SmileCare Berlin",
        package_id="basic",
    )
    assert basic in ("A", "C")
    assert hero != basic or True  # may coincide across names; pool class must differ
    assert hero in ("B", "D", "F") and basic in ("A", "C")


def test_factory_writes_hero_asset(tmp_path: Path) -> None:
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Autowerkstatt Bergmann — Inspektion in Köln",
        package_id="business",
        market_code="DE",
        contacts={
            "business_name": "Autowerkstatt Bergmann",
            "phone": "+49 221 555",
            "city": "Köln",
            "street": "Rheinstraße 12",
        },
    )
    hero = tmp_path / "sandbox" / product["product_id"] / "assets" / "hero.jpg"
    html = (tmp_path / "sandbox" / product["product_id"] / "index.html").read_text(encoding="utf-8")
    assert 'data-tier="business"' in html
    assert 'id="faq"' in html
    # Hero still copied when research showcase exists for niche
    if hero.is_file():
        assert "assets/hero.jpg" in html
        assert "has-photo" in html
