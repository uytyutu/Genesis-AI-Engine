"""Real money tiers — Получено / Ожидается / Прогноз."""

from pathlib import Path

from app.integration.money_monitor_service import build_money_monitor
from app.integration.real_money_service import build_real_money_tiers


def test_three_lanes_training_not_bank():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 112.75, "llm_cost_eur": 0.72, "total_tasks_done": 3700},
        payment_monitor={"monitor": {"toloka": {"connected": True}}, "payout": {"has_withdraw_ready": False, "threshold_usd": 10}},
        opportunities=[],
        toloka_submit_count=1253,
        finance_inputs={
            "finance_snapshot": {},
            "transactions": [],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": False,
            "demo_mode": False,
        },
    )
    assert panel["model_proven"] is False
    assert len(panel["lanes"]) == 3
    ledger = panel["lanes"][0]
    assert ledger["id"] == "training_ledger"
    assert "не выводить" in ledger["status_ru"].lower() or "не банк" in ledger["detail_ru"].lower()
    factory = panel["lanes"][1]
    assert factory["id"] == "exchange_factory"
    assert "1253" in factory["status_ru"]
    b2b = panel["lanes"][2]
    assert b2b["id"] == "b2b_client"
    assert b2b["amount_eur"] == 0
    rm = panel["real_money"]
    assert rm["training"]["amount_eur"] == 112.75
    assert rm["received"]["amount_eur"] == 0.0


def test_won_without_external_payment_not_proven():
    """Won opportunity alone must NOT prove model or count as received."""
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 50, "llm_cost_eur": 1, "total_tasks_done": 100},
        opportunities=[{"status": "won", "revenue_eur": 250}],
        finance_inputs={
            "finance_snapshot": {},
            "transactions": [],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": True,
            "demo_mode": False,
        },
    )
    assert panel["model_proven"] is False
    assert panel["lanes"][2]["amount_eur"] == 0
    assert panel["real_money"]["received"]["amount_eur"] == 0.0


def test_received_only_with_external_transaction():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 999, "total_tasks_done": 1},
        finance_inputs={
            "finance_snapshot": {
                "paid_by_client_eur": 147.35,
                "pending_settlement_eur": 147.35,
                "available_for_withdrawal_eur": 0,
            },
            "transactions": [
                {
                    "amount_eur": 147.35,
                    "provider": "stripe",
                    "payment_id": "pi_abc",
                    "category": "sale",
                    "at": "2026-07-15",
                }
            ],
            "settlements": [
                {
                    "amount_eur": 147.35,
                    "provider": "stripe",
                    "payment_id": "pi_abc",
                    "paid_at": "2026-07-15",
                    "settlement_status": "pending_settlement",
                    "label": "Audit",
                }
            ],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": True,
            "demo_mode": False,
        },
    )
    assert panel["model_proven"] is True
    assert panel["real_money"]["paid_by_client"]["amount_eur"] == 147.35
    assert panel["real_money"]["available"]["amount_eur"] == 0.0
    assert panel["real_money"]["training"]["amount_eur"] == 999.0
    assert panel["lanes"][2]["amount_eur"] == 147.35


def test_training_never_counts_as_received():
    tiers = build_real_money_tiers(
        finance_snapshot={},
        transactions=[
            {
                "amount_eur": 50.0,
                "provider": "stripe",
                "payment_id": "x",
                "category": "training",
            }
        ],
        pending_payments=[],
        payout_history=[],
        payment_connected=True,
        demo_mode=False,
        farm_training_eur=121.0,
    )
    assert tiers["paid_by_client"]["amount_eur"] == 0.0
    assert tiers["training"]["amount_eur"] == 121.0


def test_pending_from_provider_queue(tmp_path: Path):
    tiers = build_real_money_tiers(
        finance_snapshot={"pending_settlement_eur": 100.0},
        transactions=[],
        pending_payments=[{"amount_eur": 320.0, "provider": "stripe", "payment_id": "p1", "label": "Клиент A"}],
        payout_history=[],
        payment_connected=True,
        demo_mode=False,
        farm_training_eur=0,
    )
    assert tiers["pending"]["amount_eur"] == 420.0


