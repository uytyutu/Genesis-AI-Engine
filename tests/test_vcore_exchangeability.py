"""Tests — VCORE-X01 External Exchangeability."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.vcore_exchangeability.engine import (
    X01_STAGES,
    run_x01_external_exchangeability,
)


def test_x01_has_ten_stages():
    assert len(X01_STAGES) == 10
    assert X01_STAGES[0][1] == "CONTRACT"
    assert X01_STAGES[-1][1] == "TXID"


def test_real_external_not_pass_without_txid():
    r = run_x01_external_exchangeability(offline=True)
    assert r["experiment_id"] == "VCORE-X01"
    assert r["summary"]["REAL_EXTERNAL_ASSET"] == "NOT_YET"
    assert r["genesis_touch"] is False
    assert r["stages"]["X01.10_TXID"]["status"] in ("NOT_YET", "FAIL")


def test_technically_ready_market_not_created():
    r = run_x01_external_exchangeability(offline=True)
    assert r["summary"]["experiment_outcome"] in (
        "X01_GENESIS_FIRST",
        "X01_TOKEN_READY_MARKET_NOT_CREATED",
        "X01_READY_FOR_SMALL_TEST_SWAP",
        "X01_COMPLETE_REAL_EXTERNAL_ASSET",
    )
