"""Payout Manager — official withdraw paths; Execution never gets a withdraw CTA."""

from app.integration.money_monitor_service import build_money_monitor
from app.integration.swarm_bridge import ensure_swarm_importable


def test_payout_manager_stripe_withdrawable():
    ensure_swarm_importable()
    from swarm.payout_manager import build_payout_manager

    panel = build_payout_manager(
        finance_snapshot={
            "paid_by_client_eur": 200.0,
            "pending_settlement_eur": 0.0,
            "available_for_withdrawal_eur": 150.0,
            "pending_payouts_eur": 0.0,
        },
        payout_history=[],
        payment_connected=True,
        demo_mode=False,
        sandbox=False,
        farm_state={"llm_cost_eur": 10.0, "verified_spend_eur": 5.0},
    )
    assert panel["kpi"]["revenue_eur"] == 200.0
    assert panel["kpi"]["execution_cost_eur"] == 15.0
    assert panel["kpi"]["real_profit_eur"] == 185.0
    stripe = next(s for s in panel["sources"] if s["id"] == "stripe_path_a")
    assert stripe["withdrawable"] is True
    assert stripe["cta"] == "virtus_api"
    assert panel["summary"]["any_withdrawable"] is True
    assert all(e["role"] == "execution" for e in panel["execution_not_payout"])


def test_payout_manager_sandbox_blocks_withdraw():
    ensure_swarm_importable()
    from swarm.payout_manager import build_payout_manager

    panel = build_payout_manager(
        finance_snapshot={"available_for_withdrawal_eur": 99.0, "paid_by_client_eur": 99.0},
        payment_connected=True,
        sandbox=True,
    )
    stripe = next(s for s in panel["sources"] if s["id"] == "stripe_path_a")
    assert stripe["withdrawable"] is False
    assert "Sandbox" in stripe["withdraw_status_ru"]


def test_payout_manager_toloka_not_a_source():
    ensure_swarm_importable()
    from swarm.payout_manager import build_payout_manager

    panel = build_payout_manager(finance_snapshot={})
    ids = {s["id"] for s in panel["sources"]}
    assert "toloka_requester" not in ids
    exec_ids = {e["id"] for e in panel["execution_not_payout"]}
    assert "toloka_requester" in exec_ids


def test_money_monitor_includes_payout_manager():
    panel = build_money_monitor(
        farm_state={"total_earned_eur": 10, "llm_cost_eur": 1, "total_tasks_done": 1},
        finance_inputs={
            "finance_snapshot": {"available_for_withdrawal_eur": 0, "paid_by_client_eur": 0},
            "transactions": [],
            "pending_payments": [],
            "payout_history": [],
            "payment_connected": False,
            "demo_mode": False,
            "sandbox": False,
        },
    )
    assert "payout_manager" in panel
    assert panel["payout_manager"]["title_ru"] == "Payout Manager"
    assert "Execution" in panel["toloka_role_ru"] or "execution" in panel["toloka_role_ru"].lower()