def test_demo_mode_zeros_received():
    tiers = build_real_money_tiers(
        finance_snapshot={},
        transactions=[{"amount_eur": 500, "provider": "stripe", "payment_id": "x", "category": "sale"}],
        pending_payments=[],
        payout_history=[],
        payment_connected=True,
        demo_mode=True,
        farm_training_eur=0,
    )
    assert tiers["paid_by_client"]["amount_eur"] == 0.0


def test_forecast_from_pipeline():
    tiers = build_real_money_tiers(
        finance_snapshot={},
        transactions=[],
        pending_payments=[],
        payout_history=[],
        payment_connected=False,
        demo_mode=False,
        farm_training_eur=0,
        opportunities=[
            {"status": "qualified", "revenue_eur": 200},
            {"status": "won", "revenue_eur": 500},
        ],
    )
    assert tiers["forecast"]["b2b_pipeline_eur"] == 200.0


def test_sales_funnel_counts():
    from app.integration.mission2_kpi_service import build_sales_funnel_progress

    rows = [
        {"id": "1", "status": "new", "meta": {}},
        {
            "id": "2",
            "status": "contacted",
            "outreach_status": "sent",
            "proposed_message": "Hello",
            "meta": {"qualification": {"passed": True}},
        },
        {"id": "3", "status": "replied", "outreach_status": "sent", "proposed_message": "Hi", "meta": {"qualification": {"passed": True}}},
        {"id": "4", "status": "won", "outreach_status": "sent", "proposed_message": "Deal", "meta": {"qualification": {"passed": True}}},
    ]
    funnel = build_sales_funnel_progress(rows, received_eur=250.0)
    by_id = {s["id"]: s for s in funnel["steps"]}
    assert by_id["leads_found"]["count"] == 4
    assert by_id["qualification_passed"]["count"] == 3
    assert by_id["letters_prepared"]["count"] == 3
    assert by_id["sent"]["count"] == 3
    assert by_id["replies"]["count"] == 2
    assert by_id["won"]["count"] == 1
    assert by_id["received"]["amount_eur"] == 250.0


def test_money_monitor_includes_sales_funnel():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 121, "total_tasks_done": 2000},
        opportunities=[
            {"status": "new"},
            {"status": "won", "revenue_eur": 300, "meta": {"qualification": {"passed": True}}, "proposed_message": "x", "outreach_status": "sent"},
        ],
        finance_inputs={
            "finance_snapshot": {
                "paid_by_client_eur": 250.0,
                "pending_settlement_eur": 250.0,
                "available_for_withdrawal_eur": 0.0,
            },
            "transactions": [{"amount_eur": 250, "provider": "stripe", "payment_id": "pi_1", "category": "sale", "at": "2026-07-15"}],
            "settlements": [
                {
                    "amount_eur": 250.0,
                    "provider": "stripe",
                    "payment_id": "pi_1",
                    "paid_at": "2026-07-15",
                    "settlement_status": "pending_settlement",
                    "label": "Order",
                }
            ],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": True,
            "demo_mode": False,
        },
    )
    sf = panel["sales_funnel"]
    assert sf["steps"][-1]["amount_eur"] == 250.0
    assert panel["model_proven"] is True


def test_withdraw_alert_green():
    panel = build_money_monitor(
        farm_state={},
        payment_monitor={
            "payout": {
                "has_withdraw_ready": True,
                "pending_alerts": [{"message": "Пора выводить $12"}],
                "threshold_usd": 10,
            }
        },
        finance_inputs={
            "finance_snapshot": {},
            "transactions": [],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": False,
            "demo_mode": False,
        },
    )
    assert panel["withdraw_alert"]["active"] is True
    assert panel["withdraw_alert"]["level"] == "green"
