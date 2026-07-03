"""Revenue Pipeline v1 — pay → auto production → notify."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "dashboard" / "backend"
sys.path.insert(0, str(BACKEND))

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def _client(tmp_path: Path) -> TestClient:
    reset_integration()
    os.environ["GENESIS_PAYMENT_SANDBOX"] = "1"
    memory = tmp_path / "memory"
    memory.mkdir()
    cfg = memory / "finance_config.json"
    cfg.write_text(
        json.dumps({"payment_provider": "sandbox", "payment_provider_label": "Sandbox"}),
        encoding="utf-8",
    )
    get_integration(memory)
    return TestClient(app)


def test_payment_status_sandbox(tmp_path: Path):
    client = _client(tmp_path)
    res = client.get("/api/sales/payment-status")
    assert res.status_code == 200
    body = res.json()
    assert body["configured"] is True
    assert body["sandbox"] is True


def test_revenue_pipeline_full(tmp_path: Path):
    client = _client(tmp_path)
    created = client.post(
        "/api/sales/orders",
        json={
            "business_name": "Revenue Test GmbH",
            "description": "Auto repair shop premium service",
            "package_id": "basic",
        },
    ).json()
    order_id = created["order_id"]
    assert created["price_eur"] == 350

    checkout = client.post(
        f"/api/sales/orders/{order_id}/checkout",
        json={
            "success_url": f"http://localhost:3000/order/status/{order_id}",
            "cancel_url": "http://localhost:3000/order",
        },
    )
    assert checkout.status_code == 200
    assert "checkout_url" in checkout.json()

    paid = client.post(f"/api/sales/orders/{order_id}/pay-sandbox")
    assert paid.status_code == 200
    body = paid.json()
    assert body["product_id"]
    assert "оплату" in body["client_message"].lower() or "работу" in body["client_message"].lower()
    assert body["order"]["timeline"]
    assert body["order"]["next_step"]

    status = client.get(f"/api/sales/orders/{order_id}/status").json()
    assert status["paid"] is True
    assert status["status"] == "in_production"

    listed = client.get("/api/sales/orders").json()["orders"]
    row = next(o for o in listed if o["order_id"] == order_id)
    assert row["paid"] is True
    assert row["product_id"] == body["product_id"]

    notes = client.get("/api/owner/notifications").json()["notifications"]
    assert any("Revenue Test" in n["message"] for n in notes)

    finance = client.get("/api/owner/finance").json()
    assert finance["revenue_today_eur"] >= 350
