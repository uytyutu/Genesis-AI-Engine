"""Tests — Opportunity AI systematic discovery + honest NO_VALID_OPPORTUNITY."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.opportunity_ai.systematic import PRIORITY, _funnel_questions, _priority_rank, systematic_discover
from virtus_core.value_hunter.evolution import run_epoch_tick


def test_priority_compute_first():
    assert _priority_rank({"kind": "PERMISSIONLESS_COMPUTE"}) < _priority_rank({"kind": "GRANT"})
    assert _priority_rank({"kind": "COMPUTE_REWARD"}) == 0
    assert PRIORITY[0] == "COMPUTE_REWARD"


def test_funnel_rejects_application():
    f = _funnel_questions(
        {
            "capital_required": 0,
            "application_required": True,
            "eligibility": "Proposal + acceptance",
            "action": "apply",
            "source": "GRANT",
            "asset": "USDC",
            "withdrawalPath": "bank",
        }
    )
    assert f["strict_zero_friction_pass"] is False
    assert "no_application" in f["failed_gates"]


def test_systematic_offline_honest_negative():
    r = systematic_discover(offline=True)
    assert r["epoch_status"] in ("NO_VALID_OPPORTUNITY", "CANDIDATE_FOUND")
    assert r["counts"]["real_external_assets"] == 0
    assert r["agent_policy"]["may_end_epoch_with"] == "NO_VALID_OPPORTUNITY"
    assert (r.get("compute_capability") or {}).get("income_claimed") is False


def test_evolution_allows_no_valid_opportunity():
    tick = run_epoch_tick()
    assert "systematic" in tick
    assert tick["success_definition"]["honest_negative"] == "NO_VALID_OPPORTUNITY"
    assert "VECTORS_PER_SEC" in tick["success_definition"]["not_success"]
    # Most runs will be NO_VALID — either agent status or systematic epoch
    assert tick["systematic"]["epoch_status"] in ("NO_VALID_OPPORTUNITY", "CANDIDATE_FOUND")
