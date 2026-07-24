"""Tests: real exchange payout journal vs local estimates."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from app.integration.business_mode_service import BusinessModeService
from app.integration.micro_farm_service import MicroFarmService


def _farm(tmp_path: Path) -> MicroFarmService:
    opp = MagicMock()
    fin = MagicMock()
    bm = BusinessModeService(tmp_path)
    return MicroFarmService(opp, fin, business_mode=bm, memory_dir=tmp_path)


def test_log_real_exchange_payout_requires_id(tmp_path: Path):
    farm = _farm(tmp_path)
    rejected = farm.log_real_exchange_payout(
        amount_eur=0.05,
        payout_id="",
        platform="toloka",
    )
    assert rejected["ok"] is False

    ok = farm.log_real_exchange_payout(
        amount_eur=0.05,
        payout_id="84392711",
        platform="toloka",
        balance_after_eur=1.25,
    )
    assert ok["ok"] is True
    assert ok["withdrawable"] is True
    events = farm._recent_events(10)
    stages = [e.get("lifecycle_stage") for e in events]
    assert "payment_confirmed" in stages
    assert "balance_increased" in stages
    confirmed = next(e for e in events if e.get("lifecycle_stage") == "payment_confirmed")
    assert confirmed.get("real_payout") is True
    assert confirmed.get("withdrawable") is True
    assert confirmed.get("payout_id") == "84392711"
    assert confirmed.get("pay_eur") == 0.05


def test_emit_task_lifecycle_never_confirms_without_proof(tmp_path: Path):
    farm = _farm(tmp_path)
    farm._emit_task_lifecycle(
        adapter="demo",
        task_id="t-1",
        pay_eur=0.02,
        ok=True,
        real_payout=False,
    )
    events = farm._recent_events(20)
    stages = [e.get("lifecycle_stage") for e in events]
    assert "reward_estimate" in stages or "task_completed" in stages
    assert "payment_confirmed" not in stages
    for e in events:
        assert e.get("withdrawable") is not True
        assert float(e.get("pay_eur") or 0) == 0.0
