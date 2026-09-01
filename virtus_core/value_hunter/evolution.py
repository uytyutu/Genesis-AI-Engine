"""
Value Hunter Evolution Engine v1

1-hour epochs · genome inheritance · experience ledger.
Mutates research strategy only — NEVER security policy.
SUCCESS = REAL_ASSET_RECEIVED + BLOCKCHAIN_CONFIRMATION + DESTINATION_BALANCE_INCREASE
"""

from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from virtus_core.value_hunter.pipeline import process_pipeline
from virtus_core.value_hunter.states import SECURITY_POLICY_IMMUTABLE

_ROOT = Path(__file__).resolve().parents[2]
_RUNTIME = _ROOT / ".runtime" / "evolution"
_AGENTS = _RUNTIME / "agents.json"
_EXPERIENCE = _RUNTIME / "experience_ledger.jsonl"
_EPOCH_SECONDS = 3600


def _now_ts() -> float:
    return time.time()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _load_agents() -> dict[str, Any]:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    if not _AGENTS.exists():
        return {"agents": [], "active_id": None}
    return json.loads(_AGENTS.read_text(encoding="utf-8"))


def _save_agents(data: dict[str, Any]) -> None:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    _AGENTS.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _append_experience(row: dict[str, Any]) -> None:
    _RUNTIME.mkdir(parents=True, exist_ok=True)
    with _EXPERIENCE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def default_genome(*, parent: dict[str, Any] | None = None) -> dict[str, Any]:
    base = {
        "network_preference": ["ton_testnet", "evm_public", "btc_exit"],
        "asset_preference": ["TON", "USDT", "USDC", "ETH", "BTC"],
        # Compute-first — Virtus already measures CPU work; prefer reward for that work.
        "protocol_category_order": [
            "COMPUTE_REWARD",
            "TESTNET_REWARD",
            "SPONSORED_EXECUTION",
            "PERMISSIONLESS_PROTOCOL",
            "BUG_BOUNTY",
            "CLAIM",
            "INCENTIVE",
        ],
        "discovery_order": ["compute", "faucet", "sponsored", "bounty", "claim", "incentive", "exit"],
        "route_depth": 2,
        "reward_type_focus": ["COMPUTE_REWARD", "TESTNET_REWARD", "SPONSORED_EXECUTION"],
        "execution_strategy": "owner_gated_dry_run",
        "capital_limit_eur": 0.0,
        "risk_policy": "strict_zero_capital",
    }
    if not parent:
        return base
    g = dict(parent.get("genome") or base)
    # Mutation: rotate discovery order, bump route depth within safe bounds
    order = list(g.get("discovery_order") or base["discovery_order"])
    if order:
        order = order[1:] + order[:1]
    g["discovery_order"] = order
    g["route_depth"] = min(5, int(g.get("route_depth") or 2) + 1)
    focus = list(g.get("reward_type_focus") or [])
    # Prefer sponsored/compute after repeated capital failures
    lessons = parent.get("rejected_reasons") or {}
    if lessons.get("CAPITAL_REQUIRED", 0) >= 1 and "SPONSORED_EXECUTION" not in focus:
        focus = ["SPONSORED_EXECUTION"] + focus
    if lessons.get("GAS_REQUIRED", 0) >= 1 and "SPONSORED_EXECUTION" not in focus:
        focus = ["SPONSORED_EXECUTION"] + [x for x in focus if x != "SPONSORED_EXECUTION"]
    if lessons.get("NO_VALID_OPPORTUNITY", 0) >= 1:
        focus = ["COMPUTE_REWARD", "PERMISSIONLESS_PROTOCOL", "SPONSORED_EXECUTION"] + [
            x for x in focus if x not in ("COMPUTE_REWARD", "PERMISSIONLESS_PROTOCOL", "SPONSORED_EXECUTION")
        ]
        g["protocol_category_order"] = list(base["protocol_category_order"])
    g["reward_type_focus"] = focus[:6]
    g["capital_limit_eur"] = 0.0  # never mutate capital limit upward
    g["risk_policy"] = "strict_zero_capital"
    return g


