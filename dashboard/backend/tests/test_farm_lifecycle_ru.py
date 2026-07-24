from app.integration.swarm_bridge import ensure_swarm_importable

ensure_swarm_importable()
from swarm.farm_lifecycle_ru import (
    STAGE_BALANCE_INCREASED,
    STAGE_PAYMENT_CONFIRMED,
    STAGE_PAYMENT_PENDING,
    STAGE_REWARD_ESTIMATE,
    detail_for_stage,
    lifecycle_chain,
    payout_ui_block,
    stage_title,
)


def test_stage_titles_ru_honest():
    assert stage_title("task_accepted") == "Задача взята в работу"
    assert stage_title("task_completed") == "Задача обработана"
    assert stage_title("reward_estimate") == "Оценка вознаграждения"
    assert stage_title("payment_pending") == "Ожидает подтверждения платформой"
    assert stage_title("payment_confirmed") == "Платформа подтвердила оплату"
    assert stage_title("balance_increased") == "Баланс биржи обновился"
    assert stage_title("cycle_accounted") == "Расчётный учёт цикла"


def test_lifecycle_chain_live_stops_at_pending_without_real_payout():
    stages = lifecycle_chain(ok=True, sandbox=False, live_exchange=True, pay_eur=0.05)
    assert stages == [
        "task_accepted",
        "task_completed",
        "reward_estimate",
        "payment_pending",
    ]
    assert STAGE_PAYMENT_CONFIRMED not in stages
    assert STAGE_BALANCE_INCREASED not in stages


def test_lifecycle_chain_sandbox_estimate_only():
    stages = lifecycle_chain(ok=True, sandbox=True, live_exchange=False, pay_eur=0.02)
    assert stages == [
        "task_accepted",
        "task_completed",
        "reward_estimate",
    ]
    assert STAGE_PAYMENT_PENDING not in stages
    assert STAGE_PAYMENT_CONFIRMED not in stages


def test_lifecycle_chain_real_payout_appends_confirmed():
    stages = lifecycle_chain(
        ok=True,
        sandbox=False,
        live_exchange=True,
        pay_eur=0.05,
        real_payout=True,
    )
    assert STAGE_PAYMENT_CONFIRMED in stages
    assert stages[-1] == STAGE_PAYMENT_CONFIRMED


def test_detail_payment_confirmed_requires_real_payout():
    fake = detail_for_stage(
        STAGE_PAYMENT_CONFIRMED,
        task_label="demo-1",
        pay_eur=0.01,
        real_payout=False,
    )
    assert "отказ" in fake
    assert "не пишем" in fake

    real = detail_for_stage(
        STAGE_PAYMENT_CONFIRMED,
        task_label="demo-1",
        pay_eur=0.05,
        payout_id="84392711",
        real_payout=True,
    )
    assert "84392711" in real
    assert "0.0500" in real
    assert "доступно к выводу" in real


def test_detail_reward_estimate_not_withdrawable():
    text = detail_for_stage(
        STAGE_REWARD_ESTIMATE,
        task_label="demo-2",
        pay_eur=0.02,
        sandbox=False,
    )
    assert "оценка" in text
    assert "Stripe" in text
    assert "не" in text.lower()


def test_payout_ui_block_ru():
    block = payout_ui_block(threshold_usd=10.0)
    assert "реальн" in block["title"].lower() or "вывод" in block["title"].lower()
    assert len(block["steps"]) >= 3
    assert block["auto_payout"] is False
    assert "Stripe" in block["note"]
