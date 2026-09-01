"""Electricity + profitability — UNKNOWN electricity ⇒ no REAL profit claim."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ProfitEstimate:
    source_id: str
    gross_eur_day: float
    electricity_eur_day: float | None
    fees_eur_day: float
    net_eur_day: float | None
    net_per_hour: float | None
    confidence: float
    electricity_status: str  # KNOWN | UNKNOWN
    note: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def electricity_cost_eur_day(power_watts: float, eur_per_kwh: float) -> float:
    kwh_day = (power_watts / 1000.0) * 24.0
    return round(kwh_day * eur_per_kwh, 4)


def estimate_profit(
    *,
    source_id: str,
    gross_eur_day: float,
    power_watts: float,
    electricity_eur_per_kwh: float,
    fees_eur_day: float = 0.0,
    confidence: float = 0.5,
) -> ProfitEstimate:
    elec = electricity_cost_eur_day(power_watts, electricity_eur_per_kwh)
    net = round(gross_eur_day - elec - fees_eur_day, 4)
    note = "NET negative → MUST NOT RUN" if net < 0 else "NET non-negative (still needs CONFIRMED payout for REAL)"
    return ProfitEstimate(
        source_id=source_id,
        gross_eur_day=round(gross_eur_day, 4),
        electricity_eur_day=elec,
        fees_eur_day=round(fees_eur_day, 4),
        net_eur_day=net,
        net_per_hour=round(net / 24.0, 6),
        confidence=confidence,
        electricity_status="KNOWN",
        note=note,
    )
