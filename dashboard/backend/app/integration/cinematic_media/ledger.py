"""Media Budget Ledger — AI spend tracking; never mutates Stripe actual revenue."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

LedgerOp = Literal["RESERVE", "CHARGE", "REFUND", "RELEASE"]


class MediaBudgetLedger:
    def __init__(self, memory_dir: Path) -> None:
        self._path = Path(memory_dir) / "media_budget_ledger.jsonl"

    def _load(self) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return rows

    def _append(self, row: dict[str, Any]) -> dict[str, Any]:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def record(
        self,
        *,
        order_id: str,
        op: LedgerOp,
        amount_eur: float,
        provider: str = "",
        job_id: str = "",
        capability: str = "",
        status: str = "recorded",
        meta: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = {
            "entry_id": uuid.uuid4().hex[:12],
            "order_id": str(order_id),
            "op": op,
            "provider": provider or "",
            "job_id": job_id or "",
            "capability": capability or "",
            "amount_eur": round(float(amount_eur), 4),
            "status": status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "meta": meta or {},
            "note": "media_spend_only — does not alter Stripe actual revenue",
        }
        return self._append(row)

    def entries_for_order(self, order_id: str) -> list[dict[str, Any]]:
        oid = str(order_id)
        return [r for r in self._load() if str(r.get("order_id") or "") == oid]

    def spent_eur(self, order_id: str) -> float:
        spent = 0.0
        for row in self.entries_for_order(order_id):
            op = str(row.get("op") or "")
            amt = float(row.get("amount_eur") or 0)
            if op in ("CHARGE", "RESERVE"):
                spent += amt
            elif op in ("REFUND", "RELEASE"):
                spent -= amt
        return round(max(0.0, spent), 4)
