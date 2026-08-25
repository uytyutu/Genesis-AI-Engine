"""MC 2.0 Slice 1 — sales order summary fields for Orders / Products desks."""

from __future__ import annotations

from pathlib import Path

from app.integration.sales_order_service import SalesOrderService


class _Factory:
    pass


def test_sales_order_summary_includes_mc_desk_fields(tmp_path: Path):
    memory = tmp_path / "memory"
    memory.mkdir()
    svc = SalesOrderService(memory, _Factory())
    order = {
        "order_id": "ord-mc-1",
        "status": "paid",
        "status_label": "Paid",
        "business_name": "Test GmbH",
        "city": "Berlin",
        "phone": "+49111",
        "whatsapp": "",
        "email": "ceo@test.de",
        "customer_id": "cust-1",
        "package_name": "Website Basic",
        "package_id": "basic",
        "product_kind": "website",
        "price_eur": 299,
        "created_at": "2026-08-25T10:00:00+00:00",
        "product_id": "prod-1",
        "proposal_text": "",
        "paid_at": "2026-08-25T10:01:00+00:00",
    }
    path = memory / "sales_orders.json"
    path.write_text(__import__("json").dumps([order]), encoding="utf-8")

    rows = svc.list_orders(limit=10)
    assert len(rows) == 1
    row = rows[0]
    assert row["email"] == "ceo@test.de"
    assert row["customer_id"] == "cust-1"
    assert row["package_id"] == "basic"
    assert row["product_kind"] == "website"
    assert "download_ready" in row
