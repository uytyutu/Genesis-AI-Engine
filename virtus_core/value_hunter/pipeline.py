"""
ZERO-CAPITAL SOURCE HUNTER v2.1 — pipeline core.

DISCOVER → DEDUPLICATE → CLASSIFY → CAPITAL FILTER → ELIGIBILITY
→ ECONOMIC PROOF → EXPECTED VALUE → SIMULATE → QUEUE → OWNER REVIEW
→ EXECUTE (gated) → VERIFY → REALITY LEDGER → EXIT → TREASURY

No auto mainnet broadcast. Owner gate required for execution.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from virtus_core.value_hunter.adapters import run_all_adapters
from virtus_core.value_hunter.filters import (
    MAX_CAPITAL_EUR,
    apply_capital_filter,
    economic_proof,
    expected_value,
)
from virtus_core.value_hunter.real_verify import verify_real_opportunity
from virtus_core.value_hunter.signer_boundary import assert_ai_has_no_keys
from virtus_core.value_hunter.states import SECURITY_POLICY_IMMUTABLE
from virtus_core.value_hunter.success_memory import list_successes, success_count

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime"
_QUEUE_PATH = _RUNTIME / "source_hunter_queue.json"
_LOG_PATH = _RUNTIME / "source_hunter_log.jsonl"
_GENESIS_STATE = _RUNTIME / "vcore_genesis_state.json"
_REALITY_LEDGER = _RUNTIME / "vcore_reality_ledger.json"


def genesis_gate() -> dict[str, Any]:
    """Read Genesis stage only — never mnemonic / .env.ton."""
    if not _GENESIS_STATE.exists():
        return {
            "genesis_pass": False,
            "stage": "NOT_STARTED",
            "allow_send": False,
            "reason": "no_genesis_state",
        }
    try:
        g = json.loads(_GENESIS_STATE.read_text(encoding="utf-8"))
    except Exception as e:
        return {"genesis_pass": False, "stage": "ERROR", "allow_send": False, "reason": str(e)}
    stage = str(g.get("stage") or "UNKNOWN")
    master = bool(g.get("jettonMaster"))
    # PASS only when verified on-chain identity exists (same honesty as UI)
    genesis_pass = stage == "VERIFIED" and master
    allow_send = genesis_pass and stage not in ("WAITING_FAUCET", "NOT_STARTED")
    return {
        "genesis_pass": genesis_pass,
        "stage": stage,
        "allow_send": allow_send,
        "jetton_master": bool(master),
        "reason": None if genesis_pass else f"stage={stage}",
    }


def reality_external_assets() -> dict[str, Any]:
    """H5 / VH-1 KPI — only ledger + success memory + reality proofs, never painted."""
    from virtus_core.value_hunter.reality_proof import proof_count

    sm = success_count()
    proofs = proof_count()
    ledger_n = 0
    ledger_sum: list[dict[str, Any]] = []
    if _REALITY_LEDGER.exists():
        try:
            data = json.loads(_REALITY_LEDGER.read_text(encoding="utf-8"))
            entries = data if isinstance(data, list) else data.get("entries") or data.get("settlements") or []
            for e in entries:
                if e.get("confirmationStatus") in ("CONFIRMED", "verified", "VERIFIED") and not e.get("ui_only"):
                    ledger_n += 1
                    ledger_sum.append(e)
        except Exception:
            pass
    total = max(ledger_n, sm, proofs)  # don't triple-count same event; prefer union-ish max for display
    # Prefer exact unique: ledger + proofs not already counted — for honesty use sum of distinct stores with note
    unique_total = ledger_n + sm + proofs
    # If both success_memory and proofs wrote same tx, UI could double — use max of proofs/sm + ledger for KPI floor honesty
    kpi = proofs if proofs else (sm if sm else ledger_n)
    return {
        "real_external_assets": kpi,
        "reality_ledger_entries": ledger_n,
        "success_memory_entries": sm,
        "reality_proof_entries": proofs,
        "h5_status": "PASS" if kpi > 0 else "RESEARCH",
        "h5_evidence": ledger_sum[:5] + list_successes(5),
        "note": "KPI counts Reality Proof Recorder first; never paints from MODEL.",
        "_debug_sum": unique_total,
    }


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _log(action: str, *, opportunity_id: str = "", result: str = "", reason: str = "") -> None:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    row = {
        "timestamp": _now(),
        "module": "SOURCE_HUNTER_v2.1",
        "opportunityId": opportunity_id,
        "action": action,
        "result": result,
        "reason": reason,
    }
    with _LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def opportunity_hash(opp: dict[str, Any]) -> str:
    key = "|".join(
        [
            str(opp.get("protocol") or ""),
            str(opp.get("source_of_funds_type") or opp.get("kind") or ""),
            str(opp.get("asset") or ""),
            str(opp.get("eligibility") or opp.get("condition") or ""),
            str(opp.get("required_action") or ""),
            str(opp.get("id") or ""),
        ]
    )
    return hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]


def deduplicate(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for raw in items:
        o = dict(raw)
        h = opportunity_hash(o)
        o["hash"] = h
        o["firstSeen"] = o.get("firstSeen") or _now()
        o["lastSeen"] = _now()
        o["expiresAt"] = o.get("expiresAt") or o.get("expiration") or "UNKNOWN"
        if h in seen:
            seen[h]["lastSeen"] = _now()
            seen[h]["dedup_hits"] = int(seen[h].get("dedup_hits") or 1) + 1
            continue
        o["dedup_hits"] = 1
        seen[h] = o
    return list(seen.values())


def classify(opp: dict[str, Any]) -> dict[str, Any]:
    o = dict(opp)
    kind = (o.get("kind") or "").upper()
    if kind == "EXIT_CONVERTER":
        o["category"] = "EXIT"
        o["status"] = "EXIT_ONLY"
    elif kind == "FORBIDDEN":
        o["category"] = "FORBIDDEN"
    elif kind in ("BUG_BOUNTY",):
        o["category"] = "BOUNTIES"
    elif kind in ("INCENTIVE", "LIQUIDITY_INCENTIVE"):
        o["category"] = "INCENTIVES"
    elif kind in ("CLAIM",):
        o["category"] = "CLAIMS"
    elif kind in ("SPONSORED_EXECUTION", "SPONSORED_GAS"):
        o["category"] = "SPONSORED"
    elif kind in ("TESTNET_REWARD", "FAUCET"):
        o["category"] = "REWARDS"
    elif kind in ("COMPUTE_REWARD",):
        o["category"] = "COMPUTE"
    else:
        o["category"] = "SOURCES"
    if o.get("status") in (None, ""):
        o["status"] = "DISCOVERED"
    return o


def simulate(opp: dict[str, Any]) -> dict[str, Any]:
    """Honest simulation — never invents settlement amounts."""
    status = opp.get("status")
    if status in (
        "SECURITY_REJECTED",
        "CAPITAL_REQUIRED",
        "GAS_REQUIRED",
        "KYC_REQUIRED",
        "NO_SOURCE_OF_FUNDS",
        "ECONOMIC_PROOF_FAILED",
        "EXIT_ONLY",
    ):
        return {
            "ok": False,
            "status": "SIMULATION_FAILED" if status != "EXIT_ONLY" else "EXIT_ONLY",
            "reason": f"precondition={status}",
            "expected_output": "UNKNOWN",
            "broadcast": False,
        }
    proof = economic_proof(opp)
    if not proof["ok"]:
        return {
            "ok": False,
            "status": "SIMULATION_FAILED",
            "reason": "economic_proof_incomplete",
            "proof": proof,
            "expected_output": "UNKNOWN",
            "broadcast": False,
        }
    # Gas without sponsor already filtered; remaining testable items get dry-run PASS
    return {
        "ok": True,
        "status": "SIMULATION_PASS",
        "reason": "dry_run_only_no_broadcast",
        "expected_output": expected_value(opp).get("expected_net"),
        "broadcast": False,
        "note": "Симуляция не создаёт REAL. Broadcast запрещён без owner gate.",
    }


def kill_switch_check(opp: dict[str, Any], *, owner_approved: bool = False) -> dict[str, Any]:
    reasons: list[str] = []
    if not opp.get("source_of_funds_type"):
        reasons.append("unknown_source")
    dest = (opp.get("withdrawal_path") or "").upper()
    if not dest or dest == "UNKNOWN":
        reasons.append("unknown_destination")
    if opp.get("requires_foreign_wallet") or opp.get("forbidden"):
        reasons.append("security_policy")
    if opp.get("quote_stale"):
        reasons.append("stale_quote")
    if opp.get("expired") or opp.get("status") == "EXPIRED":
        reasons.append("expired_opportunity")
    if opp.get("chain_unexpected"):
        reasons.append("unexpected_chain")
    if opp.get("asset_unexpected"):
        reasons.append("unexpected_asset")
    if opp.get("simulation", {}).get("ok") is False:
        reasons.append("failed_simulation")
    if not owner_approved and opp.get("attempt_broadcast"):
        reasons.append("owner_gate")
    abort = len(reasons) > 0
    return {"abort": abort, "reasons": reasons, "action": "ABORT" if abort else "ALLOW"}


def reality_ledger_accept(event: dict[str, Any]) -> dict[str, Any]:
    """Only confirmed chain / external payout / verified balance increase."""
    required = ("network", "asset", "amount", "txHash", "source", "destination", "confirmationStatus")
    missing = [k for k in required if not event.get(k)]
    if missing:
        return {"accepted": False, "reason": f"missing={missing}", "real": False}
    if event.get("confirmationStatus") not in ("CONFIRMED", "verified", "VERIFIED"):
        return {"accepted": False, "reason": "not_confirmed", "real": False}
    if event.get("ui_only") or event.get("model_value") or event.get("simulated"):
        return {"accepted": False, "reason": "ui_or_model_not_real", "real": False}
    if event.get("forged") or event.get("fake_tx"):
        return {"accepted": False, "reason": "forged_tx", "real": False}
    return {
        "accepted": True,
        "real": True,
        "entry": {
            "network": event["network"],
            "asset": event["asset"],
            "amount": event["amount"],
            "txHash": event["txHash"],
            "block": event.get("block"),
            "source": event["source"],
            "destination": event["destination"],
            "timestamp": event.get("timestamp") or _now(),
            "confirmationStatus": event["confirmationStatus"],
            "evidence": event.get("evidence"),
        },
    }


def process_pipeline(*, max_capital_eur: float = MAX_CAPITAL_EUR, offline: bool = False) -> dict[str, Any]:
    _log("HUNT_STARTED", result="BEGIN")
    if offline:
        adapter_pack = {"at": _now(), "adapters": [], "raw_items": [], "status": "DISCOVERY_OFFLINE"}
        raw: list[dict[str, Any]] = []
        _log("DISCOVERY_OFFLINE", result="WARN", reason="network_unavailable")
    else:
        adapter_pack = run_all_adapters()
        raw = list(adapter_pack.get("raw_items") or [])

    # Also merge legacy catalog fields for continuity
    try:
        from virtus_core.value_hunter.source_hunter import hunt as legacy_hunt

        legacy = legacy_hunt(max_capital_eur=max_capital_eur)
        for s in legacy.get("sources") or []:
            raw.append(
                {
                    "id": s.get("id"),
                    "title": s.get("title"),
                    "kind": s.get("kind"),
                    "asset": s.get("asset"),
                    "protocol": s.get("kind"),
                    "eligibility": s.get("eligibility"),
                    "required_action": "see_eligibility",
                    "reward_rule": s.get("expected_value_hint") or "UNKNOWN",
                    "withdrawal_path": "owner_wallet_if_eligible",
                    "capital_required_eur": s.get("capital_required_eur") or 0,
                    "gas_required_eur": s.get("gas_required_eur") or 0,
                    "gas_sponsored": float(s.get("gas_required_eur") or 0) <= 0,
                    "fees_required_eur": 0.0,
                    "registration_required": bool(s.get("account_required")),
                    "account_required": bool(s.get("account_required")),
                    "kyc_required": bool(s.get("kyc_required")),
                    "source_of_funds_type": s.get("kind") if s.get("kind") != "FORBIDDEN" else "",
                    "source_of_funds_description": s.get("notes") or s.get("title"),
                    "source_of_funds_evidence": s.get("url") or "",
                    "url": s.get("url") or "",
                    "automatable": s.get("automatable"),
                    "risk": s.get("risk"),
                    "probability": None,
                    "expected_gross": None,
                    "status": "DISCOVERED",
                    "forbidden": s.get("kind") == "FORBIDDEN",
                    "requires_foreign_wallet": s.get("kind") == "FORBIDDEN",
                    "notes": s.get("notes"),
                }
            )
    except Exception as e:
        _log("LEGACY_CATALOG", result="WARN", reason=str(e))

    deduped = deduplicate(raw)
    processed: list[dict[str, Any]] = []
    for item in deduped:
        o = classify(item)
        if o.get("status") == "EXIT_ONLY":
            o["economic_proof"] = economic_proof(o)
            o["expected"] = expected_value(o)
            o["simulation"] = {"ok": False, "status": "EXIT_ONLY", "broadcast": False}
            o["real_verification"] = verify_real_opportunity(o)
            processed.append(o)
            _log("SOURCE_DISCOVERED", opportunity_id=str(o.get("id")), result="EXIT_ONLY")
            continue

        o = apply_capital_filter(o, max_capital_eur=max_capital_eur)
        if o.get("status") in (
            "CAPITAL_REQUIRED",
            "GAS_REQUIRED",
            "KYC_REQUIRED",
            "REGISTRATION_REQUIRED",
            "NO_SOURCE_OF_FUNDS",
            "SECURITY_REJECTED",
        ):
            _log(
                "SOURCE_REJECTED",
                opportunity_id=str(o.get("id")),
                result=str(o.get("status")),
                reason=str(o.get("reject_reason") or ""),
            )
            o["economic_proof"] = economic_proof(o)
            o["expected"] = expected_value(o)
            o["simulation"] = simulate(o)
            o["real_verification"] = verify_real_opportunity(o)
            processed.append(o)
            continue

        proof = economic_proof(o)
        o["economic_proof"] = proof
        if not proof["ok"]:
            o["status"] = "ECONOMIC_PROOF_FAILED"
            _log("ECONOMIC_PROOF_FAILED", opportunity_id=str(o.get("id")), result="FAIL")
            o["expected"] = expected_value(o)
            o["simulation"] = simulate(o)
            o["real_verification"] = verify_real_opportunity(o)
            processed.append(o)
            continue

        o["expected"] = expected_value(o)
        sim = simulate(o)
        o["simulation"] = sim
        rv = verify_real_opportunity(o)
        o["real_verification"] = rv
        if not sim.get("ok"):
            o["status"] = "SIMULATION_FAILED"
            _log("SIMULATION_FAILED", opportunity_id=str(o.get("id")), result="FAIL")
        else:
            # Candidate for testing — NOT the same as EXECUTABLE_NOW
            o["status"] = "QUEUED"
            o["owner_gate"] = "OWNER_REQUIRED"
            o["label"] = "CANDIDATE_FOR_TEST"
            if rv.get("status") != "VERIFIED":
                o["real_status"] = "NOT VERIFIED"
                _log(
                    "NOT_VERIFIED",
                    opportunity_id=str(o.get("id")),
                    result="NOT VERIFIED",
                    reason=str(rv.get("reason") or ""),
                )
            else:
                o["real_status"] = "VERIFIED"
            _log("SIMULATION_PASS", opportunity_id=str(o.get("id")), result="CANDIDATE")
            _log("OWNER_REQUIRED", opportunity_id=str(o.get("id")), result="QUEUED")
        processed.append(o)

    gate = genesis_gate()
    kpi = reality_external_assets()
    signer = assert_ai_has_no_keys()

    REJECT_STATUSES = frozenset(
        {
            "CAPITAL_REQUIRED",
            "GAS_REQUIRED",
            "KYC_REQUIRED",
            "REGISTRATION_REQUIRED",
            "APPLICATION_REQUIRED",
            "ACCOUNT_REQUIRED",
            "NO_SOURCE_OF_FUNDS",
            "SECURITY_REJECTED",
            "ECONOMIC_PROOF_FAILED",
            "SIMULATION_FAILED",
            "UNSUPPORTED",
            "EXPIRED",
            "NO_ROUTE",
            "INSUFFICIENT_LIQUIDITY",
        }
    )
    n_discovered = len(processed)
    n_rejected = sum(1 for x in processed if x.get("status") in REJECT_STATUSES)
    n_exit = sum(1 for x in processed if x.get("status") == "EXIT_ONLY")
    n_candidates = sum(1 for x in processed if x.get("status") == "QUEUED")
    n_expired = sum(1 for x in processed if x.get("status") == "EXPIRED")
    n_pending = n_discovered - n_rejected - n_exit - n_candidates - n_expired
    if n_pending < 0:
        n_pending = 0
    n_real_verified = sum(
        1 for x in processed if (x.get("real_verification") or {}).get("status") == "VERIFIED"
    )
    # EXECUTABLE_NOW: real-verified candidate + genesis allow — still owner-gated broadcast
    executable_ids = []
    for x in processed:
        if (
            x.get("status") == "QUEUED"
            and (x.get("real_verification") or {}).get("status") == "VERIFIED"
            and gate.get("genesis_pass")
            and gate.get("allow_send")
        ):
            executable_ids.append(x.get("id"))
    n_executable_now = len(executable_ids)

    accounted = n_rejected + n_exit + n_candidates + n_expired + n_pending
    counter_invariant = "PASS" if accounted == n_discovered else "FAIL"

    counts = {
        "sources_found": n_discovered,
        "discovered": n_discovered,
        "verified": n_real_verified,  # REAL Opportunity Verification (9 questions)
        "economic_proof_ok": sum(1 for x in processed if x.get("economic_proof", {}).get("ok")),
        "zero_capital": sum(
            1
            for x in processed
            if float(x.get("capital_required_eur") or 0) <= max_capital_eur
            and x.get("status") not in ("CAPITAL_REQUIRED", "SECURITY_REJECTED")
        ),
        "candidates_for_test": n_candidates,
        "testable": n_candidates,  # legacy alias — UI must say «кандидаты»
        "queued": n_candidates,
        "rejected": n_rejected,
        "exit_only": n_exit,
        "pending": n_pending,
        "expired": n_expired,
        "executable_now": n_executable_now,
        "realized": kpi["real_external_assets"],
        "real_external_assets": kpi["real_external_assets"],
        "reality_proofs": kpi.get("reality_proof_entries") or 0,
        "counter_invariant": counter_invariant,
        "accounting": {
            "DISCOVERED": n_discovered,
            "REJECTED": n_rejected,
            "EXIT_ONLY": n_exit,
            "CANDIDATES": n_candidates,
            "PENDING": n_pending,
            "EXPIRED": n_expired,
            "sum_buckets": accounted,
            "formula": "DISCOVERED = REJECTED + EXIT_ONLY + CANDIDATES + PENDING + EXPIRED",
        },
    }

    by_category: dict[str, list[dict[str, Any]]] = {
        "SOURCES": [],
        "REWARDS": [],
        "INCENTIVES": [],
        "CLAIMS": [],
        "SPONSORED": [],
        "COMPUTE": [],
        "BOUNTIES": [],
        "EXIT": [],
        "FORBIDDEN": [],
    }
    for o in processed:
        cat = o.get("category") or "SOURCES"
        by_category.setdefault(cat, []).append(o)

    queue = [x for x in processed if x.get("status") == "QUEUED"]
    rejected = [
        x
        for x in processed
        if x.get("status")
        in (
            "CAPITAL_REQUIRED",
            "GAS_REQUIRED",
            "KYC_REQUIRED",
            "REGISTRATION_REQUIRED",
            "APPLICATION_REQUIRED",
            "ACCOUNT_REQUIRED",
            "NO_SOURCE_OF_FUNDS",
            "SECURITY_REJECTED",
            "ECONOMIC_PROOF_FAILED",
            "SIMULATION_FAILED",
            "UNSUPPORTED",
            "EXPIRED",
            "NO_ROUTE",
            "INSUFFICIENT_LIQUIDITY",
        )
    ]

    viable = n_candidates > 0
    if kpi["real_external_assets"] > 0:
        message = f"VH-1: REAL EXTERNAL ASSETS = {kpi['real_external_assets']}"
    elif n_executable_now > 0:
        message = f"EXECUTABLE_NOW={n_executable_now} — нужен OWNER APPROVE (без auto-broadcast)"
    elif n_candidates > 0 and not gate.get("genesis_pass"):
        message = (
            f"Кандидатов на тестирование: {n_candidates}, но EXECUTABLE_NOW=0 "
            f"(GENESIS PASS=false, stage={gate.get('stage')}). Исполнение закрыто."
        )
    elif n_candidates > 0:
        message = (
            f"Кандидатов: {n_candidates}. REAL VERIFIED={n_real_verified}. "
            f"EXECUTABLE_NOW=0 — нет полного REAL OPPORTUNITY VERIFICATION (HOW MUCH и др.)."
        )
    else:
        message = "NO VIABLE ZERO-CAPITAL OPPORTUNITY — продолжаем поиск"

    report = {
        "engine": "ZERO-CAPITAL SOURCE HUNTER",
        "version": "2.1.1",
        "at": _now(),
        "max_capital_eur": max_capital_eur,
        "mission": {
            "id": "VH-1",
            "title": "FIRST REAL EXTERNAL DIGITAL ASSET",
            "capital_eur": 0,
            "target": "amount > 0",
            "minimum": "> 0",
            "kpi": "REAL_EXTERNAL_ASSETS",
            "current": kpi["real_external_assets"],
            "h5": kpi["h5_status"],
            "requirements": [
                "real source",
                "real eligibility",
                "real action",
                "real transaction",
                "real confirmation",
                "real balance increase",
            ],
            "not_target": ["300 BTC promise", "MODEL $1M", "VCORE supply as money"],
        },
        "genesis": gate,
        "signer_boundary": signer,
        "discovery": adapter_pack if not offline else {"status": "DISCOVERY_OFFLINE"},
        "counts": counts,
        "counter_invariant": counter_invariant,
        "executable_now_ids": executable_ids,
        "opportunities": processed,
        "queue": queue,
        "rejected": rejected,
        "by_category": {k: v for k, v in by_category.items() if v},
        "security_policy_immutable": list(SECURITY_POLICY_IMMUTABLE),
        "broadcast": "OWNER_GATED",
        "auto_broadcast": False,
        "viable_zero_capital": viable,
        "message": message,
        "pipeline": [
            "DISCOVER",
            "DEDUPLICATE",
            "CLASSIFY",
            "CAPITAL_FILTER",
            "ELIGIBILITY",
            "ECONOMIC_PROOF",
            "EXPECTED_VALUE",
            "SIMULATE",
            "REAL_OPPORTUNITY_VERIFICATION",
            "QUEUE_AS_CANDIDATE",
            "OWNER_REVIEW",
            "EXECUTE_GATED",
            "VERIFY_ON_CHAIN",
            "REALITY_LEDGER",
            "SUCCESS_MEMORY",
            "EXIT",
            "TREASURY",
        ],
        "law": [
            "MAX_CAPITAL_EUR=0",
            "Gas считается отдельно",
            "sourceOfFunds обязателен",
            "VCORE ≠ REAL money",
            "Нет auto mainnet broadcast",
            "REAL только после подтверждения",
            "AI не читает mnemonic",
            "EXECUTABLE_NOW ≠ кандидаты в очереди",
        ],
    }

    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _QUEUE_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    _log("HUNT_COMPLETED", result="OK" if viable else "NO_VIABLE")
    return report


def verify_opportunity(opportunity_id: str) -> dict[str, Any]:
    if not _QUEUE_PATH.exists():
        report = process_pipeline()
    else:
        report = json.loads(_QUEUE_PATH.read_text(encoding="utf-8"))
    found = None
    for o in report.get("opportunities") or []:
        if o.get("id") == opportunity_id or o.get("hash") == opportunity_id:
            found = o
            break
    if not found:
        return {"ok": False, "status": "UNSUPPORTED", "reason": "opportunity_not_found"}
    proof = economic_proof(found)
    ks = kill_switch_check(found, owner_approved=False)
    found["economic_proof"] = proof
    found["kill_switch"] = ks
    if not proof["ok"]:
        found["status"] = "ECONOMIC_PROOF_FAILED"
    elif found.get("status") in ("DISCOVERED", "TESTABLE"):
        found["status"] = "VERIFIED"
    _log("VERIFY", opportunity_id=opportunity_id, result=found.get("status") or "")
    return {"ok": proof["ok"] and not ks["abort"], "opportunity": found}


def simulate_opportunity(opportunity_id: str) -> dict[str, Any]:
    v = verify_opportunity(opportunity_id)
    if not v.get("opportunity"):
        return v
    o = v["opportunity"]
    sim = simulate(o)
    o["simulation"] = sim
    if sim.get("ok"):
        o["status"] = "QUEUED"
        o["owner_gate"] = "OWNER_REQUIRED"
    else:
        o["status"] = sim.get("status") or "SIMULATION_FAILED"
    _log("SIMULATE", opportunity_id=opportunity_id, result=str(o.get("status")))
    return {"ok": bool(sim.get("ok")), "opportunity": o, "broadcast": False}