def spawn_agent(*, parent_id: str | None = None, lessons: list[str] | None = None) -> dict[str, Any]:
    from virtus_core.value_hunter.success_memory import list_successes

    data = _load_agents()
    parent = None
    if parent_id:
        parent = next((a for a in data["agents"] if a["agent_id"] == parent_id), None)
    success_mem = list_successes(20)
    success_lessons = [
        f"SUCCESS: {s.get('protocol')} → {s.get('reward')} {s.get('asset')} tx={s.get('tx_hash')} capital=€0"
        for s in success_mem
    ]
    agent = {
        "agent_id": f"VH-{uuid.uuid4().hex[:8].upper()}",
        "parent_id": parent_id,
        "epoch": int((parent or {}).get("epoch") or 0) + 1,
        "started_at": _now(),
        "started_ts": _now_ts(),
        "expires_at_ts": _now_ts() + _EPOCH_SECONDS,
        "duration_sec": _EPOCH_SECONDS,
        "status": "ACTIVE",
        "strategies_tried": [],
        "sources_checked": 0,
        "verified": 0,
        "executable": 0,
        "executable_now": 0,
        "realized_eur": 0.0,
        "rejected_reasons": dict((parent or {}).get("rejected_reasons") or {}),
        "successful_patterns": list((parent or {}).get("successful_patterns") or [])
        + [s.get("tx_hash") for s in success_mem if s.get("tx_hash")],
        "experience": list(lessons or [])
        + success_lessons
        + list((parent or {}).get("experience") or [])[:40],
        "success_memory": success_mem,
        "capital_limit": 0.0,
        "risk_policy": "strict_zero_capital",
        "security_policy_immutable": list(SECURITY_POLICY_IMMUTABLE),
        "genome": default_genome(parent=parent),
        "realized_assets": [],
    }
    data["agents"].append(agent)
    data["active_id"] = agent["agent_id"]
    _save_agents(data)
    _append_experience(
        {
            "type": "AGENT_SPAWNED",
            "at": _now(),
            "agent_id": agent["agent_id"],
            "parent_id": parent_id,
            "epoch": agent["epoch"],
            "experience_seed": agent["experience"][:5],
        }
    )
    return agent


def archive_agent(agent_id: str, *, reason: str = "EXPIRED") -> dict[str, Any]:
    data = _load_agents()
    agent = next((a for a in data["agents"] if a["agent_id"] == agent_id), None)
    if not agent:
        return {"ok": False, "reason": "not_found"}
    agent["status"] = reason
    agent["archived_at"] = _now()
    lessons = []
    rr = agent.get("rejected_reasons") or {}
    for k, v in rr.items():
        lessons.append(f"{k} ×{v}")
    if agent.get("executable", 0) == 0:
        lessons.append("Executable: 0 — смена reward classes / networks")
    if float(agent.get("realized_eur") or 0) <= 0:
        lessons.append("REALIZED=0 — не повторять доказанные тупики без новой evidence")
    if rr.get("NO_VALID_OPPORTUNITY"):
        lessons.append(
            "NO_VALID_OPPORTUNITY — честный научный негатив; углубить COMPUTE→REWARD, "
            "не форсировать гипотезу и не красить vectors/s как доход"
        )
    agent["lessons_out"] = lessons
    _save_agents(data)
    _append_experience(
        {
            "type": "AGENT_ARCHIVED",
            "at": _now(),
            "agent_id": agent_id,
            "reason": reason,
            "stats": {
                "sources_checked": agent.get("sources_checked"),
                "verified": agent.get("verified"),
                "executable": agent.get("executable"),
                "realized_eur": agent.get("realized_eur"),
            },
            "lessons": lessons,
        }
    )
    return {"ok": True, "agent": agent, "lessons": lessons}


