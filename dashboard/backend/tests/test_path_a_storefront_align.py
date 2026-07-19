"""Storefront deliverables mirror Factory ZIP Layer A (no 3D / no owner panel)."""

from __future__ import annotations

from app.factory.market_delivery import deploy_readme
from app.integration.sales_order_service import (
    _PACKAGES,
    package_display_name,
    package_included_summary,
)


def test_layer_a_packages_have_value_copy() -> None:
    basic = _PACKAGES["basic"]
    business = _PACKAGES["business"]
    premium = _PACKAGES["premium"]
    assert basic["price_eur"] == 350
    assert business["price_eur"] == 650
    assert premium["price_eur"] == 1200
    assert any("WhatsApp" in d for d in basic["deliverables"])
    assert any("Maps" in d or "Route" in d for d in business["deliverables"])
    assert any("FAQ" in d for d in business["deliverables"])
    assert any("Showcase" in d or "Kennzahlen" in d for d in premium["deliverables"])
    assert any("Kostenrechner" in d for d in premium["deliverables"])
    # Layer B not sold on storefront
    blob = " ".join(
        " ".join(p["deliverables"]) + " " + p.get("included_summary", "")
        for p in _PACKAGES.values()
    ).lower()
    assert "3d" not in blob
    assert "kabinett" not in blob and "owner panel" not in blob
    assert "панель" not in blob


def test_readme_confirms_chosen_package() -> None:
    text = deploy_readme("DE", package_id="business")
    assert "Landing Business" in text or "Business" in text
    assert "Sie haben das Paket" in text
    assert "Inklusive:" in text
    assert package_included_summary("business")[:20] in text
    assert package_display_name("premium") == "Landing Premium"
