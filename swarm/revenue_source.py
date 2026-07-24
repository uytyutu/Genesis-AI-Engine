"""Universal RevenueSource contract + money Confidence states.

Not forecast quality (see revenue_confidence.py) — this is accounting confidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

CONFIDENCE_SIMULATED = "SIMULATED"
CONFIDENCE_ESTIMATED = "ESTIMATED"
CONFIDENCE_PENDING = "PENDING"
CONFIDENCE_CONFIRMED = "CONFIRMED"
CONFIDENCE_WITHDRAWN = "WITHDRAWN"
CONFIDENCE_BOOKED = "BOOKED"

CONFIDENCE_RANK = {
    CONFIDENCE_SIMULATED: 0,
    CONFIDENCE_ESTIMATED: 1,
    CONFIDENCE_PENDING: 2,
    CONFIDENCE_CONFIRMED: 3,
    CONFIDENCE_WITHDRAWN: 4,
    CONFIDENCE_BOOKED: 5,
}

CONFIDENCE_LABEL_RU = {
    CONFIDENCE_SIMULATED: "Симуляция — не доход",
    CONFIDENCE_ESTIMATED: "Оценка — не подтверждено платформой",
    CONFIDENCE_PENDING: "Ожидает подтверждения API/webhook",
    CONFIDENCE_CONFIRMED: "Подтверждено API — начислено",
    CONFIDENCE_WITHDRAWN: "Выведено с платформы",
    CONFIDENCE_BOOKED: "Поступило на основной счёт / занесено в учёт",
}


@dataclass(frozen=True)
class RevenueSourceCapabilities:
    balance_supported: bool = False
    payout_history_supported: bool = False
    webhook_supported: bool = False
    auto_withdraw_supported: bool = False
    manual_proof_supported: bool = True
    fetch_tasks_supported: bool = False
    submit_results_supported: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RevenueSource:
    """Plug-in contract — new platforms without rewriting Finance Core."""

    id: str
    name: str
    currency: str = "EUR"
    role: str = "unknown"
    capabilities: RevenueSourceCapabilities = field(default_factory=RevenueSourceCapabilities)
    can_earn: bool = False
    withdraw_mode: str = "none"
    note_ru: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "currency": self.currency,
            "role": self.role,
            "capabilities": self.capabilities.as_dict(),
            "can_earn": self.can_earn,
            "withdraw_mode": self.withdraw_mode,
            "note_ru": self.note_ru,
        }


def confidence_label(state: str) -> str:
    return CONFIDENCE_LABEL_RU.get(state, state)


def is_withdrawable_confidence(state: str) -> bool:
    return CONFIDENCE_RANK.get(state, 0) >= CONFIDENCE_RANK[CONFIDENCE_CONFIRMED]


def sources_from_audit() -> list[RevenueSource]:
    from swarm.revenue_source_capabilities import audit_sources

    out: list[RevenueSource] = []
    for row in audit_sources():
        caps = RevenueSourceCapabilities(
            balance_supported=row.get("balance_api") == "yes",
            payout_history_supported=row.get("payout_history") == "yes",
            webhook_supported=row.get("webhook") == "yes",
            auto_withdraw_supported=row.get("auto_withdraw") in {"yes", "partial"},
            manual_proof_supported=row.get("manual_withdraw") in {"yes", "n/a"}
            or bool(row.get("can_earn_via_virtus")),
            fetch_tasks_supported=row.get("fetch_tasks") in {"yes", "partial"},
            submit_results_supported=row.get("submit_results") in {"yes", "partial"},
        )
        withdraw = "none"
        if row["id"] == "stripe":
            withdraw = "stripe_managed"
        elif row.get("manual_withdraw") == "yes":
            withdraw = "manual"
        elif row.get("auto_withdraw") == "yes":
            withdraw = "auto"
        out.append(
            RevenueSource(
                id=str(row["id"]),
                name=str(row["platform"]),
                role=str(row.get("role") or "unknown"),
                capabilities=caps,
                can_earn=bool(row.get("can_earn_via_virtus")),
                withdraw_mode=withdraw,
                note_ru=str(row.get("note_ru") or ""),
            )
        )
    return out


def catalog() -> dict[str, Any]:
    items = sources_from_audit()
    return {
        "confidence_states": [
            {"id": k, "rank": CONFIDENCE_RANK[k], "label_ru": CONFIDENCE_LABEL_RU[k]}
            for k in CONFIDENCE_RANK
        ],
        "sources": [s.as_dict() for s in items],
        "note_ru": (
            "RevenueSource — универсальный контракт. "
            "Confidence SIMULATED…BOOKED — бухгалтерский уровень доверия, не прогноз фермы."
        ),
    }
