"""Tests — economic brick + Protocol State Discovery autopsy."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from virtus_core.opportunity_ai.economic_brick import classify_brick
from virtus_core.protocol_state_discovery.engine import (
    RESEARCH_QUESTION,
    autopsy_candidate,
    public_contract_analyzer,
    run_protocol_state_discovery,
)


def test_incomplete_without_amount():
    r = classify_brick(
        {
            "action": "execute_public_work",
            "source": "COMPUTE_REWARD",
            "asset": "TON",
            "withdrawalPath": "owner_wallet",
            "eligibility": "public verify",
            "evidence": "https://example.com/docs",
            "expectedAmount": None,
            "capital_required": 0,
        }
    )
    assert r["status"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert "AMOUNT" in r["missing"]


def test_candidate_real_when_complete():
    r = classify_brick(
        {
            "action": "submit_work",
            "source": "COMPUTE_MARKET",
            "asset": "USDT",
            "withdrawalPath": "0xOWN",
            "eligibility": "verifier accepts proof → transfer",
            "evidence": "https://example.com/contract#pay",
            "expectedAmount": 1.5,
            "capital_required": 0,
            "transferability": "ERC20_TRANSFER",
        }
    )
    assert r["status"] == "CANDIDATE_REAL_BRICK"


def test_real_only_with_txid():
    r = classify_brick(
        {
            "action": "submit_work",
            "source": "COMPUTE_MARKET",
            "asset": "USDT",
            "withdrawalPath": "0xOWN",
            "eligibility": "pay",
            "evidence": "https://example.com/c",
            "expectedAmount": 1,
            "transferability": "yes",
        },
        confirmed_tx={"txid": "0xabc", "confirmed": True},
    )
    assert r["status"] == "REAL_EXTERNAL_ASSET"


def test_vcore_trap_in_autopsy():
    a = autopsy_candidate(
        {
            "opportunityId": "t_vcore",
            "kind": "AGGREGATOR",
            "asset": "VCORE",
            "action": "swap",
            "capital_required": 0,
            "evidence": "hypothesis",
        }
    )
    assert a["brick_status"] == "INCOMPLETE_ECONOMIC_BRICK"
    assert any("VCORE" in w for w in a["why_not_real_yet"])


def test_contract_analyzer_priority_compute():
    pca = public_contract_analyzer()
    assert pca["priority_class"] == "compute_marketplace"
    assert "exploit" in " ".join(pca["forbidden"]).lower() or any("exploit" in x for x in pca["forbidden"])


def test_psd_offline_autopsy():
    r = run_protocol_state_discovery(offline=True)
    assert RESEARCH_QUESTION[:20] in r["research_question"]
    assert r["counts"]["real_external_asset"] == 0
    assert r["epoch_status"] in ("NO_VALID_OPPORTUNITY", "CANDIDATE_REAL_BRICK_FOUND")
    assert "VCORE → exchanger" in " ".join(r["not_insight"])
