"""
Counter-Liquidity Discovery Engine v1.0

Layer on top of Genesis / Route Finder / Value Hunter — does not replace them.
Hypothesis: can VCORE obtain REAL counter-liquidity at OWN_CAPITAL=€0?
NO is a valid scientific result.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from virtus_core.counter_liquidity.adapters import run_adapters
from virtus_core.counter_liquidity.filters import apply_strict_permissionless, implied_vs_executable
from virtus_core.counter_liquidity.proof import build_counter_liquidity_proof
from virtus_core.counter_liquidity.states import SECURITY_POLICY_IMMUTABLE

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "counter_liquidity"
_REPORT = _RUNTIME / "last_discover.json"
_GENESIS = _ROOT / ".runtime" / "vcore_genesis_state.json"
_EXP = _RUNTIME / "experience.jsonl"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _hash(o: dict[str, Any]) -> str:
    key = "|".join(
        [
            str(o.get("protocol") or ""),
            str(o.get("sourceType") or o.get("source") or ""),
            str(o.get("counterAsset") or ""),
            str(o.get("action") or ""),
            str(o.get("opportunityId") or ""),
        ]
    )
    return hashlib.sha256(key.encode()).hexdigest()[:20]


def genesis_vcore_status() -> dict[str, Any]:
    if not _GENESIS.exists():
        return {"vcore_valid": False, "stage": "NOT_STARTED", "jettonMaster": None}
    g = json.loads(_GENESIS.read_text(encoding="utf-8"))
    master = g.get("jettonMaster")
    stage = g.get("stage")
    return {
        "vcore_valid": bool(master) and stage in ("VERIFIED", "MINTED", "TRANSFERRED", "DEPLOYED"),
        "genesis_pass": stage == "VERIFIED" and bool(master),
        "stage": stage,
        "jettonMaster": master,
        "note": "Jetton identity ≠ counter-liquidity",
    }


def simulate_opp(opp: dict[str, Any]) -> dict[str, Any]:
    if not opp.get("strict_pass"):
        return {"ok": False, "status": "SIMULATION_FAILED", "reason": opp.get("status"), "broadcast": False}
    proof = opp.get("counter_liquidity_proof") or {}
    if proof.get("status") not in ("LIQUIDITY_VERIFIED",):
        return {
            "ok": False,
            "status": "SIMULATION_FAILED",
            "reason": proof.get("status") or "NO_REAL_LIQUIDITY",
            "broadcast": False,
            "max_executable": proof.get("maxExecutable"),
        }
    return {
        "ok": True,
        "status": "SIMULATION_PASS",
        "reason": "dry_run_only",
        "broadcast": False,
        "max_executable": proof.get("maxExecutable"),
        "note": "Owner gate required for any broadcast",
    }


def discover(*, offline: bool = False) -> dict[str, Any]:
    vcore = genesis_vcore_status()
    if offline:
        pack = {"at": _now(), "adapters": [], "raw": [], "status": "DISCOVERY_OFFLINE"}
        raw: list[dict[str, Any]] = []
    else:
        pack = run_adapters()
        raw = list(pack.get("raw") or [])

    # Dedup
    seen: dict[str, dict[str, Any]] = {}
    for item in raw:
        o = dict(item)
        o["hash"] = _hash(o)
        o["firstSeen"] = o.get("firstSeen") or _now()
        o["lastSeen"] = _now()
        h = o["hash"]
        if h in seen:
            seen[h]["lastSeen"] = _now()
            seen[h]["dedup_hits"] = int(seen[h].get("dedup_hits") or 1) + 1
            continue
        o["dedup_hits"] = 1
        seen[h] = o
    items = list(seen.values())

    processed: list[dict[str, Any]] = []
    hypotheses: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    zero_capital: list[dict[str, Any]] = []

    for o in items:
        if o.get("status") == "HYPOTHESIS":
            o["label"] = "HYPOTHESIS"
            o = apply_strict_permissionless(o)
            # Even hypotheses get filtered if clearly application/grant
            o["prices"] = implied_vs_executable(o)
            o["counter_liquidity_proof"] = build_counter_liquidity_proof(o)
            o["simulation"] = {"ok": False, "status": "HYPOTHESIS_NOT_OPPORTUNITY", "broadcast": False}
            hypotheses.append(o)
            processed.append(o)
            continue

        o = apply_strict_permissionless(o)
        o["prices"] = implied_vs_executable(o)

        # Empty bonding / empty pool → explicit no counter-liquidity
        if o.get("kind") in ("BONDING_CURVE", "PERMISSIONLESS_POOL") and float(o.get("poolReserve") or o.get("reserve") or 0) <= 0:
            if o.get("strict_pass"):
                o["status"] = "NO_REAL_COUNTER_LIQUIDITY"
                o["reject_reason"] = "no_initial_reserve"
                o["strict_pass"] = False

        # Aggregator / cross-chain without VCORE listing
        if o.get("kind") in ("AGGREGATOR", "CROSS_CHAIN") and not vcore.get("jettonMaster"):
            o["status"] = "UNSUPPORTED"
            o["reject_reason"] = "vcore_not_on_chain_or_not_listed"
            o["strict_pass"] = False

        o["counter_liquidity_proof"] = build_counter_liquidity_proof(o)
        o["simulation"] = simulate_opp(o)

        if o.get("strict_pass") and o["counter_liquidity_proof"]["status"] == "LIQUIDITY_VERIFIED":
            o["status"] = "LIQUIDITY_VERIFIED"
            zero_capital.append(o)
        elif o.get("strict_pass"):
            # Passed participation filter but no real liquidity yet
            o["status"] = o.get("status") or "ZERO_CAPITAL"
            if o["status"] == "ZERO_CAPITAL":
                o["status"] = "NO_REAL_COUNTER_LIQUIDITY"
            rejected.append(o)
        else:
            rejected.append(o)
        processed.append(o)

    n = len(processed)
    n_rej = len(rejected)
    n_hyp = len(hypotheses)
    n_zc = len(zero_capital)
    n_pending = max(0, n - n_rej - n_hyp - n_zc)
    # Hypotheses counted separately from rejected
    accounted = n_rej + n_hyp + n_zc + n_pending
    # Fix: hypotheses also in processed; rejected may overlap? We don't double-append.
    # pending = processed that are neither rejected list nor hyp nor zero — recompute
    hyp_ids = {h.get("opportunityId") for h in hypotheses}
    zc_ids = {z.get("opportunityId") for z in zero_capital}
    rej_ids = {r.get("opportunityId") for r in rejected}
    n_pending = sum(1 for p in processed if p.get("opportunityId") not in hyp_ids | zc_ids | rej_ids)
    accounted = len(rej_ids) + len(hyp_ids) + len(zc_ids) + n_pending
    invariant = "PASS" if accounted == n else "FAIL"

    # Research outcome
    if n_zc > 0:
        outcome = "VERIFIED_POSSIBLE"
    elif any(h.get("strict_pass") for h in hypotheses):
        outcome = "RESEARCH_REQUIRED"
    elif all(
        r.get("status") in ("CAPITAL_REQUIRED", "APPLICATION_REQUIRED", "ACCOUNT_REQUIRED", "KYC_REQUIRED", "GOVERNANCE_REQUIRED")
        for r in rejected
    ) and n_zc == 0:
        outcome = "NO_CAPITAL_PATH_FOUND"
    else:
        outcome = "NO_CAPITAL_PATH_FOUND"

    # Experience lessons
    lessons = []
    for r in rejected:
        lessons.append(
            {
                "hypothesis": r.get("opportunityId"),
                "protocol": r.get("protocol"),
                "mechanism": r.get("sourceType") or r.get("kind"),
                "result": "FAILED",
                "failureReason": r.get("reject_reason") or r.get("status"),
                "capitalRequirement": r.get("capital_required"),
                "gasRequirement": r.get("gas_required"),
            }
        )

    report = {
        "engine": "Counter-Liquidity Discovery Engine",
        "version": "1.0.0",
        "at": _now(),
        "research_question": (
            "What legitimate mechanism could make an external asset available against VCORE "
            "without Virtus contributing its own capital?"
        ),
        "own_capital_eur": 0,
        "strict_mode": True,
        "vcore": vcore,
        "discovery": pack,
        "outcome": outcome,
        "counts": {
            "opportunities": n,
            "verified_sources": sum(1 for p in processed if (p.get("source") or p.get("sourceType"))),
            "zero_capital_filter_pass": sum(1 for p in processed if p.get("strict_pass")),
            "counter_liquidity_verified": n_zc,
            "executable": 0,  # never paint; need proof + owner
            "realized": 0,
            "hypotheses": n_hyp,
            "rejected": n_rej,
            "pending": n_pending,
            "counter_invariant": invariant,
            "accounting": {
                "TOTAL": n,
                "REJECTED": n_rej,
                "HYPOTHESES": n_hyp,
                "COUNTER_LIQ_VERIFIED": n_zc,
                "PENDING": n_pending,
                "sum": accounted,
            },
        },
        "opportunities": processed,
        "hypotheses": hypotheses,
        "rejected": rejected,
        "counter_liquidity_verified": zero_capital,
        "lessons": lessons[:40],
        "security_policy_immutable": list(SECURITY_POLICY_IMMUTABLE),
        "broadcast": "OWNER_GATED",
        "auto_broadcast": False,
        "message": (
            f"Исход: {outcome}. Counter-liquidity verified={n_zc}. "
            + (
                "Гипотезы есть, доказанной встречной ликвидности нет — RESEARCH. NO по verified path."
                if outcome == "RESEARCH_REQUIRED"
                else (
                    "NO — валидный научный результат: permissionless €0 path не найден среди исследованных механизмов."
                    if outcome == "NO_CAPITAL_PATH_FOUND"
                    else "Есть verified counter-liquidity — требуется evidence + simulation + owner gate."
                )
            )
        ),
        "next_test": (
            "P0: Faucet → Genesis PASS → VCORE on-chain verify → re-run liquidity:discover "
            "(DEX listing check). Parallel: dig concrete PERMISSIONLESS_COMPUTE protocol docs."
        ),
        "real_external_assets": 0,
        "law": [
            "OWN_CAPITAL=€0",
            "IMPLIED ≠ EXECUTABLE",
            "No fake liquidity / MODEL as reserve",
            "Grant/application class REJECT under strict mode",
            "NO is valid",
        ],
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _REPORT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    with _EXP.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"at": _now(), "outcome": outcome, "lessons": lessons[:10]}, ensure_ascii=False) + "\n")
    return report


def verify_sources() -> dict[str, Any]:
    r = discover()
    verified = []
    for o in r.get("opportunities") or []:
        src = o.get("source") or o.get("sourceType")
        ev = o.get("evidence")
        ok = bool(src) and bool(ev) and str(ev).lower() not in ("", "unknown")
        verified.append(
            {
                "opportunityId": o.get("opportunityId"),
                "source_verified": ok,
                "source": src,
                "evidence": ev,
                "status": "SOURCE_VERIFIED" if ok else "NO_SOURCE",
            }
        )
    return {"at": _now(), "items": verified, "counts": r.get("counts")}


def routes_report() -> dict[str, Any]:
    vcore = genesis_vcore_status()
    # Reuse Route Finder if present
    routes_path = _ROOT / ".runtime" / "vcore_routes_last.json"
    routes = None
    if routes_path.exists():
        try:
            routes = json.loads(routes_path.read_text(encoding="utf-8"))
        except Exception:
            routes = None
    return {
        "at": _now(),
        "vcore": vcore,
        "route_finder": routes,
        "note": "Without jettonMaster / pool → NO_ROUTE. Exit ≠ source of liquidity.",
        "status": "NO_ROUTE" if not vcore.get("jettonMaster") else "CHECK_DEX",
    }


def simulate_all() -> dict[str, Any]:
    r = discover()
    sims = []
    for o in r.get("opportunities") or []:
        sims.append({"id": o.get("opportunityId"), "simulation": o.get("simulation"), "proof": o.get("counter_liquidity_proof")})
    return {"at": _now(), "simulations": sims, "outcome": r.get("outcome")}
