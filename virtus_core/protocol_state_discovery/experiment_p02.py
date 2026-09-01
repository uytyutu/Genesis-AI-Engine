"""
Experiment P-02 — Capital-free verifiable work → transferable external asset

Preserves P-01 CONTROL (Livepeer) as reference.

Hypothesis under test (unchanged):
  Can Virtus get transferable external asset via verifiable work at €0 upfront capital?

P-02 filter — seek protocols where economic INPUT is work/compute, not capital:

  NO TOKEN PURCHASE · NO STAKE · NO COLLATERAL · NO REQUIRED CAPITAL
  NO INVITE/REFERRAL · NO TESTNET · NO POINTS · NO VCORE LIQUIDITY
        ↓
  PUBLIC WORK → VERIFIABLE PROOF → PUBLIC PAYMENT → TRANSFERABLE ASSET

NON_TRANSFERABLE_REWARD (e.g. Nexus points) → INCOMPLETE, not a win.

PASS = CANDIDATE_REAL_BRICK only. REAL_EXTERNAL_ASSET only after TXID.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from virtus_core.opportunity_ai.economic_brick import BRICK_FIELDS, classify_brick, extract_brick
from virtus_core.protocol_state_discovery.experiment_p01 import P01_LIVEPEER, run_experiment_p01

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "experiments"
_LAST = _RUNTIME / "p02_last.json"

P02_FILTER_GATES: tuple[str, ...] = (
    "NO_TOKEN_PURCHASE",
    "NO_STAKE",
    "NO_COLLATERAL",
    "NO_REQUIRED_CAPITAL",
    "NO_INVITE_REFERRAL",
    "NO_TESTNET",
    "NO_POINTS_ASSET",
    "NO_VCORE_LIQUIDITY",
    "PUBLIC_WORK",
    "VERIFIABLE_PROOF",
    "PUBLIC_PAYMENT_CONDITION",
    "TRANSFERABLE_EXTERNAL_ASSET",
)

# P-01 retained as control specimen — not re-run as P-02 candidate.
P01_CONTROL_SUMMARY: dict[str, Any] = {
    "experiment_id": "P-01",
    "role": "CONTROL",
    "protocol": "Livepeer",
    "real_protocol": True,
    "real_compute": True,
    "real_proof": True,
    "real_reward": True,
    "external_asset": True,
    "eur_zero": False,
    "capital_free": False,
    "lesson": "Compute→proof→reward exists; €0 blocked by stake+registration before compute",
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _gate_results(spec: dict[str, Any]) -> dict[str, bool]:
    f = spec.get("p02_filters") or {}
    return {k: bool(f.get(k)) for k in P02_FILTER_GATES}


def _failed_gates(spec: dict[str, Any]) -> list[str]:
    return [k for k, v in _gate_results(spec).items() if not v]


def _opp_from_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    econ = spec["economic"]
    return {
        "opportunityId": f"p02_{spec['slug']}",
        "protocol": spec["protocol"],
        "kind": spec.get("kind", "PERMISSIONLESS_COMPUTE"),
        "action": econ.get("ACTION"),
        "source": econ.get("SOURCE"),
        "asset": econ.get("ASSET"),
        "withdrawalPath": econ.get("DESTINATION"),
        "eligibility": econ.get("PAYOUT_RULE"),
        "reward_rule": econ.get("PAYOUT_RULE"),
        "evidence": econ.get("ON_CHAIN_PROOF"),
        "transferability": econ.get("TRANSFERABILITY"),
        "expectedAmount": econ.get("AMOUNT"),
        "amount_rule": econ.get("amount_rule"),
        "capital_required": 0 if spec["p02_filters"].get("NO_REQUIRED_CAPITAL") else 1.0,
        "gas_required": float(econ.get("GAS_EUR") or 0),
        "registration_required": not spec["p02_filters"].get("NO_INVITE_REFERRAL", True)
        and bool(econ.get("PLATFORM_ACCOUNT")),
        "stake_required": not spec["p02_filters"].get("NO_STAKE", True),
        "deposit_required": not spec["p02_filters"].get("NO_COLLATERAL", True),
        "purchase_required": not spec["p02_filters"].get("NO_TOKEN_PURCHASE", True),
        "application_required": False,
        "kyc_required": False,
        "automatic_payout": bool(spec.get("automatic_payout")),
        "non_transferable_reward": bool(spec.get("non_transferable_reward")),
    }


# --- P-02 candidate registry (concrete protocols, honest flags) ---

P02_CANDIDATES: list[dict[str, Any]] = [
    {
        "slug": "golem_provider_mainnet",
        "protocol": "Golem Network (Yagna provider)",
        "network": "Polygon / Ethereum mainnet",
        "docs": "https://docs.golem.network/docs/providers/provider-installation",
        "overview": "https://docs.golem.network/docs/golem/overview",
        "contracts": {
            "GLM_ERC20_ETHEREUM": "0x7DD9c5Cba05E151C895FDe1CF355C9A1D5DA6429",
            "GLM_ERC20_POLYGON": "0x0B220b82F3eA3B7F6d9A1D8ab58930C064A2b5Bf",
            "note": "Yagna settlement via payment drivers on Polygon/Ethereum; not single escrow contract",
        },
        "kind": "PERMISSIONLESS_COMPUTE",
        "automatic_payout": False,
        "non_transferable_reward": False,
        "p02_filters": {
            "NO_TOKEN_PURCHASE": True,
            "NO_STAKE": True,
            "NO_COLLATERAL": True,
            "NO_REQUIRED_CAPITAL": True,
            "NO_INVITE_REFERRAL": True,
            "NO_TESTNET": True,
            "NO_POINTS_ASSET": True,
            "NO_VCORE_LIQUIDITY": True,
            "PUBLIC_WORK": True,
            "VERIFIABLE_PROOF": True,
            "PUBLIC_PAYMENT_CONDITION": True,
            "TRANSFERABLE_EXTERNAL_ASSET": True,
        },
        "state_machine": {
            "state_a": "PROVIDER_IDLE",
            "public_condition": "Publish offer → market match → agreement → execute task → invoice → requestor pays GLM on Polygon",
            "state_b": "GLM_RECEIVED_IN_YAGNA_WALLET",
            "reward_functions": ["Requestor-initiated GLM transfer via Yagna payment driver"],
        },
        "work": {
            "type": "wasi_vm_or_docker_compute_tasks",
            "virtus_can_execute": True,
            "note": "Provider sells CPU/GPU time; requestor pays per agreement — no provider stake",
        },
        "proof": {
            "type": "task_execution_logs_plus_yagna_billing",
            "independently_verifiable": True,
            "reference": "https://docs.golem.network/docs/golem/overview",
        },
        "economic": {
            "ACTION": "run_provider_agent_accept_market_jobs",
            "SOURCE": "requestor_glm_payment_on_polygon",
            "ASSET": "GLM",
            "AMOUNT": None,
            "amount_rule": "Market-priced per agreement (cpu/duration/initial coeffs); not fixed constant before job",
            "DESTINATION": "YA_ACCOUNT Ethereum/Polygon wallet",
            "PAYOUT_RULE": "After task completion requestor pays provider in GLM via Yagna; 0% protocol commission",
            "ON_CHAIN_PROOF": "https://polygonscan.com/token/0x0B220b82F3eA3B7F6d9A1D8ab58930C064A2b5Bf",
            "TRANSFERABILITY": "GLM ERC-20 transferable on Polygon/Ethereum",
            "GAS_EUR": 0,
            "gas_note": "Requestor pays compute; provider may need minimal POL only when moving GLM out of Yagna — not upfront stake",
            "PLATFORM_ACCOUNT": False,
        },
        "p02_risks": [
            "AMOUNT not deterministic before job — market variable",
            "Job demand not guaranteed — may earn 0 GLM",
            "Payment path is Yagna driver stack, not one simple public claim()",
        ],
    },
    {
        "slug": "nexus_prover_points",
        "protocol": "Nexus zkVM Prover (Node Runners)",
        "network": "Nexus testnet / off-chain points",
        "docs": "https://blog.nexus.xyz/nexus-changelog-10-03-25/",
        "contracts": {"note": "Prover rewards primarily points/NFT shop — not direct mainnet asset payout to wallet"},
        "kind": "PERMISSIONLESS_COMPUTE",
        "automatic_payout": False,
        "non_transferable_reward": True,
        "incomplete_reason": "NON_TRANSFERABLE_REWARD",
        "p02_filters": {
            "NO_TOKEN_PURCHASE": True,
            "NO_STAKE": True,
            "NO_COLLATERAL": True,
            "NO_REQUIRED_CAPITAL": True,
            "NO_INVITE_REFERRAL": False,
            "NO_TESTNET": False,
            "NO_POINTS_ASSET": False,
            "NO_VCORE_LIQUIDITY": True,
            "PUBLIC_WORK": True,
            "VERIFIABLE_PROOF": True,
            "PUBLIC_PAYMENT_CONDITION": False,
            "TRANSFERABLE_EXTERNAL_ASSET": False,
        },
        "state_machine": {
            "state_a": "UNPROVEN",
            "public_condition": "Run prover CLI/OS → valid proofs → reputation → points",
            "state_b": "POINTS_OR_NFT",
        },
        "work": {"type": "zk_proof_generation", "virtus_can_execute": True},
        "proof": {"type": "zk_proof", "independently_verifiable": True},
        "economic": {
            "ACTION": "run_nexus_prover_cli",
            "SOURCE": "off_chain_points_ledger",
            "ASSET": "NEX_POINTS",
            "AMOUNT": None,
            "DESTINATION": "platform_account",
            "PAYOUT_RULE": "Points / Glyph NFT shop — not automatic transferable mainnet asset",
            "ON_CHAIN_PROOF": None,
            "TRANSFERABILITY": "NON_TRANSFERABLE until speculative airdrop",
            "PLATFORM_ACCOUNT": True,
        },
    },
    {
        "slug": "cloudiy_devnet",
        "protocol": "Cloudiy",
        "network": "Solana devnet",
        "docs": "https://cloudiy.cloud/",
        "contracts": {"note": "Devnet USDC escrow — mainnet roadmap"},
        "kind": "PERMISSIONLESS_COMPUTE",
        "automatic_payout": True,
        "non_transferable_reward": False,
        "incomplete_reason": "TESTNET",
        "p02_filters": {
            "NO_TOKEN_PURCHASE": True,
            "NO_STAKE": True,
            "NO_COLLATERAL": True,
            "NO_REQUIRED_CAPITAL": True,
            "NO_INVITE_REFERRAL": True,
            "NO_TESTNET": False,
            "NO_POINTS_ASSET": True,
            "NO_VCORE_LIQUIDITY": True,
            "PUBLIC_WORK": True,
            "VERIFIABLE_PROOF": True,
            "PUBLIC_PAYMENT_CONDITION": True,
            "TRANSFERABLE_EXTERNAL_ASSET": False,
        },
        "economic": {
            "ACTION": "provide_compute_signed_result",
            "SOURCE": "usdc_escrow",
            "ASSET": "USDC",
            "AMOUNT": None,
            "DESTINATION": "solana_wallet",
            "PAYOUT_RULE": "Escrow releases USDC after signature verification",
            "ON_CHAIN_PROOF": None,
            "TRANSFERABILITY": "Would be transferable on mainnet — currently devnet test funds",
        },
    },
    {
        "slug": "zerog_compute_provider",
        "protocol": "0G Compute",
        "network": "0G chain",
        "docs": "https://compute.0g.ai/",
        "contracts": {"note": "Provider registration requires token stake per docs"},
        "kind": "PERMISSIONLESS_COMPUTE",
        "automatic_payout": False,
        "non_transferable_reward": False,
        "incomplete_reason": "STAKE_REQUIRED",
        "p02_filters": {
            "NO_TOKEN_PURCHASE": False,
            "NO_STAKE": False,
            "NO_COLLATERAL": False,
            "NO_REQUIRED_CAPITAL": False,
            "NO_INVITE_REFERRAL": True,
            "NO_TESTNET": True,
            "NO_POINTS_ASSET": True,
            "NO_VCORE_LIQUIDITY": True,
            "PUBLIC_WORK": True,
            "VERIFIABLE_PROOF": True,
            "PUBLIC_PAYMENT_CONDITION": True,
            "TRANSFERABLE_EXTERNAL_ASSET": True,
        },
        "economic": {
            "ACTION": "register_gpu_stake_tokens",
            "SOURCE": "inference_fees",
            "ASSET": "0G/token",
            "AMOUNT": None,
            "DESTINATION": "provider_wallet",
            "PAYOUT_RULE": "Stake required for providers",
            "ON_CHAIN_PROOF": None,
            "TRANSFERABILITY": "UNKNOWN",
        },
    },
    {
        "slug": "kascompute_testnet",
        "protocol": "KASCompute",
        "network": "Kaspa testnet",
        "docs": "https://kascompute.org/",
        "contracts": {"note": "No economic rewards active on testnet"},
        "kind": "PERMISSIONLESS_COMPUTE",
        "automatic_payout": False,
        "non_transferable_reward": True,
        "incomplete_reason": "TESTNET_NO_REWARDS",
        "p02_filters": {
            "NO_TOKEN_PURCHASE": True,
            "NO_STAKE": True,
            "NO_COLLATERAL": True,
            "NO_REQUIRED_CAPITAL": True,
            "NO_INVITE_REFERRAL": True,
            "NO_TESTNET": False,
            "NO_POINTS_ASSET": False,
            "NO_VCORE_LIQUIDITY": True,
            "PUBLIC_WORK": True,
            "VERIFIABLE_PROOF": True,
            "PUBLIC_PAYMENT_CONDITION": False,
            "TRANSFERABLE_EXTERNAL_ASSET": False,
        },
        "economic": {
            "ACTION": "run_proof_of_compute_jobs",
            "SOURCE": "none_active",
            "ASSET": "KCT",
            "AMOUNT": None,
            "DESTINATION": "node_wallet",
            "PAYOUT_RULE": "Testnet only — no compute execution rewards active",
            "ON_CHAIN_PROOF": None,
            "TRANSFERABILITY": "NON_TRANSFERABLE / no active rewards",
        },
    },
]


def analyze_p02_candidate(spec: dict[str, Any]) -> dict[str, Any]:
    opp = _opp_from_candidate(spec)
    brick = classify_brick(opp)
    failed = _failed_gates(spec)
    p02_pass = len(failed) == 0

    incomplete_reason = spec.get("incomplete_reason")
    if spec.get("non_transferable_reward") and brick["status"] != "CANDIDATE_REAL_BRICK":
        incomplete_reason = incomplete_reason or "NON_TRANSFERABLE_REWARD"
    if "NO_TESTNET" in failed:
        incomplete_reason = incomplete_reason or "TESTNET"
    if "NO_STAKE" in failed or "NO_REQUIRED_CAPITAL" in failed:
        incomplete_reason = incomplete_reason or "CAPITAL_OR_STAKE"
    if brick["missing"] and not incomplete_reason:
        incomplete_reason = "MISSING_BRICK_FIELDS"

    return {
        "slug": spec["slug"],
        "protocol": spec["protocol"],
        "p02_filter_pass": p02_pass,
        "failed_p02_gates": failed,
        "p02_gate_results": _gate_results(spec),
        "brick_status": brick["status"],
        "incomplete_reason": incomplete_reason,
        "missing_brick_fields": brick["missing"],
        "friction_violations": brick["friction_violations"],
        "brick": extract_brick(opp),
        "state_machine": spec.get("state_machine"),
        "work": spec.get("work"),
        "proof": spec.get("proof"),
        "contracts": spec.get("contracts"),
        "docs": spec.get("docs"),
        "p02_risks": spec.get("p02_risks"),
        "pass_schema": {
            "protocol": spec["protocol"],
            "contract": (spec.get("contracts") or {}).get("GLM_ERC20_POLYGON")
            or (spec.get("contracts") or {}).get("GLM_ERC20_ETHEREUM")
            or (spec.get("contracts") or {}).get("note"),
            "condition": (spec.get("state_machine") or {}).get("public_condition"),
            "work": (spec.get("work") or {}).get("type"),
            "proof": (spec.get("proof") or {}).get("type"),
            "asset": spec["economic"].get("ASSET"),
            "amount": spec["economic"].get("AMOUNT"),
            "amount_rule": spec["economic"].get("amount_rule"),
            "destination": spec["economic"].get("DESTINATION"),
            "on_chain_proof": spec["economic"].get("ON_CHAIN_PROOF"),
            "state": brick["status"],
        },
    }


def run_experiment_p02(*, include_p01_control: bool = True) -> dict[str, Any]:
    """Run P-02 across capital-free compute candidates; retain P-01 as CONTROL."""
    analyses = [analyze_p02_candidate(c) for c in P02_CANDIDATES]
    analyses.sort(
        key=lambda x: (
            0 if x["brick_status"] == "CANDIDATE_REAL_BRICK" else 1,
            0 if x["p02_filter_pass"] else 1,
            len(x["failed_p02_gates"]),
            len(x["missing_brick_fields"]),
            x["slug"],
        )
    )

    best = analyses[0] if analyses else None
    candidates_real = [a for a in analyses if a["brick_status"] == "CANDIDATE_REAL_BRICK"]
    filter_pass = [a for a in analyses if a["p02_filter_pass"]]

    p01_control = None
    if include_p01_control:
        p01 = run_experiment_p01(protocol_slug="livepeer_arbitrum")
        p01_control = {
            **P01_CONTROL_SUMMARY,
            "p01_outcome": p01.get("experiment_outcome"),
            "p01_pass_schema": p01.get("pass_schema"),
        }

    if candidates_real:
        outcome = "P02_PASS_CANDIDATE_REAL"
        message = (
            f"P-02: найден CANDIDATE_REAL_BRICK ×{len(candidates_real)} при capital-free фильтре. "
            "Дальше: simulation → owner → TX → REAL_EXTERNAL_ASSET."
        )
    elif filter_pass:
        outcome = "P02_FILTER_PASS_BRICK_INCOMPLETE"
        message = (
            f"P-02: {len(filter_pass)} протокол(ов) прошли capital-free фильтр, "
            f"но brick INCOMPLETE (часто AMOUNT/demand). Лучший: {best['protocol'] if best else '—'}."
        )
    else:
        outcome = "P02_NO_CAPITAL_FREE_CANDIDATE"
        message = (
            "P-02: ни один исследованный протокол не прошёл все capital-free gates. "
            "Nexus=points, Cloudiy/KASCompute=testnet, 0G=stake. Golem ближе всего — см. risks."
        )

    theory = {
        "methodology_still_valid": True,
        "p01_control_proves_compute_reward_not_equal_eur_zero": True,
        "p02_separates_work_input_from_capital_input": True,
        "non_transferable_counts_as_incomplete": True,
        "candidate_real_at_eur_zero": len(candidates_real) > 0,
        "real_external_asset": False,
        "vcore_not_used": True,
    }

    report = {
        "experiment_id": "P-02",
        "title": "Capital-free verifiable work → transferable external asset",
        "version": "1.0.0",
        "at": _now(),
        "hypothesis": (
            "Virtus can obtain transferable external asset via verifiable work "
            "without upfront token purchase, stake, collateral, or required capital."
        ),
        "p02_filter_gates": list(P02_FILTER_GATES),
        "p01_control": p01_control,
        "experiment_outcome": outcome,
        "message": message,
        "theory_check": theory,
        "counts": {
            "candidates_analyzed": len(analyses),
            "p02_filter_full_pass": len(filter_pass),
            "candidate_real_brick": len(candidates_real),
            "real_external_asset": 0,
        },
        "best_candidate": best,
        "ranked_analyses": analyses,
        "brick_fields_schema": list(BRICK_FIELDS),
        "next": (
            "If Golem (or other filter-pass): quantify expected GLM/job from live market + "
            "run provider dry-run → measure first payment TXID. "
            "Do not treat points/testnet/stake protocols as wins."
        ),
        "agent_policy": {
            "non_transferable_reward": "INCOMPLETE — reason NON_TRANSFERABLE_REWARD",
            "testnet": "INCOMPLETE — not income experiment",
            "may_end_with": "P02_FILTER_PASS_BRICK_INCOMPLETE",
        },
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    (_RUNTIME / "p02_capital_free_compute.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
