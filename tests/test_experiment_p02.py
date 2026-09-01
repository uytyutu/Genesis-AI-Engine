"""Tests — Experiment P-02 capital-free compute filter."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.protocol_state_discovery.experiment_p02 import (
    P02_FILTER_GATES,
    analyze_p02_candidate,
    run_experiment_p02,
)


def test_nexus_non_transferable_fails_p02():
    from virtus_core.protocol_state_discovery.experiment_p02 import P02_CANDIDATES

    nexus = next(c for c in P02_CANDIDATES if c["slug"] == "nexus_prover_points")
    a = analyze_p02_candidate(nexus)
    assert a["p02_filter_pass"] is False
    assert a["incomplete_reason"] == "NON_TRANSFERABLE_REWARD"
    assert "NO_POINTS_ASSET" in a["failed_p02_gates"]


def test_golem_passes_p02_filter_but_incomplete_amount():
    from virtus_core.protocol_state_discovery.experiment_p02 import P02_CANDIDATES

    golem = next(c for c in P02_CANDIDATES if c["slug"] == "golem_provider_mainnet")
    a = analyze_p02_candidate(golem)
    assert a["p02_filter_pass"] is True
    assert a["brick_status"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert "AMOUNT" in a["missing_brick_fields"]


def test_p02_run_includes_p01_control():
    r = run_experiment_p02(include_p01_control=True)
    assert r["experiment_id"] == "P-02"
    assert len(P02_FILTER_GATES) == 12
    assert r["p01_control"]["role"] == "CONTROL"
    assert r["counts"]["real_external_asset"] == 0
    assert r["experiment_outcome"] in (
        "P02_PASS_CANDIDATE_REAL",
        "P02_FILTER_PASS_BRICK_INCOMPLETE",
        "P02_NO_CAPITAL_FREE_CANDIDATE",
    )
