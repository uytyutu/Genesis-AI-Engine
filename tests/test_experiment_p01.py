"""Tests — Experiment P-01 Livepeer concrete protocol run."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.protocol_state_discovery.experiment_p01 import run_experiment_p01


def test_p01_livepeer_incomplete_at_zero_capital():
    r = run_experiment_p01(protocol_slug="livepeer_arbitrum")
    assert r["experiment_id"] == "P-01"
    assert r["experiment_outcome"] == "P01_INCOMPLETE"
    ps = r["pass_schema"]
    assert ps["protocol"] == "Livepeer"
    assert ps["contract"].startswith("0x")
    assert ps["state"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert r["real_external_asset"]["count"] == 0
    assert r["real_external_asset"]["txid"] is None
    tc = r["theory_check"]
    assert tc["framework_identifies_real_protocol"] is True
    assert tc["concrete_contract_not_hypothesis"] is True
    assert tc["virtus_compute_can_do_work"] is True
    assert tc["zero_capital_path_at_eur_0"] is False
    assert tc["candidate_real_brick_at_eur_0"] is False
    assert tc["vcore_used_as_liquidity"] is False
    assert "AMOUNT" in r["economic_brick"]["missing"] or "STAKE" in str(r["economic_brick"]["friction_violations"])
