"""
Reality Proof Recorder — first real on-chain results become immutable evidence.

Not a new Hunter. Stores reconstructable proofs for Evolution SUCCESS MEMORY.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = _ROOT / ".runtime" / "reality_proofs.jsonl"


def _path() -> Path:
    override = (os.environ.get("VIRTUS_REALITY_PROOF_PATH") or "").strip()
    return Path(override) if override else _DEFAULT


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


REQUIRED = (
    "opportunity_id",
    "source",
    "protocol",
    "action",
    "asset",
    "amount",
    "capital_used",
    "gas_paid",
    "tx_hash",
    "destination",
    "balance_before",
    "balance_after",
    "net_result",
)

# Causality chain — balance delta alone is not enough
CAUSALITY = (
    "source",
    "tx_hash",
    "destination",
    "asset",
    "amount",
    "confirmation",
    "balance_before",
    "balance_after",
)


def record_reality_proof(entry: dict[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED if k not in entry]
    if missing:
        return {"ok": False, "stored": False, "reason": f"missing={missing}"}
    # Causality: source → transaction → recipient → asset → amount → confirmation → delta → timing
    conf = entry.get("confirmation") or entry.get("confirmationStatus")
    if not conf or str(conf).lower() not in ("confirmed", "verified", "on_chain_confirmed"):
        return {"ok": False, "stored": False, "reason": "confirmation_required_for_causality"}
    causal_missing = [k for k in CAUSALITY if entry.get(k) in (None, "", "UNKNOWN") and k != "confirmation"]
    if entry.get("confirmation") in (None, "", "UNKNOWN") and not conf:
        causal_missing.append("confirmation")
    # amount must match balance delta (within tiny float tol)
    try:
        before = float(entry["balance_before"])
        after = float(entry["balance_after"])
        amount = float(entry["amount"])
    except (TypeError, ValueError):
        return {"ok": False, "stored": False, "reason": "balance_or_amount_not_numeric"}
    if after <= before:
        return {"ok": False, "stored": False, "reason": "balance_did_not_increase"}
    delta = after - before
    if abs(delta - amount) > max(1e-9, abs(amount) * 1e-6):
        return {
            "ok": False,
            "stored": False,
            "reason": f"causality_amount_mismatch delta={delta} amount={amount}",
        }
    if not entry.get("source") or not entry.get("destination") or not entry.get("tx_hash"):
        return {"ok": False, "stored": False, "reason": "causality_source_tx_destination_required"}
    tx = str(entry.get("tx_hash") or "")
    if not tx or tx in ("EQ..", "x", "fake", "test") or tx.startswith("EQ.."):
        return {"ok": False, "stored": False, "reason": "tx_hash_invalid_or_fixture"}
    if float(entry.get("capital_used") or 0) > 0:
        return {"ok": False, "stored": False, "reason": "capital_used_must_be_0_for_vh1"}
    # timing optional but recommended
    timing = entry.get("timestamp") or entry.get("timing") or _now()
    row = {
        **{k: entry[k] for k in REQUIRED},
        "block": entry.get("block"),
        "timestamp": timing,
        "network": entry.get("network") or "UNKNOWN",
        "confirmation": conf,
        "metric": "REAL_EXTERNAL_ASSET",
        "causality": {
            "source": entry["source"],
            "transaction": tx,
            "recipient": entry["destination"],
            "asset": entry["asset"],
            "amount": amount,
            "confirmation": conf,
            "balance_delta": delta,
            "timing": timing,
            "ok": True,
        },
    }
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    # Also feed SUCCESS MEMORY when possible
    try:
        from virtus_core.value_hunter.success_memory import append_success

        append_success(
            {
                "source": row["source"],
                "protocol": row["protocol"],
                "action": row["action"],
                "asset": row["asset"],
                "capital": float(row["capital_used"]),
                "gas": float(row["gas_paid"]),
                "reward": row["amount"],
                "tx_hash": row["tx_hash"],
                "confirmation": "verified",
                "net_result": row["net_result"],
            }
        )
    except Exception:
        pass
    return {"ok": True, "stored": True, "entry": row}


def list_proofs(limit: int = 100) -> list[dict[str, Any]]:
    p = _path()
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            rows.append(obj)
    return rows[-limit:]


def proof_count() -> int:
    return len(list_proofs(10_000))
