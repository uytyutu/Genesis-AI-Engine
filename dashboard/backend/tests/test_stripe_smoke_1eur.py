"""Stripe smoke €1 package — ENV-gated."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.factory_service import FactoryService
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.sales_order_service import SalesOrderService


def test_smoke_package_requires_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GENESIS_STRIPE_SMOKE", raising=False)
    sales = SalesOrderService(tmp_path, FactoryIntentService(tmp_path, FactoryService(tmp_path)))
    with pytest.raises(ValueError, match="smoke_disabled"):
        sales.create_order(
            {
                "business_name": "Smoke",
                "description": "test",
                "email": "a@b.com",
                "package_id": "smoke",
            }
        )


def test_smoke_listed_in_packages_when_show_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STRIPE_SMOKE", "1")
    monkeypatch.setenv("GENESIS_SHOW_SMOKE_PACKAGE", "1")
    sales = SalesOrderService(tmp_path, FactoryIntentService(tmp_path, FactoryService(tmp_path)))
    ids = {p["id"] for p in sales.packages()}
    assert "smoke" in ids
    smoke = next(p for p in sales.packages() if p["id"] == "smoke")
    assert float(smoke["price_eur"]) == 1.0

    created = sales.create_order(
        {
            "business_name": "Smoke",
            "description": "test",
            "email": "a@b.com",
            "package_id": "smoke",
            "city": "Berlin",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order is not None
    assert float(order["price_eur"]) == 1.0
    assert order["package_id"] == "smoke"


def test_smoke_checkout_without_ui_listing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """GENESIS_STRIPE_SMOKE alone enables checkout; UI listing needs SHOW flag."""
    monkeypatch.setenv("GENESIS_STRIPE_SMOKE", "1")
    monkeypatch.delenv("GENESIS_SHOW_SMOKE_PACKAGE", raising=False)
    sales = SalesOrderService(tmp_path, FactoryIntentService(tmp_path, FactoryService(tmp_path)))
    assert "smoke" not in {p["id"] for p in sales.packages()}
    created = sales.create_order(
        {
            "business_name": "Smoke",
            "description": "test",
            "email": "a@b.com",
            "package_id": "smoke",
            "city": "Berlin",
        }
    )
    assert created["order_id"]
    assert sales.get_order(created["order_id"])["package_id"] == "smoke"


def test_smoke_not_listed_without_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("GENESIS_STRIPE_SMOKE", raising=False)
    monkeypatch.delenv("GENESIS_SHOW_SMOKE_PACKAGE", raising=False)
    sales = SalesOrderService(tmp_path, FactoryIntentService(tmp_path, FactoryService(tmp_path)))
    assert "smoke" not in {p["id"] for p in sales.packages()}