def record_success(agent_id: str, asset: dict[str, Any]) -> dict[str, Any]:
    """Only REAL confirmed external asset counts as success → SUCCESS MEMORY + Treasury handoff."""
    from virtus_core.value_hunter.success_memory import append_success

    required = ("asset", "amount", "tx", "confirmations", "capital_used_eur")
    missing = [k for k in required if k not in asset]
    if missing:
        return {"ok": False, "reason": f"missing={missing}", "success": False}
    if float(asset.get("capital_used_eur") or 0) > 0:
        return {"ok": False, "reason": "capital_used_not_zero", "success": False}
    if str(asset.get("confirmations") or "").lower() not in ("verified", "confirmed"):
        return {"ok": False, "reason": "not_verified_on_chain", "success": False}

    mem = append_success(
        {
            "source": asset.get("source") or asset.get("source_of_funds") or "",
            "protocol": asset.get("protocol") or "",
            "action": asset.get("action") or "",
            "asset": asset["asset"],
            "capital": float(asset.get("capital_used_eur") or 0),
            "gas": float(asset.get("gas") or 0),
            "reward": asset["amount"],
            "tx_hash": asset["tx"],
            "confirmation": asset["confirmations"],
            "net_result": asset.get("net_result") or asset["amount"],
            "agent_id": agent_id,
        }
    )
    if not mem.get("ok"):
        return {"ok": False, "reason": mem.get("reason"), "success": False, "success_memory": mem}

    data = _load_agents()
    agent = next((a for a in data["agents"] if a["agent_id"] == agent_id), None)
    if not agent:
        return {"ok": False, "reason": "agent_not_found"}
    agent["realized_assets"].append(asset)
    agent["successful_patterns"].append(
        f"{asset['asset']} amount={asset['amount']} capital=€0 tx={asset['tx']}"
    )
    agent["status"] = "SUCCESS_HANDOFF_TREASURY"
    _save_agents(data)
    _append_experience(
        {
            "type": "SUCCESS",
            "at": _now(),
            "agent_id": agent_id,
            "asset": asset,
            "metric": "REAL_ASSET_RECEIVED",
            "success_memory": mem.get("entry"),
        }
    )
    return {"ok": True, "success": True, "handoff": "TREASURY", "agent": agent, "success_memory": mem}


