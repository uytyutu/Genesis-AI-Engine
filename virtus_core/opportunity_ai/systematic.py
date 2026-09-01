"""
Opportunity AI — Systematic Economic Discovery

Not a second hunter. Orchestrates existing layers into an economic funnel:

  PUBLIC MECHANISMS
      → €0 / no account / no KYC / no application / no deposit / no purchase / no stake?
      → concrete action that creates payout right
      → source of funds
      → asset
      → how it arrives on wallet
      → on-chain confirmable?
      → convertible?

Priority (compute-first — Virtus already measures CPU work):
  1 COMPUTE → REWARD
  2 PUBLIC VERIFIABLE WORK → REWARD
  3 PERMISSIONLESS PROTOCOL → REWARD
  4 SPONSORED COMPUTE → REWARD
  5 AUTOMATIC ON-CHAIN REWARD
  6 COUNTER-LIQUIDITY
  7 OTHER

Honest epoch end: NO_VALID_OPPORTUNITY is success-of-science, not agent failure.
Vectors/s = compute capability, never income.
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from virtus_core.opportunity_ai.economic_brick import classify_brick

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "opportunity_ai"
_LAST = _RUNTIME / "last_systematic.json"

from virtus_core.opportunity_ai.economic_brick import classify_brick

PRIORITY = (
    "COMPUTE_REWARD",
    "PUBLIC_VERIFIABLE_WORK",
    "PERMISSIONLESS_PROTOCOL",
    "SPONSORED_COMPUTE",
    "AUTOMATIC_ONCHAIN_REWARD",
    "COUNTER_LIQUIDITY",
    "OTHER",
)

FUNNEL_GATES = (
    ("own_capital_eur", 0, "capital"),
    ("registration", False, "registration"),
    ("kyc", False, "kyc"),
    ("application", False, "application"),
    ("deposit", False, "deposit"),
    ("purchase", False, "purchase"),
    ("stake", False, "stake"),
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _priority_rank(opp: dict[str, Any]) -> int:
    kind = (opp.get("kind") or opp.get("sourceType") or opp.get("source") or "").upper()
    mapping = [
        (("COMPUTE", "PERMISSIONLESS_COMPUTE"), 0),
        (("PUBLIC_VERIFIABLE", "VERIFIABLE_WORK"), 1),
        (("OPEN_PROTOCOL", "PERMISSIONLESS_PROTOCOL", "PROTOCOL_REWARD"), 2),
        (("SPONSORED_COMPUTE", "SPONSORED_EXECUTION", "SPONSORED"), 3),
        (("AUTOMATIC", "ONCHAIN_REWARD", "ON_CHAIN"), 4),
        (("COUNTER", "LIQUIDITY", "POOL", "BONDING"), 5),
    ]
    for keys, rank in mapping:
        if any(k in kind for k in keys):
            return rank
    # Hypotheses about compute stay high
    if opp.get("status") == "HYPOTHESIS" and "COMPUTE" in kind:
        return 0
    return 6


def _funnel_questions(opp: dict[str, Any]) -> dict[str, Any]:
    capital = float(opp.get("capital_required") or opp.get("capital_required_eur") or 0)
    registration = bool(opp.get("registration_required") or opp.get("account_required") or opp.get("accountRequired"))
    kyc = bool(opp.get("kyc_required") or opp.get("kycRequired"))
    application = bool(
        opp.get("application_required")
        or opp.get("applicationRequired")
        or opp.get("approval_required")
        or "proposal" in str(opp.get("eligibility") or "").lower()
        or "acceptance" in str(opp.get("eligibility") or "").lower()
    )
    deposit = bool(opp.get("deposit_required") or opp.get("depositRequired"))
    purchase = bool(opp.get("purchase_required") or opp.get("purchaseRequired"))
    stake = bool(opp.get("stake_required") or opp.get("stakeRequired"))

    gates = {
        "own_capital_eur_0": capital <= 0,
        "no_registration": not registration,
        "no_kyc": not kyc,
        "no_application": not application,
        "no_deposit": not deposit,
        "no_purchase": not purchase,
        "no_stake": not stake,
    }
    strict_pass = all(gates.values())

    classified = classify_brick(opp)
    brick = classified["brick"]
    economic = {
        "concrete_action": brick.get("ACTION") or "UNKNOWN",
        "action_known": brick.get("ACTION") is not None,
        "source_of_funds": brick.get("SOURCE") or "UNKNOWN",
        "source_known": brick.get("SOURCE") is not None,
        "asset": brick.get("ASSET") or "UNKNOWN",
        "asset_known": brick.get("ASSET") is not None,
        "wallet_arrival": brick.get("DESTINATION") or "UNKNOWN",
        "arrival_known": brick.get("DESTINATION") is not None,
        "on_chain_confirmable": brick.get("ON_CHAIN_PROOF") is not None,
        "convertible": bool(brick.get("TRANSFERABILITY")),
        "amount_known": brick.get("AMOUNT") is not None,
        "payout_rule_known": brick.get("PAYOUT_RULE") is not None,
    }

    brick_ready = classified["status"] == "CANDIDATE_REAL_BRICK"

    return {
        "gates": gates,
        "strict_zero_friction_pass": strict_pass,
        "economic": economic,
        "working_brick": brick_ready and strict_pass,
        "brick_status": classified["status"],
        "brick": brick,
        "failed_gates": [k for k, v in gates.items() if not v],
        "failed_economic": classified["missing"],
        "friction_violations": classified["friction_violations"],
    }


def _compute_capability() -> dict[str, Any]:
    """Measure only — never paint as income."""
    try:
        from virtus_core.bip39_compute_lab.lab import run_bip39_bench

        b = run_bip39_bench(workers=4, batch_per_worker=80)
        return {
            "vectors_per_sec": b.get("vectors_per_sec"),
            "workers": b.get("workers"),
            "income_claimed": False,
            "role": "CAPABILITY_MEASUREMENT_ONLY",
        }
    except Exception as e:
        return {"vectors_per_sec": None, "income_claimed": False, "error": str(e)}


def systematic_discover(
    *,
    offline: bool = False,
    reuse_vh: dict[str, Any] | None = None,
    reuse_cl: dict[str, Any] | None = None,
    measure_compute: bool = True,
) -> dict[str, Any]:
    from virtus_core.counter_liquidity.engine import discover as cl_discover
    from virtus_core.value_hunter.pipeline import process_pipeline

    cl = reuse_cl if reuse_cl is not None else cl_discover(offline=offline)
    vh = reuse_vh if reuse_vh is not None else process_pipeline(offline=offline)
    if measure_compute and not offline:
        capability = _compute_capability()
    else:
        capability = {"vectors_per_sec": None, "offline": offline or not measure_compute, "income_claimed": False}

    # Merge candidates from both layers
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
                "_origin": "value_hunter",
            }
        )

    scored: list[dict[str, Any]] = []
    for o in raw:
        if o.get("forbidden") or o.get("requires_foreign_wallet"):
            funnel = {"strict_zero_friction_pass": False, "working_brick": False, "failed_gates": ["security"], "gates": {}, "economic": {}}
            scored.append({**o, "priority_rank": 99, "priority_label": "SECURITY_REJECTED", "funnel": funnel, "verdict": "SECURITY_REJECTED"})
            continue
        rank = _priority_rank(o)
        funnel = _funnel_questions(o)
        if funnel["working_brick"]:
            verdict = "CANDIDATE_REAL_BRICK"
        elif funnel["strict_zero_friction_pass"]:
            verdict = "INCOMPLETE_ECONOMIC_BRICK"
        else:
            verdict = "FILTERED_OUT"
        scored.append(
            {
                **o,
                "priority_rank": rank,
                "priority_label": PRIORITY[min(rank, len(PRIORITY) - 1)],
                "funnel": funnel,
                "verdict": verdict,
                "brick_status": funnel.get("brick_status"),
            }
        )

    scored.sort(key=lambda x: (0 if x["verdict"] == "CANDIDATE_REAL_BRICK" else 1, x["priority_rank"], x.get("opportunityId") or ""))

    bricks = [x for x in scored if x["verdict"] == "CANDIDATE_REAL_BRICK"]
    frictionless = [x for x in scored if x["verdict"] == "INCOMPLETE_ECONOMIC_BRICK"]
    filtered = [x for x in scored if x["verdict"] == "FILTERED_OUT"]

    # Compute-first slice
    by_priority: dict[str, list[str]] = {p: [] for p in PRIORITY}
    for x in scored:
        by_priority.setdefault(x["priority_label"], []).append(str(x.get("opportunityId")))

    if bricks:
        epoch_status = "CANDIDATE_FOUND"
        scientific = "CONTINUE_VERIFY"
        message = f"Найден CANDIDATE_REAL_BRICK ({len(bricks)}). Дальше: simulation → owner → on-chain — без auto-broadcast. REAL только после TX."
    elif frictionless:
        epoch_status = "NO_VALID_OPPORTUNITY"
        scientific = "HONEST_NEGATIVE_WITH_LEADS"
        message = (
            f"NO_VALID_OPPORTUNITY: INCOMPLETE_ECONOMIC_BRICK={len(frictionless)}. "
            f"Нужен Protocol State Discovery: compute→proof→state→reward (не VCORE→пул). "
            f"Capability={capability.get('vectors_per_sec')} vec/s ≠ income."
        )
    else:
        epoch_status = "NO_VALID_OPPORTUNITY"
        scientific = "HONEST_NEGATIVE"
        message = (
            "NO_VALID_OPPORTUNITY: ни один публичный механизм не прошёл €0 + no-account funnel. "
            "Это валидный научный результат — не ошибка агента. Не подтверждать гипотезу силой."
        )

    report = {
        "engine": "Opportunity AI — Systematic Economic Discovery",
        "version": "1.1.0",
        "at": _now(),
        "research_question": (
            "Существует ли публичный механизм, где Virtus выполняет разрешённое вычислительное действие "
            "при €0, после чего протокол автоматически отправляет transferable asset на wallet?"
        ),
        "axiom": "Liquidity does not appear from VCORE.",
        "thesis": (
            "Not create value from air — discover existing external value and lawfully deliver it "
            "to a controlled wallet. Test = TXID + network confirm + balance increase — not BALANCE=$1M in DB."
        ),
        "brick_statuses": [
            "INCOMPLETE_ECONOMIC_BRICK",
            "CANDIDATE_REAL_BRICK",
            "REAL_EXTERNAL_ASSET",
        ],
        "priority_order": list(PRIORITY),
        "compute_capability": capability,
        "epoch_status": epoch_status,
        "scientific_result": scientific,
        "message": message,
        "counts": {
            "mechanisms_scanned": len(scored),
            "working_brick_candidates": len(bricks),
            "candidate_real_brick": len(bricks),
            "frictionless_incomplete": len(frictionless),
            "incomplete_economic_brick": len(frictionless),
            "filtered_out": len(filtered),
            "real_external_assets": 0,
        },
        "by_priority": {k: v for k, v in by_priority.items() if v},
        "top_compute_first": [
            {
                "id": x.get("opportunityId"),
                "priority": x.get("priority_label"),
                "verdict": x.get("verdict"),
                "brick_status": x.get("brick_status") or x.get("verdict"),
                "action": (x.get("funnel") or {}).get("economic", {}).get("concrete_action"),
                "failed_gates": (x.get("funnel") or {}).get("failed_gates"),
                "failed_economic": (x.get("funnel") or {}).get("failed_economic"),
                "missing_brick_fields": (x.get("funnel") or {}).get("failed_economic"),
                "origin": x.get("_origin"),
            }
            for x in scored[:20]
        ],
        "working_bricks": bricks[:5],
        "counter_liquidity_outcome": cl.get("outcome"),
        "value_hunter_message": vh.get("message"),
        "agent_policy": {
            "may_end_epoch_with": "NO_VALID_OPPORTUNITY",
            "must_not": "keep searching until money appears / force-confirm hypothesis",
            "vectors_per_sec_is": "capability measurement only",
        },
        "next": (
            "Run Protocol State Discovery autopsy on INCOMPLETE bricks. "
            "Replace class/hypothesis with concrete compute_marketplace instance. "
            "Do not invent VCORE price."
        ),
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _LAST.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report
