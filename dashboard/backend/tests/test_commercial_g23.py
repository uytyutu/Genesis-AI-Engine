"""G2.3 — Commercial Readiness (catalog honesty · Landing payments path)."""

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
    assert sellable_online_ids() == frozenset({"landing_website"})


def test_landing_prices_locked():
    assert LANDING_PACKAGES_EUR == {"basic": 350, "business": 650, "premium": 1200}
    for pid, eur in LANDING_PACKAGES_EUR.items():
        assert _PACKAGES[pid]["price_eur"] == eur


def test_vector_monthly_tariffs_published_not_sold():
    assert VECTOR_MONTHLY_EUR == {"starter": 99, "business": 199, "professional": 349}
    monthly = [r for r in commercial_catalog_rows() if r["id"].startswith("vector_")]
    paid = [r for r in monthly if r["id"] != "vector_employee"]
    assert paid
    assert all(r["cta"] == "coming_soon" for r in paid)


def test_coming_soon_services_have_prices():
    ones = [r for r in commercial_catalog_rows() if r["category"] == "one_time"]
    assert len(ones) >= 5
    assert all(r["availability"] == "coming_soon" for r in ones)
    assert all("€" in r["price_label"] or "Individual" in r["price_label"] for r in ones)


def test_portal_catalog_does_not_sell_unready_analytics():
    by_id = {p.product_id: p for p in default_product_catalog()}
    assert by_id["prod_analytics"].availability == "coming_soon"
    assert by_id["prod_crm"].availability == "coming_soon"
    assert by_id["prod_website"].availability == "available"


def test_landing_payment_path_order_to_paid_status(tmp_path: Path):
    """Sellable product path: create order → mark paid → public status paid."""
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
