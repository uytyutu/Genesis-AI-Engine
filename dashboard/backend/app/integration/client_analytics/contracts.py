"""B3 Analytics Foundation — MetricContract + connection states.

Law: never invent visitors/revenue. Only emit MetricSeries when a real
DataSource reports connected_with_data (or connected_no_data with empty points).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ConnectionState = Literal[
    "not_connected",
    "connected_no_data",
    "connected_with_data",
    "coming_soon",
]

Period = Literal["today", "7d", "30d", "12m"]


@dataclass(frozen=True)
class MetricPoint:
    t: str  # ISO date or bucket label
    v: float


@dataclass(frozen=True)
class MetricContract:
    """One real metric series — chart-ready, never synthetic."""

    metric_id: str
    label: str
    unit: str  # count | eur | ratio | text
    period: Period
    points: tuple[MetricPoint, ...]
    source_id: str
    as_of: str
    product: str  # website | shop | ai | marketing | crm | platform

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_id": self.metric_id,
            "label": self.label,
            "unit": self.unit,
            "period": self.period,
            "points": [{"t": p.t, "v": p.v} for p in self.points],
            "source_id": self.source_id,
            "as_of": self.as_of,
            "product": self.product,
            "point_count": len(self.points),
        }


@dataclass(frozen=True)
class DataSourceStatus:
    source_id: str
    label: str
    status: ConnectionState
    reason: str
    product: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ProductFlags:
    has_website: bool = False
    has_shop: bool = False
    has_ai: bool = False
    has_domain: bool = False
    website_order_id: str | None = None
    shop_order_id: str | None = None


@dataclass
class AnalyticsOverview:
    """SSOT payload for BCC Analytics UI + Client Context (Vector later)."""

    ok: bool = True
    engine: str = "b3_analytics_foundation_v1"
    # Analytics module connection (traffic / dedicated analytics)
    analytics_state: ConnectionState = "not_connected"
    analytics_cta: str = "Analytics hinzufügen"
    analytics_cta_href: str = "/client/analytics"
    products: dict[str, Any] = field(default_factory=dict)
    sources: list[dict[str, Any]] = field(default_factory=list)
    metrics: list[dict[str, Any]] = field(default_factory=list)
    panels: list[dict[str, Any]] = field(default_factory=list)
    copy: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "engine": self.engine,
            "analytics_state": self.analytics_state,
            "analytics_cta": self.analytics_cta,
            "analytics_cta_href": self.analytics_cta_href,
            "products": self.products,
            "sources": self.sources,
            "metrics": self.metrics,
            "panels": self.panels,
            "copy": self.copy,
        }


def empty_copy_for(state: ConnectionState) -> dict[str, str]:
    if state == "coming_soon":
        return {
            "title": "Analytics · Coming Soon",
            "body": "Das Analytics-Modul ist noch nicht freigeschaltet.",
            "hint": "Keine Beispieldaten — Reality over Features.",
        }
    if state == "connected_no_data":
        return {
            "title": "Analytics verbunden",
            "body": "Noch keine Daten verfügbar.",
            "hint": "Sobald echte Ereignisse eintreffen, erscheinen Kennzahlen hier.",
        }
    if state == "connected_with_data":
        return {
            "title": "Analytics verbunden",
            "body": "Kennzahlen stammen nur aus angebundenen Quellen.",
            "hint": "Keine synthetischen Besucher- oder Umsatzzahlen.",
        }
    return {
        "title": "Analytics noch nicht verbunden",
        "body": (
            "Verbinde Analytics oder nutze vorhandene Produktquellen "
            "(Shop-Bestellungen, Inbox), um echte Kennzahlen zu sehen."
        ),
        "hint": "Website kann Aktiv sein — ohne verbundene Quelle keine Besucher-Grafiken.",
    }
