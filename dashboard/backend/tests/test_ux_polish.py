"""R3.2.1 — UX Polish: document scroll + tiered back-to-top."""

from __future__ import annotations

from pathlib import Path

from app.factory.analyzer import analyze
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features
from app.factory.ux_polish import (
    back_to_top_html,
    ux_polish_css,
    ux_polish_enabled,
    write_ux_polish_assets,
)


def test_ux_polish_tier_rules():
    assert not ux_polish_enabled("basic")
    assert ux_polish_enabled("business")
    assert ux_polish_enabled("premium")
    assert "back-to-top" not in back_to_top_html("basic")
    assert "back-to-top" in back_to_top_html("business")
    assert "back-to-top" in back_to_top_html("premium")
    assert "scroll-behavior: smooth" in ux_polish_css("basic")
    assert "back-to-top" in ux_polish_css("business")
    assert 'data-tier="premium"' in ux_polish_css("premium") or "premium" in ux_polish_css(
        "premium"
    )


def test_html_business_has_back_to_top_basic_does_not():
    analysis = analyze("Salon Mira Berlin — Haarschnitt, Farbe, Pflege.")
    basic = build_landing_html(
        analysis,
        features=resolve_package_features("basic"),
        market_code="DE",
        hero_photo=True,
    )
    business = build_landing_html(
        analysis,
        features=resolve_package_features("business"),
        market_code="DE",
        hero_photo=True,
    )
    premium = build_landing_html(
        analysis,
        features=resolve_package_features("premium"),
        market_code="DE",
        hero_photo=True,
    )
    assert 'id="top"' in basic
    assert "overflow-x: clip" in basic
    assert "back-to-top" not in basic
    assert "assets/ux_polish.js" not in basic
    assert 'class="back-to-top"' in business
    assert "assets/ux_polish.js" in business
    assert 'class="back-to-top"' in premium
    assert "assets/ux_polish.js" in premium


def test_factory_writes_ux_asset(tmp_path: Path):
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Autowerkstatt Nord — Inspektion in Hamburg.",
        package_id="business",
        market_code="DE",
        client_legal={
            "owner_name": "Nord",
            "street": "Test 1",
            "zip": "20095",
            "city": "Hamburg",
            "email": "a@b.de",
        },
    )
    pid = product["product_id"]
    assets = tmp_path / "sandbox" / pid / "assets"
    assert (assets / "ux_polish.js").is_file()
    html = (tmp_path / "sandbox" / pid / "index.html").read_text(encoding="utf-8")
    assert "back-to-top" in html
    assert "R3.2.1 UX Polish" in html or "scroll-behavior: smooth" in html


def test_write_ux_polish_assets(tmp_path: Path):
    written = write_ux_polish_assets(tmp_path)
    assert written == ["assets/ux_polish.js"]
    assert (tmp_path / "assets" / "ux_polish.js").is_file()
