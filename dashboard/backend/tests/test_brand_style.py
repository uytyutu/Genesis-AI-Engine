"""Brand Style packs — additive Path A look (does not remove niche defaults)."""

from __future__ import annotations

from app.factory.analyzer import analyze
from app.factory.brand_style import (
    get_brand_style_pack,
    list_brand_styles,
    normalize_brand_style,
)
from app.factory.factory_service import FactoryService
from app.factory.landing_builder import build_landing_html
from app.factory.package_features import resolve_package_features


def test_normalize_and_catalog():
    assert normalize_brand_style(None) == "auto"
    assert normalize_brand_style("Premium") == "premium"
    assert normalize_brand_style("lux") == "premium"
    assert get_brand_style_pack("auto") is None
    assert get_brand_style_pack("minimal") is not None
    styles = list_brand_styles(lang="de")
    assert styles[0]["id"] == "auto"
    assert any(s["id"] == "friendly" for s in styles)


def test_html_data_brand_and_css(tmp_path):
    html_auto = build_landing_html(
        analyze("Zahnarzt München"),
        features=resolve_package_features("basic"),
        market_code="DE",
        brand_style="auto",
    )
    assert 'data-brand="auto"' in html_auto

    html_min = build_landing_html(
        analyze("Zahnarzt München"),
        features=resolve_package_features("basic"),
        market_code="DE",
        brand_style="minimal",
    )
    assert 'data-brand="minimal"' in html_min
    assert "Brand Style: minimal" in html_min
    assert "--btn-radius:" in html_min


def test_factory_meta_stores_brand_style(tmp_path):
    factory = FactoryService(memory_dir=tmp_path / "mem", sandbox_dir=tmp_path / "sandbox")
    result = factory.build_landing(
        "Autowerkstatt Berlin — Inspektion und Reifen",
        package_id="business",
        contacts={
            "business_name": "Auto Berlin",
            "city": "Berlin",
            "brand_style": "corporate",
            "market_code": "DE",
        },
        market_code="DE",
    )
    import json

    meta = json.loads(
        (tmp_path / "sandbox" / result["product_id"] / "meta.json").read_text(encoding="utf-8")
    )
    assert meta.get("brand_style") == "corporate"
    html = (tmp_path / "sandbox" / result["product_id"] / "index.html").read_text(
        encoding="utf-8"
    )
    assert 'data-brand="corporate"' in html
