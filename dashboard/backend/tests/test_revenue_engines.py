from pathlib import Path

from app.integration.finance_service import FinanceService
from app.integration.revenue_engines_service import (
    ENGINE_B2B,
    ENGINE_LAB,
    build_revenue_engines,
)


def test_lab_never_counts_as_b2b_profit(tmp_path: Path):
    fin = FinanceService(tmp_path)
    result = build_revenue_engines(
        memory_dir=tmp_path,
        finance_snapshot=fin._load_snapshot(),
        settlements=[],
        farm_state={"total_earned_eur": 121.0},
    )
    lab = next(e for e in result["engines"] if e["id"] == ENGINE_LAB)
    b2b = next(e for e in result["engines"] if e["id"] == ENGINE_B2B)
    assert lab["counts_as_profit"] is False
    assert lab["lab_journal_eur"] == 121.0
    assert b2b["confirmed_eur"] == 0.0


def test_b2b_confirmed_from_settlements(tmp_path: Path):
    fin = FinanceService(tmp_path)
    fin.credit_order_payment(50.0, "B2B deal", provider="stripe", external_id="cs_1")
    snap = fin._load_snapshot()
    inputs = fin.real_money_inputs()
    result = build_revenue_engines(
        memory_dir=tmp_path,
        finance_snapshot=snap,
        settlements=inputs["settlements"],
        farm_state={},
    )
    b2b = next(e for e in result["engines"] if e["id"] == ENGINE_B2B)
    assert b2b["confirmed_eur"] == 50.0
    toloka = next(x for x in result["experiments"] if x["channel"] == "toloka_requester")
    assert toloka["status"] == "failed"
