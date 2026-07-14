from swarm.farm_lifecycle_ru import (
    STAGE_BALANCE_INCREASED,
    STAGE_PAYMENT_CONFIRMED,
    detail_for_stage,
    lifecycle_chain,
    payout_ui_block,
    stage_title,
)


def test_stage_titles_ru():
    assert stage_title("task_accepted") == "Задача принята"
    assert stage_title("task_completed") == "Задача выполнена"
    assert stage_title("payment_confirmed") == "Платформа подтвердила оплату"
    assert stage_title("balance_increased") == "Баланс увеличился"


def test_lifecycle_chain_live_has_pending_not_balance_per_task():
    stages = lifecycle_chain(ok=True, sandbox=False, live_exchange=True, pay_eur=0.05)
    assert stages == [
        "task_accepted",
        "task_completed",
        "payment_pending",
        "payment_confirmed",
    ]
    assert STAGE_BALANCE_INCREASED not in stages


def test_detail_payment_confirmed_sandbox():
    text = detail_for_stage(
        STAGE_PAYMENT_CONFIRMED,
        task_label="demo-1",
        pay_eur=0.01,
        sandbox=True,
    )
    assert "учебное начисление" in text
    assert "0.0100" in text


def test_payout_ui_block_ru():
    block = payout_ui_block(threshold_usd=10.0)
    assert block["title"] == "Как выводить деньги"
    assert len(block["steps"]) >= 3
    assert block["auto_payout"] is False
