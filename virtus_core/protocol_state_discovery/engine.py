"""
Protocol State Discovery Engine

Insight (not another Value Hunter):
  PUBLIC SYSTEM has F(X) → Virtus computes X → condition met → system emits/pays → REAL ASSET

Three cores (research-only — no exploit, no key crack, no bypass):
  PUBLIC CONTRACT ANALYZER
  STATE TRANSITION ANALYZER
  REWARD FLOW ANALYZER

Axiom: liquidity does not appear from VCORE. Seek emission/distribution activated by computable proof.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from virtus_core.opportunity_ai.economic_brick import classify_brick

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "protocol_state_discovery"
_LAST = _RUNTIME / "last_discovery.json"

RESEARCH_QUESTION = (
    "Существует ли публичный механизм, где Virtus может выполнить разрешённое "
    "вычислительное действие, не вкладывая собственные средства, после чего внешний "
    "протокол автоматически отправляет реальный transferable asset на указанный wallet?"
)

AXIOM = "Liquidity does not appear from VCORE. Seek compute→proof→state transition→reward."


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


# --- Core 1: Public Contract Analyzer (classes, not random ABI dump) ---

CONTRACT_CLASSES: list[dict[str, Any]] = [
    {
        "class_id": "merkle_claim",
        "public_functions": ["claim(proof, amount)", "isClaimed"],
        "payment_trigger": "valid merkle proof + unclaimed leaf",
        "computable_by_virtus": "partial — needs leaf in tree (not inventable)",
        "own_capital": "often gas only",
        "notes": "Emission already allocated; Virtus cannot mint new leaves",
    },
    {
        "class_id": "faucet_drip",
        "public_functions": ["requestTokens", "claim"],
        "payment_trigger": "rate-limit / captcha / social gate",
        "computable_by_virtus": "no — human/captcha gates common",
        "own_capital": "€0 but often non-automatable",
        "notes": "Testnet TON faucet = infra, not income",
    },
    {
        "class_id": "compute_marketplace",
        "public_functions": ["submitWork", "verify", "releasePayment"],
        "payment_trigger": "accepted verifiable work result",
        "computable_by_virtus": "YES if task matches CPU/GPU capability",
        "own_capital": "€0 if gas sponsored or claim is free",
        "notes": "PRIMARY insight target — concrete instance still RESEARCH_REQUIRED",
    },
    {
        "class_id": "staking_reward",
        "public_functions": ["stake", "claimRewards"],
        "payment_trigger": "prior deposit/stake",
        "computable_by_virtus": "n/a — capital required",
        "own_capital": ">0",
        "notes": "REJECT under €0 axiom",
    },
    {
        "class_id": "lp_incentive",
        "public_functions": ["addLiquidity", "harvest"],
        "payment_trigger": "LP deposit",
        "computable_by_virtus": "n/a",
        "own_capital": ">0",
        "notes": "REJECT — VCORE→pool is not the insight",
    },
    {
        "class_id": "sponsored_execution",
        "public_functions": ["execute(metaTx)", "relay"],
        "payment_trigger": "sponsor pays gas; reward optional",
        "computable_by_virtus": "maybe — need documented campaign",
        "own_capital": "€0 if sponsor real",
        "notes": "Gas ≠ reward asset; still need payment function",
    },
]


def public_contract_analyzer() -> dict[str, Any]:
    return {
        "core": "PUBLIC_CONTRACT_ANALYZER",
        "mode": "research_class_catalog",
        "axiom": AXIOM,
        "question": "Which public function surfaces can legally move assets?",
        "classes": CONTRACT_CLASSES,
        "forbidden": [
            "exploit / reentrancy hunt as income strategy",
            "private key / BIP39 foreign wallet",
            "access-control bypass",
        ],
        "priority_class": "compute_marketplace",
    }


# --- Core 2: State Transition Analyzer ---

def state_transition_analyzer(candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    """Map candidate onto STATE A → condition → STATE B → reward."""
    kind = str(
        (candidate or {}).get("kind")
        or (candidate or {}).get("sourceType")
        or (candidate or {}).get("source")
        or ""
    ).upper()

    templates = {
        "PERMISSIONLESS_COMPUTE": {
            "state_a": "NO_WORK_SUBMITTED",
            "public_condition": "valid work proof accepted by verifier",
            "state_b": "WORK_ACCEPTED",
            "automatic_reward": True,
            "virtus_can_produce_proof": "UNKNOWN_UNTIL_CONCRETE_PROTOCOL",
            "capital_eur_0": True,
            "reward_deterministic": "UNKNOWN",
            "reward_source": "protocol_treasury_or_escrow",
            "tx_verifiable": "YES_IF_ONCHAIN",
        },
        "OPEN_PROTOCOL_REWARDS": {
            "state_a": "ELIGIBLE_UNCLAIMED",
            "public_condition": "permissionless claim() success",
            "state_b": "CLAIMED",
            "automatic_reward": True,
            "virtus_can_produce_proof": "IF_ELIGIBILITY_PUBLIC",
            "capital_eur_0": "GAS_MAY_BLOCK",
            "reward_deterministic": "UNKNOWN",
            "reward_source": "UNKNOWN",
            "tx_verifiable": "YES_IF_ONCHAIN",
        },
        "TESTNET_REWARD": {
            "state_a": "UNFUNDED_TEST_WALLET",
            "public_condition": "faucet grants / bot allows request",
            "state_b": "TESTNET_BALANCE_GT_0",
            "automatic_reward": False,
            "virtus_can_produce_proof": "NO_CAPTCHA",
            "capital_eur_0": True,
            "reward_deterministic": False,
            "reward_source": "faucet_operator",
            "tx_verifiable": "YES_ON_TESTNET",
            "note": "Not convertible income; Genesis infra only",
        },
        "EXIT_CONVERTER": {
            "state_a": "HOLD_SUPPORTED_ASSET",
            "public_condition": "swap route exists",
            "state_b": "RECEIVE_BTC_OR_TON",
            "automatic_reward": False,
            "virtus_can_produce_proof": "n/a — needs inbound asset first",
            "capital_eur_0": False,
            "reward_deterministic": False,
            "reward_source": "user_inventory",
            "tx_verifiable": "YES",
            "note": "EXIT ≠ emission. Reject as primary insight.",
        },
        "DEFAULT": {
            "state_a": "UNKNOWN",
            "public_condition": "UNKNOWN",
            "state_b": "UNKNOWN",
            "automatic_reward": None,
            "virtus_can_produce_proof": "UNKNOWN",
            "capital_eur_0": None,
            "reward_deterministic": None,
            "reward_source": "UNKNOWN",
            "tx_verifiable": "UNKNOWN",
        },
    }

    key = "DEFAULT"
    for k in templates:
        if k != "DEFAULT" and k in kind:
            key = k
            break
    if "FAUCET" in kind or "TESTNET" in kind:
        key = "TESTNET_REWARD"
    if "EXIT" in kind or "THOR" in kind:
        key = "EXIT_CONVERTER"
    if "COMPUTE" in kind:
        key = "PERMISSIONLESS_COMPUTE"
    if "PROTOCOL_REWARD" in kind or "OPEN_PROTOCOL" in kind:
        key = "OPEN_PROTOCOL_REWARDS"

    machine = templates[key]
    questions = {
        "Can Virtus produce the required proof?": machine.get("virtus_can_produce_proof"),
        "Can it do so with €0?": machine.get("capital_eur_0"),
        "Is reward deterministic?": machine.get("reward_deterministic"),
        "Where does reward come from?": machine.get("reward_source"),
        "Can transaction be verified?": machine.get("tx_verifiable"),
    }
    experiment_ready = all(
        str(questions[q]).upper() in ("YES", "TRUE", "YES_IF_ONCHAIN", "YES_ON_TESTNET")
        for q in (
            "Can Virtus produce the required proof?",
            "Can it do so with €0?",
            "Can transaction be verified?",
        )
    ) and machine.get("automatic_reward") is True

    return {
        "core": "STATE_TRANSITION_ANALYZER",
        "template": key,
        "machine": machine,
        "insight_questions": questions,
        "experiment_ready": experiment_ready,
        "path": "STATE A → public condition → STATE B → automatic reward",
    }


# --- Core 3: Reward Flow Analyzer ---

def reward_flow_analyzer(candidate: dict[str, Any] | None = None) -> dict[str, Any]:
    c = candidate or {}
    asset = c.get("asset") or c.get("counterAsset") or c.get("ASSET")
    amount = c.get("expectedAmount") if "expectedAmount" in c else c.get("expected_gross")
    auto = c.get("automatic_payout")
    evidence = c.get("evidence") or c.get("url") or ""

    vcore_liquidity_trap = str(asset or "").upper() == "VCORE" or "VCORE" in str(c.get("protocol") or "").upper()
    is_hypothesis = str(c.get("status") or "").upper() in ("HYPOTHESIS", "ZERO_CAPITAL") and (
        "RESEARCH" in str(evidence).upper() or "HYPOTHESIS" in str(evidence).upper() or not evidence
    )

    return {
        "core": "REWARD_FLOW_ANALYZER",
        "asset": asset,
        "amount_known": amount not in (None, "", 0, 0.0),
        "amount": amount,
        "automatic_payout": auto,
        "source_of_funds_documented": bool(evidence) and "RESEARCH" not in str(evidence).upper(),
        "vcore_liquidity_trap": vcore_liquidity_trap,
        "is_class_hypothesis_not_instance": is_hypothesis or "RESEARCH" in str(evidence).upper(),
        "flow": "protocol_reserve_or_escrow → transfer/mint → destination_wallet",
        "reject_if": [
            "reward funded only by our deposit",
            "VCORE painted as counter-liquidity",
            "amount unknown",
            "no on-chain payment function",
        ],
    }


def autopsy_candidate(opp: dict[str, Any]) -> dict[str, Any]:
    brick = classify_brick(opp)
    st = state_transition_analyzer(opp)
    rf = reward_flow_analyzer(opp)
    oid = opp.get("opportunityId") or opp.get("id")

    # Honest why-not for incomplete
    why: list[str] = []
    if brick["friction_violations"]:
        why.append(f"friction: {brick['friction_violations']}")
    if brick["missing"]:
        why.append(f"missing: {brick['missing']}")
    if rf.get("vcore_liquidity_trap"):
        why.append("AXIOM: VCORE does not create external liquidity")
    if rf.get("is_class_hypothesis_not_instance"):
        why.append("class/hypothesis — no concrete contract instance")
    if st["template"] == "EXIT_CONVERTER":
        why.append("EXIT converter needs inbound real asset first — not emission")
    if st["template"] == "TESTNET_REWARD":
        why.append("testnet faucet ≠ transferable income / treasury")
    if not st.get("experiment_ready"):
        why.append("state-machine experiment not ready (proof/€0/auto-reward)")

    return {
        "id": oid,
        "origin": opp.get("_origin"),
        "kind": opp.get("kind") or opp.get("sourceType") or opp.get("source"),
        "brick_status": brick["status"],
        "brick": brick["brick"],
        "missing": brick["missing"],
        "friction_violations": brick["friction_violations"],
        "state_machine": st,
        "reward_flow": rf,
        "why_not_real_yet": why,
        "insight_fit": st["template"] == "PERMISSIONLESS_COMPUTE" and not rf.get("vcore_liquidity_trap"),
    }


def run_protocol_state_discovery(*, offline: bool = False) -> dict[str, Any]:
    """Deep autopsy of frictionless candidates + three analyzer cores."""
    from virtus_core.opportunity_ai.systematic import systematic_discover

    # Full live/offline systematic to get same candidate set as UI
    sysd = systematic_discover(offline=offline, measure_compute=False)

    # Rebuild scored list via same merge path — use top + re-fetch raw for autopsy depth
    from virtus_core.counter_liquidity.engine import discover as cl_discover
    from virtus_core.value_hunter.pipeline import process_pipeline
    from virtus_core.opportunity_ai.systematic import _funnel_questions

    cl = cl_discover(offline=offline)
    vh = process_pipeline(offline=offline)
    raw: list[dict[str, Any]] = []
    for o in cl.get("opportunities") or []:
        raw.append({**o, "_origin": "counter_liquidity"})
    for o in vh.get("opportunities") or []:
        raw.append(
            {
                "opportunityId": o.get("id"),
                "protocol": o.get("protocol") or o.get("kind"),
                "kind": o.get("kind"),
                "source": o.get("source_of_funds_type"),
                "sourceType": o.get("source_of_funds_type"),
                "asset": o.get("asset"),
                "counterAsset": o.get("asset"),
                "capital_required": o.get("capital_required_eur") or 0,
                "gas_required": o.get("gas_required_eur") or 0,
                "eligibility": o.get("eligibility"),
                "action": o.get("required_action"),
                "withdrawalPath": o.get("withdrawal_path"),
                "evidence": o.get("source_of_funds_evidence") or o.get("url"),
                "automatic_payout": o.get("kind") in ("TESTNET_REWARD", "COMPUTE_REWARD"),
                "registration_required": o.get("registration_required"),
                "account_required": o.get("account_required"),
                "kyc_required": o.get("kyc_required"),
                "application_required": o.get("kind") in ("DEVELOPER_PROGRAM", "GRANT", "BUG_BOUNTY"),
                "deposit_required": False,
                "purchase_required": False,
                "stake_required": False,
                "expectedAmount": o.get("expected_gross"),
                "status": o.get("status"),
                "forbidden": o.get("forbidden"),
                "reward_rule": o.get("reward_rule"),
                "_origin": "value_hunter",
            }
        )

    frictionless: list[dict[str, Any]] = []
    for o in raw:
        if o.get("forbidden"):
            continue
        funnel = _funnel_questions(o)
        if funnel["strict_zero_friction_pass"] and not funnel["working_brick"]:
            frictionless.append(o)

    autopsies = [autopsy_candidate(o) for o in frictionless]
    insight_fits = [a for a in autopsies if a.get("insight_fit")]
    candidates_real = [a for a in autopsies if a["brick_status"] == "CANDIDATE_REAL_BRICK"]
    incomplete = [a for a in autopsies if a["brick_status"] == "INCOMPLETE_ECONOMIC_BRICK"]

    # Aggregate missing field frequency
    miss_freq: dict[str, int] = {}
    for a in incomplete:
        for m in a.get("missing") or []:
            miss_freq[m] = miss_freq.get(m, 0) + 1

    pca = public_contract_analyzer()

    if candidates_real:
        epoch = "CANDIDATE_REAL_BRICK_FOUND"
        scientific = "CONTINUE_TO_SIMULATION_OWNER_GATE"
        message = (
            f"Найден CANDIDATE_REAL_BRICK ×{len(candidates_real)}. "
            "Дальше: simulation → owner → on-chain. REAL только после TX."
        )
    else:
        epoch = "NO_VALID_OPPORTUNITY"
        scientific = "FRICTIONLESS_AUTOPSY_COMPLETE"
        message = (
            f"Глубокий разбор {len(autopsies)} frictionless: все INCOMPLETE_ECONOMIC_BRICK. "
            f"Частые дыры: {sorted(miss_freq.items(), key=lambda x: -x[1])[:5]}. "
            "Инсайт-класс: искать конкретный compute_marketplace instance, не VCORE→пул."
        )

    report = {
        "engine": "Protocol State Discovery Engine",
        "version": "1.0.0",
        "at": _now(),
        "axiom": AXIOM,
        "research_question": RESEARCH_QUESTION,
        "insight_class": "compute → proof → protocol state transition → reward",
        "not_insight": ["VCORE → exchanger → money", "VCORE → pool → TON", "paint BALANCE=$1M"],
        "cores": {
            "public_contract_analyzer": pca,
            "state_transition_analyzer": "per-candidate in autopsy",
            "reward_flow_analyzer": "per-candidate in autopsy",
        },
        "epoch_status": epoch,
        "scientific_result": scientific,
        "message": message,
        "counts": {
            "frictionless_autopsied": len(autopsies),
            "incomplete_economic_brick": len(incomplete),
            "candidate_real_brick": len(candidates_real),
            "real_external_asset": 0,
            "insight_fit_compute_path": len(insight_fits),
        },
        "missing_field_frequency": miss_freq,
        "autopsy": autopsies,
        "insight_fit_ids": [a["id"] for a in insight_fits],
        "systematic_epoch": sysd.get("epoch_status"),
        "next": (
            "1) Pick insight_fit IDs (compute path). "
            "2) Replace class/hypothesis with ONE concrete public protocol (docs+contract). "
            "3) Fill AMOUNT+DESTINATION+PAYOUT_RULE+ON_CHAIN_PROOF. "
            "4) Only then simulate → owner gate → TX. "
            "Do not invent VCORE price."
        ),
        "agent_policy": {
            "may_end_with": "NO_VALID_OPPORTUNITY",
            "must_not": "force-confirm hypothesis / treat vectors/s as income",
        },
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
