"""AI Store R1 — shop_brief, customer gate, pipeline stub."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.commercial_catalog_g23 import WEBSITE_SERVICE_PRICES_EUR
from app.integration.sales_order_service import SalesOrderService
from app.integration.shop_brief import (
    SHOP_PIPELINE_PUBLISHED,
    validate_shop_brief,
)


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-shop"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def _brief(**over):
    base = {
        "company_name": "Demo GmbH",
        "store_name": "Demo Shop",
        "what_is_sold": "Shoes and bags",
        "category": "clothing",
        "catalog_size": "100",
        "languages": ["de"],
        "currency": "EUR",
        "payments": ["stripe"],
        "shipping": ["dhl"],
        "pages": ["home", "catalog", "pdp", "legal"],
        "style": "modern",
    }
    base.update(over)
    return base


def test_catalog_price_unchanged():
    assert WEBSITE_SERVICE_PRICES_EUR["ecommerce_shop"] == 799


def test_validate_shop_brief_ok():
    b = validate_shop_brief(_brief())
    assert b["store_name"] == "Demo Shop"
    assert b["category"] == "clothing"


def test_ecommerce_requires_customer(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    with pytest.raises(ValueError, match="customer_id_required_for_shop"):
        sales.create_order(
            {
                "business_name": "Demo Shop",
                "email": "shop@test.local",
                "package_id": "ecommerce_shop",
                "description": "Shoes and bags for local buyers",
                "shop_brief": _brief(),
            }
        )


def test_ecommerce_persists_brief_and_pipeline(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Demo Shop",
            "email": "shop@test.local",
            "package_id": "ecommerce_shop",
            "description": "Shoes and bags for local buyers",
            "customer_id": "cust-shop-1",
            "shop_brief": _brief(),
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert order["product_kind"] == "shop"
    assert float(order["price_eur"]) == 799.0
    assert order["shop_brief"]["store_name"] == "Demo Shop"
    assert order["customer_id"] == "cust-shop-1"

    order["status"] = "paid"
    order["paid_at"] = "2026-08-04T10:00:00+00:00"
    sales._save_order(order)  # noqa: SLF001

    result = sales.start_shop_pipeline(created["order_id"])
    assert result["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert result["factory_hook"]["status"] == "completed"
    assert result["product_id"]
    assert result["published_url"]

    status = sales.public_status(created["order_id"])
    assert status["product_kind"] == "shop"
    assert status["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert status["shop_pipeline_label"]
    assert "Publish" in str(status["shop_pipeline_label"]) or "опублик" in str(
        status["shop_pipeline_label"]
    ).lower() or "Veröffentlich" in str(status["shop_pipeline_label"])
    assert status["download_ready"] is False
    assert status["store_url"] == f"/client/stores/{created['order_id']}"

    store = sales.get_store_for_customer(
        created["order_id"], customer_id="cust-shop-1", email="shop@test.local"
    )
    assert store["ok"] is True
    assert store["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert len(store["r3_sections"]) >= 4

    with pytest.raises(ValueError, match="forbidden"):
        sales.get_store_for_customer(
            created["order_id"], customer_id="other", email="x@y.z"
        )

    again = sales.enqueue_shop_factory(created["order_id"])
    assert again["shop_pipeline"] == SHOP_PIPELINE_PUBLISHED
    assert again["product_id"] == result["product_id"]


def test_shop_brief_features_and_integrations():
    b = validate_shop_brief(
        _brief(
            logo_need="need_new_logo",
            product_categories=["Women", "Men"],
            need_variants=True,
            need_promo_codes=True,
            integrations=["instagram_shop", "meta_pixel"],
            style="luxury",
        )
    )
    assert b["logo_need"] == "need_new_logo"
    assert b["product_categories"] == ["Women", "Men"]
    assert b["need_variants"] is True
    assert b["need_promo_codes"] is True
    assert "instagram_shop" in b["integrations"]
    assert b["style"] == "luxury"
