"""Vector Phase 1 — Store Admin setup readiness (rule-based)."""

from __future__ import annotations

from pathlib import Path

from app.integration.store_admin.design_service import default_design
from app.integration.store_admin.setup_status import (
    PRODUCT_TARGET,
    StoreSetupStatusService,
    build_setup_status,
)
from app.integration.store_admin.commerce_settings import default_commerce_settings
from app.integration.store_admin.catalog_service import StoreCatalogService


def test_build_setup_status_empty_store():
    design = default_design(store_name="Demo")
    commerce = default_commerce_settings()
    out = build_setup_status(
        order_id="ord-1",
        product_count=0,
        design=design,
        commerce_settings=commerce,
        shop_pipeline="ready_to_publish",
    )
    assert out["surface"] == "store_admin"
    assert out["vector"]["assistant"] == "Vector"
    assert out["readiness_pct"] == 0
    assert out["setup_pct"] == 0
    assert out["next_step"]["id"] == "logo"
    assert any(t["id"] == "tip_logo" for t in out["tips"])
    assert any(t["id"] == "tip_products_empty" for t in out["tips"])
    stripe = next(s for s in out["steps"] if s["id"] == "stripe")
    assert stripe["done"] is False
    assert stripe["actionable"] is True
    shipping = next(s for s in out["steps"] if s["id"] == "shipping")
    assert shipping["actionable"] is True
    assert shipping.get("coming") is None
    taxes = next(s for s in out["steps"] if s["id"] == "taxes")
    assert taxes["actionable"] is True


def test_build_setup_status_partial_catalog_tip():
    design = default_design()
    design["branding"]["logo"] = {"id": "logo-1", "url": "/x.png"}
    design["colors"]["primary"] = "#111111"
    commerce = default_commerce_settings()
    out = build_setup_status(
        order_id="ord-2",
        product_count=2,
        design=design,
        commerce_settings=commerce,
        shop_pipeline="published",
    )
    assert out["product_count"] == 2
    products = next(s for s in out["steps"] if s["id"] == "products")
    assert products["done"] is True
    assert products["meta"]["target"] == PRODUCT_TARGET
    assert products["meta"]["strong"] is False
    tip = next(t for t in out["tips"] if t["id"] == "tip_products_thin")
    assert "2 product" in tip["message"]
    assert "10" in tip["message"]
    assert next(s for s in out["steps"] if s["id"] == "publish")["done"] is True
    # logo 15 + products 18 + colors 10 + publish 9 = 52 (commerce steps open; email added)
    assert out["readiness_pct"] == 52
    assert out["setup_pct"] == 52


def test_store_setup_status_service(tmp_path: Path):
    catalog = StoreCatalogService(tmp_path)
    catalog.create_product(
        "ord-svc",
        {"title": "First SKU", "price": 19.9, "status": "published"},
    )
    svc = StoreSetupStatusService(tmp_path)
    out = svc.get("ord-svc", store_name="Handwerk Shop", shop_pipeline="generating")
    assert out["ok"] is True
    assert out["product_count"] == 1
    assert out["order_id"] == "ord-svc"
    assert isinstance(out["steps"], list)
    assert len(out["steps"]) == 9
    assert any(s["id"] == "email" for s in out["steps"])
