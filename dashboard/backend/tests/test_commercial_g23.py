"""G2.X — Commercial catalog honesty (active services + Coming Soon channels)."""

from __future__ import annotations

from pathlib import Path

from app.integration.commercial_catalog_g23 import (
    ENGINE_ID,
    LANDING_PACKAGES_EUR,
    VECTOR_MONTHLY_EUR,
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
    assert "seo_audit" not in sellable
    assert "whatsapp_ai_bot" not in sellable
    assert "telegram_ai_bot" not in sellable


def test_landing_prices_locked():
    assert LANDING_PACKAGES_EUR == {"basic": 350, "business": 650, "premium": 1200}
    for pid, eur in LANDING_PACKAGES_EUR.items():
        assert _PACKAGES[pid]["price_eur"] == eur


def test_unready_channels_stay_coming_soon():
    by_id = {r["id"]: r for r in commercial_catalog_rows()}
    # Channel SKUs collapsed into ai_business_bot — Meta channels connect after pay
    assert "whatsapp_ai_bot" not in by_id
    assert "instagram_ai_bot" not in by_id
    assert by_id["ai_business_bot"]["cta"] == "order_now"
    assert by_id["crm_starter"]["cta"] == "coming_soon"


def test_website_services_are_orderable():
    ones = [r for r in commercial_catalog_rows() if r.get("group") == "website_services"]
    assert len(ones) >= 5
    live_ids = {"ai_website_analysis", "website_repair"}
    for r in ones:
        assert r["cta_href"] and str(r["cta_href"]).startswith("/order/service/")
        if r["id"] in live_ids:
            assert r["availability"] == "available"
            assert r["cta"] == "order_now"
        else:
            assert r["availability"] == "coming_soon"
            assert r["cta"] == "coming_soon"
    assert "seo_audit" not in sellable_online_ids()
    assert "ai_website_analysis" in sellable_online_ids()


def test_addon_packages_exist_in_sales():
    for pid in (
        "seo_audit",
        "speed_optimization",
        "security_check",
        "ai_website_analysis",
        "website_repair",
    ):
        assert pid in _PACKAGES
        assert _PACKAGES[pid]["product_kind"] == "addon"


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
