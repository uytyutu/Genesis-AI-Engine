"""German-ready finance ledger skeleton — real confirmed income only by default.

Double-entry lite: each posting has uuid, source, amounts, confidence, refs.
Export: CSV. PDF later.
"""

from __future__ import annotations

import csv
import io
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.revenue_source import (
    CONFIDENCE_BOOKED,
    CONFIDENCE_CONFIRMED,
    CONFIDENCE_ESTIMATED,
    CONFIDENCE_PENDING,
    CONFIDENCE_SIMULATED,
    CONFIDENCE_WITHDRAWN,
    confidence_label,
    is_withdrawable_confidence,
)

LEDGER_FILENAME = "virtus_finance_ledger.jsonl"

REQUIRED_FIELDS = (
    "uuid",
    "booked_at",
    "source_id",
    "income_type",
    "description",
    "amount",
    "currency",
    "vat_rate",
    "vat_amount",
    "accrual_date",
    "settlement_date",
    "payout_id",
    "task_id",
    "invoice_id",
    "bank_reference",
    "confidence",
    "status",
    "proof_url",
)


class FinanceLedger:
    """Append-only journal. Estimates may be stored but flagged; export_real filters them."""

    def __init__(self, memory_dir: Path) -> None:
        self._path = memory_dir / LEDGER_FILENAME
        self._memory = memory_dir

    def append(
        self,
        *,
        source_id: str,
        amount: float,
        currency: str = "EUR",
        income_type: str = "revenue",
        description: str = "",
        confidence: str = CONFIDENCE_CONFIRMED,
        payout_id: str = "",
        task_id: str = "",
        invoice_id: str = "",
        bank_reference: str = "",
        vat_rate: float = 0.0,
        accrual_date: str | None = None,
        settlement_date: str | None = None,
        proof_url: str = "",
        status: str | None = None,
    ) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        amount_r = round(float(amount), 4)
        vat = round(amount_r * float(vat_rate or 0), 4)
        row = {
            "uuid": uuid.uuid4().hex,
            "booked_at": now,
            "source_id": source_id,
            "income_type": income_type,
            "description": description or f"{source_id} {confidence}",
            "amount": amount_r,
            "currency": currency,
            "vat_rate": float(vat_rate or 0),
            "vat_amount": vat,
            "accrual_date": accrual_date or now[:10],
            "settlement_date": settlement_date,
            "payout_id": payout_id or None,
            "task_id": task_id or None,
            "invoice_id": invoice_id or None,
            "bank_reference": bank_reference or None,
            "confidence": confidence,
            "confidence_label_ru": confidence_label(confidence),
            "status": status
            or (
                "available"
                if is_withdrawable_confidence(confidence)
                else confidence.lower()
            ),
            "proof_url": proof_url or None,
            "withdrawable": is_withdrawable_confidence(confidence),
        }
        if confidence in {CONFIDENCE_SIMULATED, CONFIDENCE_ESTIMATED} and not payout_id:
            # Allowed for audit trail — never marked withdrawable
            row["withdrawable"] = False
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return row

    def list_entries(self, *, limit: int = 200, real_only: bool = False) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if real_only and not row.get("withdrawable"):
                conf = row.get("confidence")
                if conf not in {
                    CONFIDENCE_CONFIRMED,
                    CONFIDENCE_WITHDRAWN,
                    CONFIDENCE_BOOKED,
                }:
                    continue
            rows.append(row)
        return list(reversed(rows[-limit:]))

    def export_csv(self, *, real_only: bool = True) -> str:
        from swarm.finance_reality_law import tax_export_allowed

        rows = self.list_entries(limit=10_000, real_only=bool(real_only))
        if real_only:
            rows = [
                r for r in rows if tax_export_allowed(str(r.get("confidence") or ""))
            ]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=list(REQUIRED_FIELDS), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k) for k in REQUIRED_FIELDS})
        return buf.getvalue()

    def summary(self) -> dict[str, Any]:
        from swarm.finance_reality_law import (
            TAX_ALLOWED_CONFIDENCE,
            financial_truth_manifest,
        )

        rows = self.list_entries(limit=10_000, real_only=False)
        by_conf: dict[str, float] = {}
        real_total = 0.0
        tax_total = 0.0
        sim_total = 0.0
        for row in rows:
            conf = str(row.get("confidence") or "").upper()
            amt = float(row.get("amount") or 0)
            by_conf[conf] = round(by_conf.get(conf, 0.0) + amt, 4)
            if row.get("withdrawable") or conf in TAX_ALLOWED_CONFIDENCE:
                real_total += amt
            if conf in TAX_ALLOWED_CONFIDENCE:
                tax_total += amt
            if conf in {"SIMULATED", "ESTIMATED"}:
                sim_total += amt
        tax_total = round(tax_total, 4)
        return {
            "entries": len(rows),
            "by_confidence_eur": by_conf,
            "real_withdrawable_eur": round(real_total, 4),
            "tax_report_confirmed_eur": tax_total,
            "simulation_estimate_eur": round(sim_total, 4),
            "money_layers": {
                "REAL": tax_total,
                "SIMULATION": round(sim_total, 4),
            },
            "path": str(self._path),
            "export": {"csv": True, "pdf": False, "tax_real_only": True},
            "financial_truth": financial_truth_manifest(),
            "note_ru": (
                "Подтверждённый доход (Ledger / налоги): "
                f"{tax_total:.2f} €. "
                "DATEV/EÜR/CSV для Steuerberater — только CONFIRMED|BOOKED|WITHDRAWN. "
                "Demo/Replay/Estimate в налоговый экспорт не попадают."
            ),
            "pending_states": [CONFIDENCE_PENDING, CONFIDENCE_ESTIMATED],
        }
