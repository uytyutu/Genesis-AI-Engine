"""
SUCCESS MEMORY — only REAL confirmed external assets.

Used by Evolution Engine so child agents inherit concrete winning mechanisms,
not only failure lessons.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT = _ROOT / ".runtime" / "evolution" / "success_memory.jsonl"


def _path() -> Path:
    override = (os.environ.get("VIRTUS_SUCCESS_MEMORY_PATH") or "").strip()
    return Path(override) if override else _DEFAULT


REQUIRED = (
    "source",
    "protocol",
    "action",
    "asset",
    "capital",
    "gas",
    "reward",
    "tx_hash",
    "confirmation",
    "net_result",
)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_success(entry: dict[str, Any]) -> dict[str, Any]:
    missing = [k for k in REQUIRED if k not in entry or entry.get(k) in (None, "", "UNKNOWN")]
    if missing:
        return {"ok": False, "reason": f"missing={missing}", "stored": False}
    conf = str(entry.get("confirmation") or "").lower()
    if conf not in ("verified", "confirmed", "on_chain_confirmed"):
        return {"ok": False, "reason": "confirmation_not_on_chain", "stored": False}
    if float(entry.get("capital") or 0) > 0:
        return {"ok": False, "reason": "capital_must_be_zero_for_vh1", "stored": False}
    # Reject obvious test/fixture hashes from polluting VH-1 KPI
    tx = str(entry.get("tx_hash") or "")
    if tx in ("EQ..", "x", "fake", "test") or tx.startswith("EQ.."):
        return {"ok": False, "reason": "tx_hash_looks_fixture", "stored": False}
    row = {**entry, "at": _now(), "metric": "REAL_ASSET_RECEIVED"}
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return {"ok": True, "stored": True, "entry": row}


def list_successes(limit: int = 50) -> list[dict[str, Any]]:
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
        if not isinstance(obj, dict):
            continue
        # Ignore fixture pollution
        tx = str(obj.get("tx_hash") or "")
        if tx in ("EQ..", "x", "fake", "test") or tx.startswith("EQ.."):
            continue
        rows.append(obj)
    return rows[-limit:]


def success_count() -> int:
    return len(list_successes(10_000))
