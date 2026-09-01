"""Payout states — only CONFIRMED counts as REAL."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

PayoutState = Literal["EXPECTED", "PENDING", "CONFIRMED", "WITHDRAWABLE"]


@dataclass
class PayoutRecord:
    id: str
    source: str
    amount: float
    currency: str
    state: PayoutState
    external_id: str | None
    note: str
    at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TreasuryView:
    expected: float = 0.0
    pending: float = 0.0
    confirmed: float = 0.0
    withdrawable: float = 0.0
    currency: str = "EUR"
    records: list[PayoutRecord] = field(default_factory=list)
    rule: str = "REAL = CONFIRMED only · External Payout ID required"

    def to_dict(self) -> dict[str, Any]:
        return {
            "expected": self.expected,
            "pending": self.pending,
            "confirmed": self.confirmed,
            "withdrawable": self.withdrawable,
            "currency": self.currency,
            "records": [r.to_dict() for r in self.records],
            "rule": self.rule,
        }


def load_ledger(path: Path) -> TreasuryView:
    if not path.exists():
        return TreasuryView()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return TreasuryView()
    records = []
    for r in raw.get("records") or []:
        records.append(
            PayoutRecord(
                id=str(r.get("id")),
                source=str(r.get("source")),
                amount=float(r.get("amount") or 0),
                currency=str(r.get("currency") or "EUR"),
                state=r.get("state") or "EXPECTED",  # type: ignore
                external_id=r.get("external_id"),
                note=str(r.get("note") or ""),
                at=str(r.get("at") or ""),
            )
        )
    view = TreasuryView(currency=str(raw.get("currency") or "EUR"), records=records)
    for rec in records:
        # Only CONFIRMED with external_id counts toward REAL confirmed
        if rec.state == "EXPECTED":
            view.expected += rec.amount
        elif rec.state == "PENDING":
            view.pending += rec.amount
        elif rec.state == "CONFIRMED" and rec.external_id:
            view.confirmed += rec.amount
        elif rec.state == "WITHDRAWABLE" and rec.external_id:
            view.withdrawable += rec.amount
            view.confirmed += rec.amount
    return view


def save_empty_ledger(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"currency": "EUR", "records": [], "note": "No CONFIRMED payouts yet"}, indent=2),
        encoding="utf-8",
    )