def run_epoch_tick(*, force_new: bool = False) -> dict[str, Any]:
    """Run one hunt cycle under active agent; expire → spawn child with lessons.

    Honest science: epoch may end with NO_VALID_OPPORTUNITY — that is not agent failure.
    """
    from virtus_core.opportunity_ai.systematic import systematic_discover

    data = _load_agents()
    active = None
    if data.get("active_id") and not force_new:
        active = next((a for a in data["agents"] if a["agent_id"] == data["active_id"]), None)
        if active and active.get("status") not in ("ACTIVE", "NO_VALID_OPPORTUNITY"):
            if active.get("status") != "ACTIVE":
                active = None
        if active and active.get("status") == "NO_VALID_OPPORTUNITY":
            # Allow continuing research under same agent until expiry
            if _now_ts() <= float(active.get("expires_at_ts") or 0):
                active["status"] = "ACTIVE"
            else:
                active = None
        if active and _now_ts() > float(active.get("expires_at_ts") or 0):
            arch = archive_agent(active["agent_id"], reason="EXPIRED")
            active = spawn_agent(parent_id=active["agent_id"], lessons=arch.get("lessons") or [])
    if not active:
        active = spawn_agent()

    hunt = process_pipeline(max_capital_eur=float(active.get("capital_limit") or 0))
    # Reuse VH result; skip nested bip39 bench (capability ≠ income on this tick).
    systematic = systematic_discover(offline=False, reuse_vh=hunt, measure_compute=False)

    active["sources_checked"] = int(active.get("sources_checked") or 0) + int(
        hunt.get("counts", {}).get("sources_found") or 0
    )
    active["verified"] = int(hunt.get("counts", {}).get("verified") or 0)
    active["executable"] = int(hunt.get("counts", {}).get("candidates_for_test") or 0)
    active["executable_now"] = int(hunt.get("counts", {}).get("executable_now") or 0)
    active["strategies_tried"] = list(
        dict.fromkeys(
            list(active.get("strategies_tried") or [])
            + list((active.get("genome") or {}).get("reward_type_focus") or [])
            + ["SYSTEMATIC_ECONOMIC_DISCOVERY", "COMPUTE_REWARD_FIRST"]
        )
    )
    # Aggregate reject reasons
    rr = dict(active.get("rejected_reasons") or {})
    for o in hunt.get("rejected") or []:
        st = str(o.get("status") or "REJECTED")
        rr[st] = int(rr.get(st) or 0) + 1
    if systematic.get("epoch_status") == "NO_VALID_OPPORTUNITY":
        rr["NO_VALID_OPPORTUNITY"] = int(rr.get("NO_VALID_OPPORTUNITY") or 0) + 1
    active["rejected_reasons"] = rr

    # Experience bullets from this tick
    exp = list(active.get("experience") or [])
    if rr.get("CAPITAL_REQUIRED"):
        exp.append("DEX/LP без своего капитала → бесполезно при MAX_CAPITAL=0")
    if rr.get("NO_SOURCE_OF_FUNDS"):
        exp.append("Без sourceOfFunds → REJECTED")
    if rr.get("GAS_REQUIRED"):
        exp.append("Gas без sponsor → не zero-capital")
    if any(o.get("kind") == "FORBIDDEN" for o in hunt.get("opportunities") or []):
        exp.append("Foreign wallet / exploit → SECURITY_REJECTED навсегда")
    if systematic.get("epoch_status") == "NO_VALID_OPPORTUNITY":
        exp.append(
            "NO_VALID_OPPORTUNITY — честный конец эпохи; не искать подтверждение гипотезы силой. "
            "vectors/s = capability ≠ income. Priority: COMPUTE→REWARD."
        )
        active["status"] = "NO_VALID_OPPORTUNITY"
    elif systematic.get("epoch_status") == "CANDIDATE_FOUND":
        exp.append("CANDIDATE_REAL_BRICK — verify + simulate + owner gate (no auto broadcast)")
        active["status"] = "ACTIVE"
    active["experience"] = list(dict.fromkeys(exp))[-50:]
    active["last_systematic"] = {
        "epoch_status": systematic.get("epoch_status"),
        "scientific_result": systematic.get("scientific_result"),
        "working_bricks": systematic.get("counts", {}).get("working_brick_candidates"),
        "compute_vps": (systematic.get("compute_capability") or {}).get("vectors_per_sec"),
    }

    data = _load_agents()
    for i, a in enumerate(data["agents"]):
        if a["agent_id"] == active["agent_id"]:
            data["agents"][i] = active
            break
    data["active_id"] = active["agent_id"]
    _save_agents(data)

    remaining = max(0, int(float(active["expires_at_ts"]) - _now_ts()))
    return {
        "engine": "Value Hunter Evolution Engine",
        "version": "1.1.0",
        "at": _now(),
        "agent": {
            "agent_id": active["agent_id"],
            "parent_id": active.get("parent_id"),
            "epoch": active["epoch"],
            "status": active["status"],
            "remaining_sec": remaining,
            "sources_checked": active["sources_checked"],
            "verified": active["verified"],
            "executable": active["executable"],
            "executable_now": active.get("executable_now") or 0,
            "realized_eur": active["realized_eur"],
            "capital_limit": float(active.get("capital_limit") or 0),
            "genome": active["genome"],
            "experience": active["experience"][:12],
            "success_memory": active.get("success_memory") or [],
            "rejected_reasons": active["rejected_reasons"],
            "security_policy_immutable": active["security_policy_immutable"],
            "last_systematic": active.get("last_systematic"),
        },
        "hunt": {
            "counts": hunt.get("counts"),
            "message": hunt.get("message"),
            "mission": hunt.get("mission"),
            "genesis": hunt.get("genesis"),
            "counter_invariant": hunt.get("counter_invariant"),
            "viable_zero_capital": hunt.get("viable_zero_capital"),
            "queue_ids": [q.get("id") for q in (hunt.get("queue") or [])],
            "rejected_sample": [
                {"id": r.get("id"), "status": r.get("status"), "reason": r.get("reject_reason")}
                for r in (hunt.get("rejected") or [])[:12]
            ],
        },
        "systematic": {
            "epoch_status": systematic.get("epoch_status"),
            "scientific_result": systematic.get("scientific_result"),
            "message": systematic.get("message"),
            "counts": systematic.get("counts"),
            "priority_order": systematic.get("priority_order"),
            "top_compute_first": systematic.get("top_compute_first"),
            "compute_capability": systematic.get("compute_capability"),
        },
        "mission_vh1": hunt.get("mission"),
        "success_definition": {
            "required": [
                "REAL_ASSET_RECEIVED",
                "BLOCKCHAIN_CONFIRMATION",
                "DESTINATION_BALANCE_INCREASE",
            ],
            "not_success": ["MODEL_VALUE", "VCORE_SUPPLY", "UI_BALANCE", "DECLARED_PRICE", "VECTORS_PER_SEC"],
            "kpi": "REAL_EXTERNAL_ASSETS",
            "honest_negative": "NO_VALID_OPPORTUNITY",
        },
    }


def status() -> dict[str, Any]:
    data = _load_agents()
    active = next((a for a in data["agents"] if a["agent_id"] == data.get("active_id")), None)
    return {
        "active": active,
        "agents_count": len(data.get("agents") or []),
        "experience_path": str(_EXPERIENCE),
    }
