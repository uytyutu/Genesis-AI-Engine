"""Assisted Deployment — ZIP Only vs Assisted preference (no host passwords)."""

from __future__ import annotations

from pathlib import Path

from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def get_product(self, product_id: str):
        return {"product_id": product_id} if product_id else None


class _Intent:
    def __init__(self) -> None:
        self._factory = _Factory()


def _ready_order(sales: SalesOrderService, tmp_path: Path) -> str:
    created = sales.create_order(
        {
            "business_name": "Praxis Test",
            "description": "Zahnarztpraxis Landing Path A Test",
            "city": "Köln",
            "email": "test@example.com",
            "package_id": "basic",
            "market_code": "DE",
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order
    order["status"] = "in_production"
    order["product_id"] = "prod-assist-1"
    order["paid_at"] = "2026-07-19T12:00:00+00:00"
    sales._save_order(order)
    return order_id


def test_deployment_preference_zip_only(tmp_path: Path) -> None:
    sales = SalesOrderService(tmp_path, _Intent())
    order_id = _ready_order(sales, tmp_path)

    status = sales.set_deployment_preference(order_id, "zip_only")
    assert status["deployment_preference"] == "zip_only"
    assert status["hosting_provider"] is None
    assert status["assisted_guide"] is None
    assert status["download_ready"] is True

    stored = sales.get_order(order_id)
    assert stored["deployment_preference"] == "zip_only"
    for banned in ("password", "ftp_password", "hosting_password", "credentials", "api_token"):
        assert banned not in stored


def test_deployment_preference_assisted_notifies(tmp_path: Path) -> None:
    sales = SalesOrderService(tmp_path, _Intent())
    order_id = _ready_order(sales, tmp_path)

    status = sales.set_deployment_preference(
        order_id, "assisted", hosting_provider="hetzner"
    )
    assert status["deployment_preference"] == "assisted"
    assert status["hosting_provider"] == "hetzner"
    guide = status["assisted_guide"]
    assert guide is not None
    assert "variant_a" in guide
    assert "variant_b" in guide
    assert "Hosting-Passwort" in guide["never_stores"]

    notes = OwnerNotificationService(tmp_path).list_recent(5)
    assert any(n.get("order_id") == order_id for n in notes)
    assert any("Assisted Deployment" in str(n.get("title", "")) for n in notes)

    stored = sales.get_order(order_id)
    assert stored is not None
    for banned in ("ftp_password", "hosting_password", "api_token", "credentials"):
        assert banned not in stored


def test_deployment_preference_before_zip_rejected(tmp_path: Path) -> None:
    sales = SalesOrderService(tmp_path, _Intent())
    created = sales.create_order(
        {
            "business_name": "Praxis Early",
            "description": "Noch ohne ZIP",
            "package_id": "basic",
            "market_code": "DE",
        }
    )
    try:
        sales.set_deployment_preference(created["order_id"], "zip_only")
        assert False, "expected download_not_ready"
    except ValueError as exc:
        assert str(exc) == "download_not_ready"


def test_public_status_exposes_unset_preference(tmp_path: Path) -> None:
    sales = SalesOrderService(tmp_path, _Intent())
    order_id = _ready_order(sales, tmp_path)
    status = sales.public_status(order_id)
    assert status["deployment_preference"] == "unset"
    assert status["assisted_guide"] is None
