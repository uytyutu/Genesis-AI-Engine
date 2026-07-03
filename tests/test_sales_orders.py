"""Sprint 1 — Genesis Sales order flow tests."""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def _client(tmp_path: Path) -> TestClient:
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    get_integration(memory)
    return TestClient(app)


def test_sales_packages(tmp_path: Path):
    client = _client(tmp_path)
    res = client.get("/api/sales/packages")
    assert res.status_code == 200
    packages = res.json()["packages"]
    assert len(packages) == 3
    ids = {p["id"] for p in packages}
    assert ids == {"basic", "business", "premium"}


def test_create_sales_order_and_list(tmp_path: Path):
    client = _client(tmp_path)
    res = client.post(
        "/api/sales/orders",
        json={
            "business_name": "Кафе Уют",
            "description": "Уютное кафе с завтраками и кофе",
            "city": "Берлин",
            "phone": "+49 123",
            "whatsapp": "+49 123",
            "needs_logo": True,
            "needs_domain": False,
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["order_id"].startswith("ord-")
    assert body["price_eur"] == 650
    assert "Спасибо" in body["message"]
    assert len(body["deliverables"]) > 0

    listed = client.get("/api/sales/orders")
    assert listed.status_code == 200
    orders = listed.json()["orders"]
    assert any(o["order_id"] == body["order_id"] for o in orders)
    assert orders[0]["status"] == "awaiting_payment"


def test_confirm_and_start_production(tmp_path: Path):
    client = _client(tmp_path)
    created = client.post(
        "/api/sales/orders",
        json={
            "business_name": "Автосервис Pro",
            "description": "Ремонт авто премиум класса",
            "city": "Мюнхен",
            "package_id": "basic",
        },
    ).json()
    order_id = created["order_id"]

    confirm = client.post(f"/api/sales/orders/{order_id}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["order"]["status"] == "confirmed"

    start = client.post(f"/api/sales/orders/{order_id}/start-production")
    assert start.status_code == 200
    data = start.json()
    assert data["product_id"]
    assert data["order"]["status"] == "in_production"
