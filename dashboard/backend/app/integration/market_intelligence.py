"""Market Intelligence — recommendations for Internal CEO (no auto price changes).

Flow:
  Market Registry → Market Intelligence → CEO Notification → Approve/Reject → Registry update
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from app.integration.market_registry import get_market
from app.integration.market_registry_schema import MarketPriceRange, project_type_label


class RecommendationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class MarketIntelligenceRecommendation:
    """Proposed registry change — never applied without owner approval."""

    recommendation_id: str
    market_code: str
    service_id: str
    project_type: str | None
    direction: str  # up | down | stable
    percent_change: float
    reasons: tuple[str, ...]
    previous_range: MarketPriceRange
    recommended_range: MarketPriceRange
    status: RecommendationStatus = RecommendationStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "market_code": self.market_code,
            "service_id": self.service_id,
            "project_type": self.project_type,
            "direction": self.direction,
            "percent_change": self.percent_change,
            "reasons": list(self.reasons),
            "previous_range": {
                "from": self.previous_range.from_amount,
                "to": self.previous_range.to_amount,
                "average": self.previous_range.average_market,
            },
            "recommended_range": {
                "from": self.recommended_range.from_amount,
                "to": self.recommended_range.to_amount,
                "average": self.recommended_range.average_market,
            },
            "status": self.status.value,
            "created_at": self.created_at,
        }


_PENDING: list[MarketIntelligenceRecommendation] = []


def propose_recommendation(
    market_code: str,
    *,
    service_id: str = "website",
    project_type: str = "business_website",
    direction: str = "down",
    percent_change: float = 3.0,
    reasons: tuple[str, ...] = ("выросла конкуренция", "больше AI-студий"),
) -> MarketIntelligenceRecommendation:
    """Create a recommendation — does NOT mutate MARKET_REGISTRY."""
    market = get_market(market_code)
    if service_id == "website":
        current = market.project_range(project_type)
    else:
        current = market.service_range(service_id)
    if not current:
        raise ValueError(f"No pricing for {market_code}/{service_id}/{project_type}")

    factor = 1.0 - (percent_change / 100.0) if direction == "down" else 1.0 + (percent_change / 100.0)

    def _adj(v: int) -> int:
        return max(10, int(round(v * factor)))

    recommended = MarketPriceRange(
        from_amount=_adj(current.from_amount),
        to_amount=_adj(current.to_amount),
        average_market=_adj(current.average_market),
    )
    rec = MarketIntelligenceRecommendation(
        recommendation_id=f"mi-{market_code}-{service_id}-{len(_PENDING) + 1}",
        market_code=market_code,
        service_id=service_id,
        project_type=project_type if service_id == "website" else None,
        direction=direction,
        percent_change=percent_change,
        reasons=reasons,
        previous_range=current,
        recommended_range=recommended,
    )
    _PENDING.append(rec)
    return rec


def list_pending_recommendations() -> list[MarketIntelligenceRecommendation]:
    return [r for r in _PENDING if r.status == RecommendationStatus.PENDING]


def approve_recommendation(recommendation_id: str) -> bool:
    for rec in _PENDING:
        if rec.recommendation_id == recommendation_id and rec.status == RecommendationStatus.PENDING:
            rec.status = RecommendationStatus.APPROVED
            return True
    return False


def reject_recommendation(recommendation_id: str) -> bool:
    for rec in _PENDING:
        if rec.recommendation_id == recommendation_id and rec.status == RecommendationStatus.PENDING:
            rec.status = RecommendationStatus.REJECTED
            return True
    return False


def format_ceo_notification(rec: MarketIntelligenceRecommendation) -> str:
    market = get_market(rec.market_code)
    label = (
        project_type_label(rec.project_type or "business_website")
        if rec.service_id == "website"
        else rec.service_id
    )
    arrow = "⬇" if rec.direction == "down" else "⬆" if rec.direction == "up" else "→"
    reasons = "\n".join(f"• {r}" for r in rec.reasons)
    prev = rec.previous_range
    nxt = rec.recommended_range
    sym = market.symbol
    return (
        f"**Market Intelligence**\n\n"
        f"**{market.name('ru')}** · {label}\n"
        f"Средняя цена на рынке: {arrow} {rec.percent_change:.0f}%\n\n"
        f"**Причина:**\n{reasons}\n\n"
        f"**Рекомендуем:** {prev.average_market} {sym} → **{nxt.average_market} {sym}**\n"
        f"Диапазон: {prev.from_amount}–{prev.to_amount} → {nxt.from_amount}–{nxt.to_amount} {sym}\n\n"
        f"Действие владельца: **Принять** или **Оставить мои цены**.\n"
        f"Автоматического изменения нет."
    )


def market_intelligence_rules_for_vector() -> str:
    return """## Market Intelligence (архитектура)

```
Market Registry → Market Intelligence → CEO Notification → Approve → Registry update
```

- **Никаких автоматических изменений цен** в реестре.
- Market Intelligence формирует **рекомендации** (тренд, конкуренция, AI-студии).
- **Internal CEO Edition** получает уведомление; владелец нажимает «Принять» или «Оставить».
- Только после одобрения обновляется Global Market Database.

Customer Edition (Vector) использует **текущий** реестр; не меняет цены сам."""
