"""Finance Center and Company API tests."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.integration.context import get_integration, reset_integration
from app.main import app


def test_finance_center_no_provider(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text(
        '{"owner_name": "Рамиш"}',
        encoding="utf-8",
    )
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/finance")
    assert res.status_code == 200
    data = res.json()
    assert data["owner_name"] == "Рамиш"
    assert data["payment_connected"] is False
    assert data["platform_balance_eur"] == 0.0
    assert "не хранит средства" in data["data_source_note"].lower() or "не подключена" in data["data_source_note"].lower()
    assert data["withdrawal_enabled"] is False
    assert data["wallets"]
    assert len(data["wallets"]) == 5
    assert data["payout_history"] == []
    assert data["demo_mode"] is False

    reset_integration()


def test_finance_center_with_provider_snapshot(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text('{"owner_name": "Рамиш"}', encoding="utf-8")
    (memory / "finance_config.json").write_text(
        json.dumps(
            {
                "payment_provider": "stripe",
                "payment_provider_label": "Stripe",
                "last_sync_at": "2026-07-02T12:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    (memory / "finance_snapshot.json").write_text(
        json.dumps(
            {
                "source": "stripe",
                "platform_balance_eur": 12483.72,
                "revenue_today_eur": 327.40,
                "revenue_month_eur": 8214.90,
                "gross_revenue_eur": 12483.72,
                "expenses_eur": 1533.42,
                "net_profit_eur": 10950.30,
                "available_for_withdrawal_eur": 7950.30,
                "pending_payouts_eur": 264.00,
                "products_sold": 184,
                "clients": 96,
                "active_subscriptions": 51,
            }
        ),
        encoding="utf-8",
    )
    (memory / "finance_transactions.jsonl").write_text(
        '{"at":"2026-07-02T18:00:00Z","amount_eur":49,"label":"Landing Page","category":"sale"}\n',
        encoding="utf-8",
    )
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/finance")
    assert res.status_code == 200
    data = res.json()
    assert data["payment_connected"] is True
    assert data["platform_balance_eur"] == 12483.72
    assert data["revenue_today_eur"] == 327.40
    assert len(data["recent_transactions"]) == 1
    assert data["recent_transactions"][0]["amount_eur"] == 49.0
    assert data["withdrawal_enabled"] is True
    assert len(data["wallets"]) == 5
    assert data["wallets"][1]["id"] == "stripe"
    assert data["wallets"][1]["connected"] is True

    reset_integration()


def test_payment_webhook_records_sale(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text('{"owner_name": "Рамиш"}', encoding="utf-8")
    (memory / "finance_config.json").write_text(
        json.dumps({"payment_provider": "stripe", "payment_provider_label": "Stripe"}),
        encoding="utf-8",
    )
    get_integration(memory)

    client = TestClient(app)
    res = client.post(
        "/api/webhooks/payment",
        json={"amount_eur": 49.0, "label": "Landing стоматология", "provider": "stripe"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["amount_eur"] == 49.0
    assert data["pending"] is True
    assert data["payment_id"]

    fin = client.get("/api/owner/finance").json()
    assert fin["revenue_today_eur"] == 0.0
    assert len(fin["pending_payments"]) == 1
    assert fin["pending_payments"][0]["amount_eur"] == 49.0

    confirm = client.post(f"/api/owner/finance/payments/{data['payment_id']}/confirm")
    assert confirm.status_code == 200
    assert confirm.json()["pending"] is False

    fin2 = client.get("/api/owner/finance").json()
    assert fin2["revenue_today_eur"] == 49.0
    assert fin2["payment_connected"] is True
    assert len(fin2["recent_transactions"]) == 1
    assert fin2["pending_payments"] == []

    reset_integration()


def test_company_overview(tmp_path: Path):
    reset_integration()
    memory = tmp_path / "memory"
    memory.mkdir()
    (memory / "launcher_config.json").write_text('{"owner_name": "Рамиш"}', encoding="utf-8")
    get_integration(memory)

    client = TestClient(app)
    res = client.get("/api/owner/company")
    assert res.status_code == 200
    data = res.json()
    assert data["company_name"] == "Genesis Company"
    assert "digital_employees_active" in data
    assert "ai_team" in data
    assert data["gross_revenue_eur"] == 0.0
    assert "pulse" in data
    assert len(data["pulse"]["metrics"]) == 6
    assert data["morning_brief"]["headline"]

    reset_integration()
