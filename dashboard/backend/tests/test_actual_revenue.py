"""Actual revenue vs farm potential — no mixing."""

from pathlib import Path

from app.integration.finance_service import FinanceService
from app.integration.real_money_service import get_actual_revenue, get_farm_potential


def test_actual_revenue_from_settlements_only(tmp_path: Path):
    fin = FinanceService(tmp_path)
    fin.credit_order_payment(
        99.0,
        "Webhook order",
        provider="stripe",
        external_id="cs_live_test",
    )
    inputs = fin.real_money_inputs()
    actual = get_actual_revenue(
        finance_snapshot=inputs["finance_snapshot"],
        settlements=inputs["settlements"],
    )
    assert actual["paid_by_client_eur"] == 99.0
    assert actual["available_for_withdrawal_eur"] == 0.0
    assert actual["pending_settlement_eur"] == 99.0
    assert actual["payment_count"] == 1


def test_farm_potential_not_stripe(tmp_path: Path):
    farm = get_farm_potential(
        farm_state={"total_earned_eur": 121.0, "today_earned_eur": 2.5, "total_tasks_done": 2000}
    )
    assert farm["farm_journal_eur"] == 121.0
    assert "Не Stripe" in farm["detail_ru"]
