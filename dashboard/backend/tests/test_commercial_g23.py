"""G2.X — Commercial catalog honesty (Website Services agency LIVE)."""

from __future__ import annotations

from pathlib import Path

from app.integration.commercial_catalog_g23 import (
    ENGINE_ID,
    LANDING_PACKAGES_EUR,
    WEBSITE_SERVICE_PRICES_EUR,
    assert_no_fake_buy_buttons,
    commercial_catalog_rows,
    sellable_online_ids,
)
from app.integration.sales_order_service import SalesOrderService, _PACKAGES
from app.portal.product import default_product_catalog


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-g23"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def test_engine_and_no_fake_buy():
    assert ENGINE_ID == "commercial_catalog_g23_v1"
    assert_no_fake_buy_buttons()
    sellable = sellable_online_ids()
    assert "landing_website" in sellable
    assert "ai_website_analysis" in sellable
    assert "website_repair" in sellable
    assert "ai_business_bot" in sellable
    assert "seo_audit" in sellable
    assert "reputation_audit" in sellable
    assert "ai_seo_monitoring" in sellable
    assert "whatsapp_ai_bot" not in sellable
    assert "telegram_ai_bot" not in sellable


def test_landing_prices_locked():
    assert LANDING_PACKAGES_EUR == {"basic": 350, "business": 650, "premium": 1200}
    for pid, eur in LANDING_PACKAGES_EUR.items():
        assert _PACKAGES[pid]["price_eur"] == eur


def test_unready_channels_stay_coming_soon():
    by_id = {r["id"]: r for r in commercial_catalog_rows()}
    assert "whatsapp_ai_bot" not in by_id
    assert "instagram_ai_bot" not in by_id
    assert by_id["ai_business_bot"]["cta"] == "order_now"
    assert by_id["crm_starter"]["cta"] == "coming_soon"


def test_website_services_are_orderable():
    ones = [r for r in commercial_catalog_rows() if r.get("group") == "website_services"]
    assert len(ones) >= 12
    for r in ones:
        href = str(r["cta_href"] or "")
        if r["id"] == "ecommerce_shop":
            assert href.startswith("/order/shop")
        else:
            assert href.startswith("/order/service/")
        assert r["availability"] == "available"
        assert r["cta"] == "order_now"
        assert r["id"] in sellable_online_ids()
        assert r["id"] in WEBSITE_SERVICE_PRICES_EUR


def test_addon_packages_exist_in_sales():
    for pid in WEBSITE_SERVICE_PRICES_EUR:
        assert pid in _PACKAGES
        kind = _PACKAGES[pid]["product_kind"]
        if pid == "ecommerce_shop":
            assert kind == "shop"
        else:
            assert kind == "addon"
        assert int(_PACKAGES[pid]["price_eur"]) == WEBSITE_SERVICE_PRICES_EUR[pid]


def test_portal_catalog_does_not_sell_unready_analytics():
    by_id = {p.product_id: p for p in default_product_catalog()}
    assert by_id["prod_analytics"].availability == "coming_soon"
    assert by_id["prod_crm"].availability == "coming_soon"
    assert by_id["prod_website"].availability == "available"


def test_landing_payment_path_order_to_paid_status(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "G23 Shop",
            "email": "buyer@g23.test",
            "package_id": "basic",
            "description": "Commercial readiness path",
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "paid"
    order["paid_at"] = "2026-07-23T10:00:00+00:00"
    sales._save_order(order)  # noqa: SLF001

    status = sales.public_status(order_id)
    assert status["paid"] is True
    assert status["order_id"] == order_id
    assert "email" not in status


def test_addon_order_keeps_package_id(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "SEO Client",
            "email": "seo@g23.test",
            "package_id": "seo_audit",
            "description": "Standalone SEO",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert order["package_id"] == "seo_audit"
    assert float(order.get("price_eur") or 0) == 249.0
    status = sales.public_status(created["order_id"])
    assert status.get("service_name")
    assert status.get("eta_label") == "2–4"


def test_new_agency_sku_reputation(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Rep Co",
            "email": "rep@g23.test",
            "package_id": "reputation_audit",
            "description": "Reviews check",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert float(order.get("price_eur") or 0) == 149.0
