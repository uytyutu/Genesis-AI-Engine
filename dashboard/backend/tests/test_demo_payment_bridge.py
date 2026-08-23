"""D0 Demo Payment Bridge — demo orders only, never Production money."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.demo_payment import (
    assert_demo_payment_allowed,
    demo_payment_bridge_enabled,
    is_demo_order,
    matches_demo_company_name,
    should_tag_demo_order,
)
from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        oid = getattr(intent, "order_id", None) or "x"
        return {"product_id": f"web-{str(oid)[:12]}"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def _pipeline(tmp_path: Path) -> tuple[SalesOrderService, RevenuePipelineService, FinanceService]:
    sales = SalesOrderService(tmp_path, _Factory())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)
    return sales, revenue, finance


def test_nordlicht_is_demo_company():
    assert matches_demo_company_name("Nordlicht Möbel GmbH")
    assert matches_demo_company_name("Nordlicht Moebel")
    assert matches_demo_company_name("Golden Test Baeckerei Nord")
    assert should_tag_demo_order(
        {"business_name": "Golden Website Café", "email": "buyer@firma.de"}
    )
    assert should_tag_demo_order(
        {"business_name": "Acme Dental", "email": "golden.test+v2@example.com"}
    )
    assert not matches_demo_company_name("Acme Dental Berlin")
    assert not should_tag_demo_order(
        {"business_name": "Acme Dental Berlin", "email": "owner@acme.de"}
    )

def test_production_lock_blocks_bridge(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PRODUCTION", "1")
    monkeypatch.delenv("GENESIS_ALLOW_DEMO_PAYMENT", raising=False)
    monkeypatch.delenv("GENESIS_DEMO_MODE", raising=False)
    monkeypatch.delenv("GENESIS_DEMO_PAYMENT", raising=False)
    assert demo_payment_bridge_enabled() is False
    with pytest.raises(ValueError, match="demo_payment_disabled"):
        assert_demo_payment_allowed({"demo": True, "business_name": "Nordlicht Möbel GmbH"})


def test_demo_bridge_allowed_with_flag(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PRODUCTION", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    assert demo_payment_bridge_enabled() is True


def test_complete_demo_payment_nordlicht(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GENESIS_PRODUCTION", raising=False)
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)

    sales, revenue, finance = _pipeline(tmp_path)
    before = float(finance._load_snapshot().get("gross_revenue_eur") or 0)  # noqa: SLF001

    created = sales.create_order(
        {
            "business_name": "Nordlicht Möbel GmbH",
            "description": "Tischlerei Hamburg Handwerk Premium",
            "email": "info@nordlicht-moebel.de",
            "package_id": "business",
            "city": "Hamburg",
            "demo": True,
        }
    )
    order_id = created["order_id"]
    assert created.get("demo") is True
    assert created.get("payment_mode") == "demo"

    order = sales.get_order(order_id)
    assert order is not None
    assert is_demo_order(order)
    assert should_tag_demo_order({"business_name": "Nordlicht Möbel GmbH", "demo": True})

    status = sales.public_status(order_id)
    assert status["demo"] is True
    assert status["demo_payment_available"] is True
    assert "Demo" in (status.get("demo_payment_banner") or "")

    # Ordinary company cannot use demo pay
    other = sales.create_order(
        {
            "business_name": "Acme Dental Berlin",
            "description": "Zahnarztpraxis Berlin",
            "email": "a@b.de",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    with pytest.raises(ValueError, match="not_a_demo_order"):
        revenue.complete_demo_payment(other["order_id"])

    result = revenue.complete_demo_payment(order_id)
    assert result["ok"] is True
    assert result["demo"] is True
    assert result["payment_mode"] == "demo"

    paid = sales.get_order(order_id)
    assert paid is not None
    assert paid["payment_mode"] == "demo"
    assert paid["payment_provider"] == "demo"
    assert paid["counts_toward_revenue"] is False
    assert paid.get("paid_at")

    after = float(finance._load_snapshot().get("gross_revenue_eur") or 0)  # noqa: SLF001
    assert after == before  # demo must not inflate real finance

    status2 = sales.public_status(order_id)
    assert status2["paid"] is True
    assert status2["demo_payment_available"] is False


def test_explicit_demo_false_regular_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    sales, revenue, _finance = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Regular Cafe GmbH",
            "description": "Cafe in Mitte",
            "email": "cafe@example.de",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert order.get("demo") is not True
    with pytest.raises(ValueError, match="not_a_demo_order"):
        revenue.complete_demo_payment(created["order_id"])
