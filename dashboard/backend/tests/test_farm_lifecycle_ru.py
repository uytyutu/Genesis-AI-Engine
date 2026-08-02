from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.farm_lifecycle_ru import (
    STAGE_BALANCE_INCREASED,
    STAGE_PAYMENT_CONFIRMED,
    STAGE_PAYMENT_PENDING,
    STAGE_REWARD_ESTIMATE,
    STAGE_SPEND_ACCEPTED,
    detail_for_stage,
    lifecycle_chain,
    money_direction_for_adapter,
    payout_ui_block,
    stage_title,
)


def test_stage_titles_ru_honest():
    assert stage_title("task_accepted") == "Задача взята в работу"
    assert stage_title("task_completed") == "Задача обработана"
    assert "Spend" in stage_title("spend_accepted")
    assert "моделирование" in stage_title("reward_estimate").lower()
    assert "Earn" in stage_title("payment_pending")
    assert stage_title("payment_confirmed") == "Платформа подтвердила оплату"


def test_toloka_is_spend_not_earn_pending():
    assert money_direction_for_adapter("toloka") == "spend"
    assert money_direction_for_adapter("toloka_submit") == "spend"
    stages = lifecycle_chain(
        ok=True,
        sandbox=False,
        money_direction="spend",
        pay_eur=0.05,
    )
    assert stages == [
        "task_accepted",
        "task_completed",
        "spend_accepted",
    ]
    assert STAGE_REWARD_ESTIMATE not in stages
    assert STAGE_PAYMENT_PENDING not in stages
    assert STAGE_PAYMENT_CONFIRMED not in stages


def test_legacy_live_exchange_no_longer_forces_pending_on_model():
    """Old call shape: live_exchange alone must NOT invent Earn pending."""
    stages = lifecycle_chain(
        ok=True,
        sandbox=False,
        live_exchange=True,
        pay_eur=0.05,
        money_direction="earn_model",
    )
    assert stages == [
        "task_accepted",
        "task_completed",
        "reward_estimate",
    ]
    assert STAGE_PAYMENT_PENDING not in stages


def test_earn_live_awaited_pending_without_real_payout():
    stages = lifecycle_chain(
        ok=True,
        sandbox=False,
        money_direction="earn_live",
        pay_eur=0.05,
        earn_payout_awaited=True,
    )
    assert STAGE_PAYMENT_PENDING in stages
    assert STAGE_PAYMENT_CONFIRMED not in stages
    assert STAGE_BALANCE_INCREASED not in stages


def test_lifecycle_chain_sandbox_estimate_only():
    stages = lifecycle_chain(
        ok=True, sandbox=True, money_direction="earn_model", pay_eur=0.02
    )
    assert stages == [
        "task_accepted",
        "task_completed",
        "reward_estimate",
    ]
    assert STAGE_PAYMENT_PENDING not in stages


def test_lifecycle_chain_real_payout_appends_confirmed():
    stages = lifecycle_chain(
        ok=True,
        sandbox=False,
        money_direction="earn_live",
        pay_eur=0.05,
        earn_payout_awaited=True,
        real_payout=True,
    )
    assert STAGE_PAYMENT_CONFIRMED in stages
    assert stages[-1] == STAGE_PAYMENT_CONFIRMED


def test_detail_spend_accepted_no_payout_expected():
    text = detail_for_stage(STAGE_SPEND_ACCEPTED, task_label="ds-1")
    assert "Spend" in text or "Requester" in text or "заказчик" in text.lower()
    assert "не" in text.lower()


def test_detail_payment_confirmed_requires_real_payout():
    fake = detail_for_stage(
        STAGE_PAYMENT_CONFIRMED,
        task_label="demo-1",
        pay_eur=0.01,
        real_payout=False,
    )
    assert "отказ" in fake

    real = detail_for_stage(
        STAGE_PAYMENT_CONFIRMED,
        task_label="demo-1",
        pay_eur=0.05,
        payout_id="84392711",
        real_payout=True,
    )
    assert "84392711" in real
    assert "0.0500" in real


def test_detail_reward_estimate_is_modeling():
    text = detail_for_stage(
        STAGE_REWARD_ESTIMATE,
        task_label="demo-2",
        pay_eur=0.02,
        sandbox=False,
    )
    assert "моделирование" in text.lower() or "оценка" in text.lower()
    assert "REAL" in text or "не" in text.lower()


def test_payout_ui_block_ru():
    block = payout_ui_block(threshold_usd=10.0)
    assert len(block["steps"]) >= 3
    assert block["auto_payout"] is False
    assert "Live Earn" in block["note"] or "Hard REAL" in block["note"]
