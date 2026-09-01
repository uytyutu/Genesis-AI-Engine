"""
Experiment P-01 — Verifiable Compute → Reward

One concrete public protocol, full path:
  docs + contract → analyzers → Virtus compute fit → proof → economic brick

PASS ≠ insight_fit. PASS = CANDIDATE_REAL_BRICK with all critical fields.
REAL_EXTERNAL_ASSET only after TXID.

Axiom: VCORE is NOT the liquidity source for this experiment.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from virtus_core.opportunity_ai.economic_brick import BRICK_FIELDS, classify_brick, extract_brick
from virtus_core.protocol_state_discovery.engine import (
    AXIOM,
    RESEARCH_QUESTION,
    public_contract_analyzer,
    reward_flow_analyzer,
    state_transition_analyzer,
)

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "experiments"
_LAST = _RUNTIME / "p01_last.json"

# Primary P-01 target: real public verifiable-compute protocol with on-chain settlement.
# Not VCORE. Not hypothesis class — named contracts + docs.
P01_LIVEPEER: dict[str, Any] = {
    "experiment_id": "P-01",
    "slug": "livepeer_arbitrum",
    "protocol": "Livepeer",
    "network": "Arbitrum One",
    "docs": "https://docs.livepeer.org/network/reference/contracts",
    "orchestrator_guide": "https://docs.livepeer.org/network/guides/orchestrator-activate",
    "contracts": {
        "Controller": "0xD8E8328501E9645d16Cf49539efC04f734606ee4",
        "BondingManager": "0x35Bcf3c30594191d53231E4FF333E8A770453e40",
        "TicketBroker": "0xa8bB618B1520E284046F3dFc448851A1Ff26e41B",
    },
    "public_functions": {
        "BondingManager": [
            "bond(uint256 _amount)",
            "becomeOrchestrator(...)",
            "reward()",
            "transcoderWithHint(...)",
        ],
        "TicketBroker": [
            "redeemWinningTicket(...)",
        ],
    },
    "state_machine": {
        "state_a": "INACTIVE_ORCHESTRATOR",
        "public_condition": (
            "Bond LPT stake + on-chain activation + enter top-100 active set + "
            "perform verifiable transcoding work + accumulate winning payment tickets"
        ),
        "state_b": "WINNING_TICKETS_REDEEMABLE",
        "automatic_reward": False,
        "reward_functions": ["TicketBroker.redeemWinningTicket → ETH", "BondingManager.reward → LPT inflation"],
    },
    "work": {
        "type": "video_transcode_inference",
        "virtus_can_execute": True,
        "virtus_compute_fit": "CPU/GPU transcoding — matches Livepeer orchestrator workload",
        "note": "Virtus can run compute; protocol still gates payout via stake + active set",
    },
    "proof": {
        "type": "winning_payment_ticket_on_chain",
        "independently_verifiable": True,
        "verifier": "TicketBroker + on-chain ticket merkle/root checks",
        "reference": "https://docs.livepeer.org/network/developers/core-concepts/payments",
    },
    "economic": {
        "ACTION": "transcode_assigned_streams_then_redeemWinningTicket_and_reward",
        "SOURCE": "gateway_micropayments_plus_LPT_inflation",
        "ASSET": "ETH",
        "secondary_asset": "LPT",
        "AMOUNT": None,
        "amount_rule": "Variable: ETH per winning ticket batch + LPT per round via reward(); not fixed constant",
        "DESTINATION": "orchestrator_EOA_on_Arbitrum",
        "PAYOUT_RULE": (
            "Gateways pay orchestrators via probabilistic payment tickets; "
            "orchestrator redeems winning tickets for ETH; LPT inflation minted when reward() called each round"
        ),
        "ON_CHAIN_PROOF": "https://arbiscan.io/address/0xa8bB618B1520E284046F3dFc448851A1Ff26e41B",
        "TRANSFERABILITY": "ETH and LPT transferable ERC-20/native on Arbitrum",
        "CAPITAL": "STAKE_REQUIRED",
        "capital_detail": (
            "No fixed minimum LPT; effective minimum = stake of 100th active orchestrator "
            "(check explorer.livepeer.org). Bond + approve txs require LPT + ETH gas."
        ),
        "GAS": ">0 ETH on Arbitrum for bond/activate/redeem/reward txs",
        "REGISTRATION": True,
        "registration_detail": "On-chain orchestrator registration via livepeer_cli multi-step flow",
        "KYC": False,
        "APPLICATION": False,
        "DEPOSIT": False,
        "PURCHASE": False,
        "STAKE": True,
    },
    "zero_capital_eur": False,
    "zero_capital_blocker": "STAKE + GAS + active-set competition (top 100 by LPT stake)",
    "vcore_axiom_note": "VCORE not involved; reward assets are ETH/LPT from Livepeer protocol",
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _opp_from_p01(spec: dict[str, Any]) -> dict[str, Any]:
    econ = spec["economic"]
    return {
        "opportunityId": f"p01_{spec['slug']}",
        "protocol": spec["protocol"],
        "kind": "PERMISSIONLESS_COMPUTE",
        "sourceType": "COMPUTE_REWARD",
        "action": econ["ACTION"],
        "source": econ["SOURCE"],
        "asset": econ["ASSET"],
        "counterAsset": econ["ASSET"],
        "withdrawalPath": econ["DESTINATION"],
        "eligibility": econ["PAYOUT_RULE"],
        "reward_rule": econ["PAYOUT_RULE"],
        "evidence": econ["ON_CHAIN_PROOF"],
        "transferability": econ["TRANSFERABILITY"],
        "expectedAmount": econ.get("AMOUNT"),
        "amount_rule": econ.get("amount_rule"),
        "capital_required": 1.0 if econ.get("CAPITAL") == "STAKE_REQUIRED" else 0,
        "gas_required": 0.01,
        "registration_required": bool(econ.get("REGISTRATION")),
        "stake_required": bool(econ.get("STAKE")),
        "deposit_required": bool(econ.get("DEPOSIT")),
        "purchase_required": bool(econ.get("PURCHASE")),
        "application_required": bool(econ.get("APPLICATION")),
        "kyc_required": bool(econ.get("KYC")),
        "automatic_payout": False,
        "docs": spec["docs"],
        "contracts": spec["contracts"],
    }


def run_experiment_p01(*, protocol_slug: str = "livepeer_arbitrum") -> dict[str, Any]:
    """Run P-01 on one concrete protocol. Default: Livepeer on Arbitrum."""
    if protocol_slug != "livepeer_arbitrum":
        return {"ok": False, "error": f"unknown_protocol={protocol_slug}", "experiment_id": "P-01"}

    spec = P01_LIVEPEER
    opp = _opp_from_p01(spec)
    brick_result = classify_brick(opp)
    st = state_transition_analyzer(opp)
    rf = reward_flow_analyzer(opp)
    pca = public_contract_analyzer()

    # Override state machine with concrete Livepeer path
    st_concrete = {
        **st,
        "concrete": spec["state_machine"],
        "insight_questions": {
            "Can Virtus produce the required proof?": spec["proof"]["independently_verifiable"],
            "Can it do so with €0?": spec["zero_capital_eur"],
            "Is reward deterministic?": False,
            "Where does reward come from?": spec["economic"]["SOURCE"],
            "Can transaction be verified?": True,
        },
        "experiment_ready": False,
        "experiment_ready_blocker": spec["zero_capital_blocker"],
    }

    virtus = spec["work"]
    proof = spec["proof"]

    # Owner PASS schema (partial fill — honest)
    pass_payload = {
        "protocol": spec["protocol"],
        "contract": spec["contracts"]["BondingManager"],
        "condition": spec["state_machine"]["public_condition"],
        "work": spec["work"]["type"],
        "proof": spec["proof"]["type"],
        "asset": spec["economic"]["ASSET"],
        "amount": spec["economic"].get("AMOUNT"),
        "amount_rule": spec["economic"].get("amount_rule"),
        "destination": spec["economic"]["DESTINATION"],
        "on_chain_proof": spec["economic"]["ON_CHAIN_PROOF"],
        "state": brick_result["status"],
    }

    missing = list(brick_result["missing"])
    friction = list(brick_result["friction_violations"])
    if not spec["zero_capital_eur"]:
        if "STAKE" not in friction and spec["economic"].get("STAKE"):
            friction.append("STAKE")
        if "CAPITAL" not in friction:
            friction.append("CAPITAL")

    # Theory verdict
    theory_works = {
        "framework_identifies_real_protocol": True,
        "concrete_contract_not_hypothesis": True,
        "state_machine_mapped": True,
        "virtus_compute_can_do_work": virtus["virtus_can_execute"],
        "zero_capital_path_at_eur_0": spec["zero_capital_eur"],
        "candidate_real_brick_at_eur_0": brick_result["status"] == "CANDIDATE_REAL_BRICK",
        "real_external_asset": False,
        "vcore_used_as_liquidity": False,
        "honest_incomplete_is_valid_science": brick_result["status"] == "INCOMPLETE_ECONOMIC_BRICK",
    }

    if brick_result["status"] == "CANDIDATE_REAL_BRICK":
        experiment_outcome = "P01_PASS_CANDIDATE_REAL"
        verdict = (
            "P-01 PASS (schema): все критические поля заполнены при €0. "
            "Дальше: simulation → owner → real TX → REAL_EXTERNAL_ASSET."
        )
    elif brick_result["status"] == "INCOMPLETE_ECONOMIC_BRICK":
        experiment_outcome = "P01_INCOMPLETE"
        verdict = (
            f"P-01 INCOMPLETE — теория работает как фильтр истины. "
            f"Протокол реальный, compute→proof→reward существует, но €0 путь заблокирован: "
            f"{spec['zero_capital_blocker']}. Missing: {missing}. Friction: {friction}."
        )
    else:
        experiment_outcome = "P01_OTHER"
        verdict = brick_result["status"]

    report = {
        "experiment_id": "P-01",
        "title": "Verifiable Compute → Reward",
        "version": "1.0.0",
        "at": _now(),
        "axiom": AXIOM,
        "research_question": RESEARCH_QUESTION,
        "protocol_slug": protocol_slug,
        "spec": spec,
        "pipeline": [
            "PUBLIC PROTOCOL",
            "docs + contract address",
            "PUBLIC CONTRACT ANALYZER",
            "STATE TRANSITION",
            "REWARD FLOW",
            "VIRTUS COMPUTE",
            "PROOF",
            "ECONOMIC BRICK",
            "simulation → owner → TX → TXID",
        ],
        "analyzers": {
            "public_contract_analyzer": {
                "matched_class": "compute_marketplace",
                "priority_class": pca["priority_class"],
                "concrete_contracts": spec["contracts"],
                "public_functions": spec["public_functions"],
            },
            "state_transition_analyzer": st_concrete,
            "reward_flow_analyzer": rf,
        },
        "virtus_compute": virtus,
        "proof": proof,
        "economic_brick": {
            "fields_schema": list(BRICK_FIELDS),
            "extracted": extract_brick(opp),
            "classification": brick_result,
            "missing": missing,
            "friction_violations": friction,
        },
        "pass_schema": pass_payload,
        "experiment_outcome": experiment_outcome,
        "verdict": verdict,
        "theory_check": theory_works,
        "real_external_asset": {
            "count": 0,
            "txid": None,
            "note": "REAL only after confirmed TX — not claimed in P-01 research run",
        },
        "next_if_incomplete": (
            "Either accept STAKE≠€0 and re-run P-01 without zero-capital axiom (separate experiment), "
            "or find another public protocol where compute+proof pays at €0 with fixed amount + auto payout. "
            "Do not use VCORE as liquidity source."
        ),
        "next_if_candidate": "simulate → owner approval → broadcast → verify TXID + balance delta",
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    out_path = _RUNTIME / f"p01_{protocol_slug}.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
