"""Stripe DE settlement — 3 business days hold before withdrawal."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DE_SETTLEMENT_BUSINESS_DAYS = 3

_STATUS_PENDING = "pending_settlement"
_STATUS_AVAILABLE = "available_for_withdrawal"
_STATUS_WITHDRAWN = "withdrawn"
_STATUS_PAID = "paid_by_client"


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def add_business_days(start: datetime, days: int) -> datetime:
    """Add business days (Mon–Fri) — Germany settlement timing."""
    if days <= 0:
        return start
    current = start
    added = 0
    while added < days:
        current += timedelta(days=1)
        if current.weekday() < 5:
            added += 1
    return current


class PaymentSettlementService:
    """finance_settlements.jsonl — payout status per external payment."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._path = memory_dir / "finance_settlements.jsonl"

    def _load_rows(self) -> list[dict[str, Any]]:
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

    def _save_rows(self, rows: list[dict[str, Any]]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + ("\n" if rows else ""),
            encoding="utf-8",
        )

    def find_by_payment_id(self, payment_id: str) -> dict[str, Any] | None:
        for row in self._load_rows():
            if str(row.get("payment_id") or "") == payment_id:
                return row
        return None

    def record_payment(
        self,
        *,
        amount_eur: float,
        payment_id: str,
        provider: str,
        label: str,
        order_id: str | None = None,
        sender: str | None = None,
        immediate_available: bool = False,
    ) -> dict[str, Any]:
        """Record webhook-confirmed payment — DE: 3 business days until withdrawable."""
        existing = self.find_by_payment_id(payment_id)
        if existing:
            return existing

        amount = round(float(amount_eur), 2)
        now = datetime.now(timezone.utc)
        paid_at = now.isoformat()
        if immediate_available or provider == "sandbox":
            available_at = now.isoformat()
            status = _STATUS_AVAILABLE
        else:
            avail_dt = add_business_days(now, DE_SETTLEMENT_BUSINESS_DAYS)
            available_at = avail_dt.isoformat()
            status = _STATUS_AVAILABLE if now >= avail_dt else _STATUS_PENDING

        row = {
            "settlement_id": uuid.uuid4().hex[:12],
            "payment_id": payment_id,
            "order_id": order_id,
            "amount_eur": amount,
            "provider": provider,
            "label": label,
            "sender": sender or "",
            "paid_at": paid_at,
            "available_at": available_at,
            "settlement_status": status,
            "settlement_status_ru": self.status_label_ru(status, available_at),
            "business_days_hold": 0 if immediate_available else DE_SETTLEMENT_BUSINESS_DAYS,
        }
        rows = self._load_rows()
        rows.append(row)
        self._save_rows(rows)
        return row

    @staticmethod
    def status_label_ru(status: str, available_at: str = "") -> str:
        if status == _STATUS_PENDING:
            return f"Ожидает settlement ({DE_SETTLEMENT_BUSINESS_DAYS} раб. дня DE)"
        if status == _STATUS_AVAILABLE:
            return "Доступно к выводу"
        if status == _STATUS_WITHDRAWN:
            return "Выведено"
        return "Оплачено клиентом"

    def refresh_statuses(self) -> list[dict[str, Any]]:
        """Promote pending_settlement → available_for_withdrawal when date passed."""
        now = datetime.now(timezone.utc)
        rows = self._load_rows()
        changed = False
        for row in rows:
            if row.get("settlement_status") != _STATUS_PENDING:
                continue
            avail = _parse_dt(str(row.get("available_at") or ""))
            if avail and now >= avail:
                row["settlement_status"] = _STATUS_AVAILABLE
                row["settlement_status_ru"] = self.status_label_ru(_STATUS_AVAILABLE)
                changed = True
        if changed:
            self._save_rows(rows)
        return rows

    def totals(self) -> dict[str, float]:
        rows = self.refresh_statuses()
        paid_by_client = 0.0
        pending_settlement = 0.0
        available = 0.0
        withdrawn = 0.0
        for row in rows:
            amount = round(float(row.get("amount_eur") or 0), 2)
            if amount <= 0:
                continue
            status = str(row.get("settlement_status") or "")
            if status == _STATUS_WITHDRAWN:
                withdrawn += amount
            elif status == _STATUS_AVAILABLE:
                available += amount
                paid_by_client += amount
            elif status == _STATUS_PENDING:
                pending_settlement += amount
                paid_by_client += amount
        return {
            "paid_by_client_eur": round(paid_by_client + withdrawn, 2),
            "pending_settlement_eur": round(pending_settlement, 2),
            "available_for_withdrawal_eur": round(available, 2),
            "withdrawn_eur": round(withdrawn, 2),
        }

    def apply_to_snapshot(self, snap: dict[str, Any]) -> dict[str, Any]:
        t = self.totals()
        snap["paid_by_client_eur"] = t["paid_by_client_eur"]
        snap["pending_settlement_eur"] = t["pending_settlement_eur"]
        snap["available_for_withdrawal_eur"] = t["available_for_withdrawal_eur"]
        snap["pending_payouts_eur"] = t["pending_settlement_eur"]
        return snap

    def list_settlements(self, limit: int = 30) -> list[dict[str, Any]]:
        rows = self.refresh_statuses()
        rows.sort(key=lambda r: str(r.get("paid_at", "")), reverse=True)
        out: list[dict[str, Any]] = []
        for row in rows[:limit]:
            out.append(
                {
                    "settlement_id": row.get("settlement_id"),
                    "payment_id": row.get("payment_id"),
                    "amount_eur": float(row.get("amount_eur") or 0),
                    "provider": row.get("provider"),
                    "label": row.get("label"),
                    "paid_at": row.get("paid_at"),
                    "available_at": row.get("available_at"),
                    "settlement_status": row.get("settlement_status"),
                    "settlement_status_ru": row.get("settlement_status_ru")
                    or self.status_label_ru(
                        str(row.get("settlement_status") or ""),
                        str(row.get("available_at") or ""),
                    ),
                }
            )
        return out

    def allocate_withdrawal(self, amount_eur: float) -> list[str]:
        """Mark available settlements as withdrawn (FIFO). Returns settlement_ids."""
        amount = round(float(amount_eur), 2)
        if amount <= 0:
            return []
        rows = self.refresh_statuses()
        remaining = amount
        touched: list[str] = []
        for row in sorted(rows, key=lambda r: str(r.get("available_at") or "")):
            if remaining <= 0:
                break
            if row.get("settlement_status") != _STATUS_AVAILABLE:
                continue
            row_amount = round(float(row.get("amount_eur") or 0), 2)
            if row_amount <= 0:
                continue
            if row_amount <= remaining + 0.001:
                row["settlement_status"] = _STATUS_WITHDRAWN
                row["settlement_status_ru"] = self.status_label_ru(_STATUS_WITHDRAWN)
                row["withdrawn_at"] = datetime.now(timezone.utc).isoformat()
                touched.append(str(row.get("settlement_id") or ""))
                remaining = round(remaining - row_amount, 2)
        self._save_rows(rows)
        return touched

    def has_stripe_webhook_payment(self) -> bool:
        for row in self._load_rows():
            if str(row.get("provider") or "") == "stripe":
                return True
        return False
