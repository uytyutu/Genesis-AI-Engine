"""Tests — Experiment P-03 Golem field observation framework."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.protocol_state_discovery.experiment_p03 import (
    RESEARCH_DIMENSIONS,
    TAXONOMY_STATES,
    run_experiment_p03,
)
from virtus_core.protocol_state_discovery.golem_observer import (
    check_prerequisites,
    run_phase_b_settlement,
)


def test_p03_prerequisites_missing_on_typical_windows():
    r = run_experiment_p03(include_p02_context=False)
    assert r["experiment_id"] == "P-03"
    assert r["axiom"] == "€0 CAPITAL ≠ €0 COST — capital-free ≠ cost-free"
    dims = r["research_dimensions"]
    assert dims["CAPITAL_FREE"] == "PASS"
    assert dims["DETERMINISTIC_AMOUNT"] == "FAIL"
    assert dims["GUARANTEED_DEMAND"] == "FAIL"
    assert dims["REAL_TRANSACTION"] == "NOT_YET_OBSERVED"
    assert r["economic_brick"]["state"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert r["taxonomy"]["current_id"] == 3
    assert r["real_external_asset"]["count"] == 0


def test_phase_b_never_claims_real_without_txid():
    phase_a = {
        "settlement_hints": {"job_id": "act-1", "earned_glm": "0.5", "polygon_txid": None},
    }
    b = run_phase_b_settlement(phase_a=phase_a)
    assert b["economic_brick_state"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert b["real_external_asset"] == "NOT_CLAIMED"


def test_taxonomy_has_four_states():
    assert len(TAXONOMY_STATES) == 4
    assert "CAPITAL_FREE" in RESEARCH_DIMENSIONS


def test_prerequisites_structure():
    p = check_prerequisites()
    assert "ready_to_observe" in p
    assert "platform_note" in p
