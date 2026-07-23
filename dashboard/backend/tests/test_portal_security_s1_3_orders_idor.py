"""S1.3 — Orders IDOR (Mission 1 sales orders)."""

from __future__ import annotations

from pathlib import Path

from app.integration.sales_order_service import SalesOrderService
from app.security import is_public_api_path, production_api_allowed


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "prod-test-1"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

    _factory = _Inner()


def test_orders_list_not_public_api():
    assert not is_public_api_path("/api/sales/orders", "GET")
    assert not production_api_allowed("/api/sales/orders", "GET")


def test_order_idor_unknown_id_and_no_email_in_public_status(tmp_path: Path):
    svc = SalesOrderService(tmp_path, _Factory())
    created = svc.create_order(
        {
            "business_name": "Alice Shop",
            "email": "alice-secret@example.com",
            "package_id": "basic",
            "description": "Dental Berlin",
        }
    )
    order_id = created["order_id"]
    status = svc.public_status(order_id)
    blob = str(status).lower()
    assert "alice-secret@example.com" not in blob
    assert "email" not in status

    try:
        svc.public_status("ord-deadbeef00")
        assert False, "expected missing order"
    except ValueError as exc:
        assert str(exc) == "order_not_found"

    try:
        svc.build_client_download("ord-deadbeef00")
        assert False, "expected missing order"
    except ValueError as exc:
        assert str(exc) == "order_not_found"


def test_order_id_is_unguessable_capability_token(tmp_path: Path):
    svc = SalesOrderService(tmp_path, _Factory())
    a = svc.create_order(
        {
            "business_name": "A",
            "email": "a@ex.com",
            "package_id": "basic",
            "description": "A",
        }
    )
    b = svc.create_order(
        {
            "business_name": "B",
            "email": "b@ex.com",
            "package_id": "basic",
            "description": "B",
        }
    )
    assert a["order_id"] != b["order_id"]
    assert a["order_id"].startswith("ord-")
    assert len(a["order_id"]) >= 14
