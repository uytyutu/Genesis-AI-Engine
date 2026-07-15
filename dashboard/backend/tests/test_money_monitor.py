"""Money monitor — three money lanes."""

from app.integration.money_monitor_service import build_money_monitor


def test_three_lanes_training_not_bank():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 112.75, "llm_cost_eur": 0.72, "total_tasks_done": 3700},
        payment_monitor={"monitor": {"toloka": {"connected": True}}, "payout": {"has_withdraw_ready": False, "threshold_usd": 10}},
        opportunities=[],
        toloka_submit_count=1253,
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


def test_b2b_proven_when_won():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 50, "llm_cost_eur": 1, "total_tasks_done": 100},
        opportunities=[{"status": "won", "revenue_eur": 250}],
    )
    assert panel["model_proven"] is True
    assert panel["lanes"][2]["amount_eur"] == 250


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
    )
    assert panel["withdraw_alert"]["active"] is True
    assert panel["withdraw_alert"]["level"] == "green"
