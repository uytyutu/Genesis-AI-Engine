"""Analytics Service — single SSOT for BCC charts + Client Context (Vector later)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.integration.client_analytics.contracts import (
    AnalyticsOverview,
    ConnectionState,
    Period,
    empty_copy_for,
)
from app.integration.client_analytics.sources import (
    DataSourceRegistry,
    derive_analytics_state,
)


def _connection_path(memory_dir: Path, customer_id: str) -> Path:
    return (
        Path(memory_dir)
        / "customer_identity"
        / str(customer_id)
        / "analytics_connection.json"
    )


def load_analytics_connection(memory_dir: Path, customer_id: str) -> dict[str, Any]:
    path = _connection_path(memory_dir, customer_id)
    if not path.is_file():
        return {"traffic_connected": False, "providers": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"traffic_connected": False, "providers": []}
    if not isinstance(data, dict):
        return {"traffic_connected": False, "providers": []}
    return {
        "traffic_connected": bool(data.get("traffic_connected")),
        "providers": list(data.get("providers") or []),
        "updated_at": data.get("updated_at"),
    }


def save_analytics_connection(
    memory_dir: Path, customer_id: str, payload: dict[str, Any]
) -> dict[str, Any]:
    path = _connection_path(memory_dir, customer_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return payload


def _panel(
    panel_id: str,
    *,
    product: str,
    state: ConnectionState,
    metric_ids: list[str],
    title: str,
) -> dict[str, Any]:
    return {
        "panel_id": panel_id,
        "product": product,
        "state": state,
        "title": title,
        "metric_ids": metric_ids,
    }


def build_panels(
    *,
    flags: Any,
    sources: list[Any],
    metrics: list[Any],
    analytics_state: ConnectionState,
) -> list[dict[str, Any]]:
    by_source = {s.source_id: s for s in sources}
    metric_ids = {m.metric_id for m in metrics}
    panels: list[dict[str, Any]] = []

    if flags.has_website:
        traffic = by_source.get("website_traffic")
        st: ConnectionState = (
            traffic.status if traffic else analytics_state  # type: ignore[assignment]
        )
        panels.append(
            _panel(
                "website_visitors",
                product="website",
                state=st if st in ("not_connected", "connected_no_data", "connected_with_data", "coming_soon") else "not_connected",
                metric_ids=[],
                title="Website-Besucher",
            )
        )
        panels.append(
            _panel(
                "website_pages",
                product="website",
                state=st if traffic else "not_connected",
                metric_ids=[],
                title="Seitenaufrufe",
            )
        )

    if flags.has_shop:
        shop_src = by_source.get("store_checkout")
        shop_state: ConnectionState = shop_src.status if shop_src else "coming_soon"
        panels.append(
            _panel(
                "shop_orders",
                product="shop",
                state=shop_state,
                metric_ids=[m for m in ("shop_orders_count",) if m in metric_ids],
                title="Shop-Bestellungen",
            )
        )
        panels.append(
            _panel(
                "shop_revenue",
                product="shop",
                state=shop_state,
                metric_ids=[m for m in ("shop_revenue",) if m in metric_ids],
                title="Shop-Umsatz",
            )
        )

    if flags.has_ai:
        inbox = by_source.get("virtus_inbox")
        inbox_state: ConnectionState = inbox.status if inbox else "coming_soon"
        panels.append(
            _panel(
                "website_leads",
                product="ai",
                state=inbox_state,
                metric_ids=[m for m in ("ai_inbox_threads",) if m in metric_ids],
                title="Anfragen (Inbox)",
            )
        )

    # Always declare CRM/Marketing as coming_soon panels (no fake data)
    panels.append(
        _panel(
            "crm_leads",
            product="crm",
            state="coming_soon",
            metric_ids=[],
            title="CRM Leads",
        )
    )
    panels.append(
        _panel(
            "marketing_campaigns",
            product="marketing",
            state="coming_soon",
            metric_ids=[],
            title="Marketing",
        )
    )
    return panels


class ClientAnalyticsService:
    def __init__(self, memory_dir: Path, *, sales: Any | None = None) -> None:
        self._memory = Path(memory_dir)
        self._sales = sales
        self._registry = DataSourceRegistry(self._memory)

    def _orders(self, *, customer_id: str, email: str | None) -> list[dict[str, Any]]:
        if self._sales is None:
            return []
        try:
            rows = self._sales.list_orders_for_customer(
                customer_id=str(customer_id or ""),
                email=email,
                limit=100,
            )
            return [o for o in (rows or []) if isinstance(o, dict)]
        except Exception:
            return []

    def _load_shop_orders(self, shop_order_id: str) -> list[dict[str, Any]]:
        try:
            from app.integration.store_checkout.service import StoreCheckoutService

            raw = StoreCheckoutService(self._memory).list_shop_orders(shop_order_id)
            rows = list(raw.get("orders") or [])
            return [r for r in rows if isinstance(r, dict)]
        except Exception:
            return []

    def _count_inbox(self, customer_id: str) -> int:
        try:
            from app.integration.workspace_inbox_service import list_threads

            raw = list_threads(self._memory, customer_id, limit=200)
            if isinstance(raw, dict):
                threads = raw.get("threads") or []
                return len(threads)
            if isinstance(raw, list):
                return len(raw)
            return 0
        except Exception:
            return 0

    def overview(
        self,
        *,
        customer_id: str,
        email: str | None = None,
        period: Period = "30d",
    ) -> dict[str, Any]:
        orders = self._orders(customer_id=customer_id, email=email)
        conn = load_analytics_connection(self._memory, customer_id)
        traffic_connected = bool(conn.get("traffic_connected"))

        sources, metrics, flags = self._registry.collect(
            customer_id=customer_id,
            orders=orders,
            period=period,
            load_shop_orders=self._load_shop_orders,
            count_inbox_threads=self._count_inbox,
            analytics_traffic_connected=traffic_connected,
        )
        analytics_state = derive_analytics_state(
            flags=flags,
            sources=sources,
            analytics_traffic_connected=traffic_connected,
        )
        panels = build_panels(
            flags=flags,
            sources=sources,
            metrics=metrics,
            analytics_state=analytics_state,
        )

        cta = "Analytics hinzufügen"
        cta_href = "/client/analytics"
        if analytics_state == "coming_soon":
            cta = "Coming Soon"
            cta_href = "/client/products"
        elif analytics_state in ("connected_no_data", "connected_with_data"):
            cta = "Analytics öffnen"
            cta_href = "/client/analytics"

        overview = AnalyticsOverview(
            analytics_state=analytics_state,
            analytics_cta=cta,
            analytics_cta_href=cta_href,
            products={
                "website": {
                    "owned": flags.has_website,
                    "order_id": flags.website_order_id,
                    "status": "active" if flags.has_website else "not_activated",
                },
                "shop": {
                    "owned": flags.has_shop,
                    "order_id": flags.shop_order_id,
                    "status": "active" if flags.has_shop else "not_activated",
                },
                "ai": {
                    "owned": flags.has_ai,
                    "status": "active" if flags.has_ai else "not_activated",
                },
                "analytics": {
                    "owned": traffic_connected,
                    "status": analytics_state,
                    "traffic_connected": traffic_connected,
                },
            },
            sources=[s.to_dict() for s in sources],
            metrics=[m.to_dict() for m in metrics],
            panels=panels,
            copy=empty_copy_for(analytics_state),
        )
        return overview.to_dict()

    def connect_traffic(self, *, customer_id: str) -> dict[str, Any]:
        """Honest connect gate — external trackers not live yet.

        Does NOT set traffic_connected=True (would imply fake Besucher).
        Returns coming_soon so UI never shows a false Connected success.
        """
        return {
            "ok": False,
            "status": "coming_soon",
            "detail": "external_analytics_tracker_not_available",
            "message": (
                "Externe Besucher-Analytics (Pixel / GA / Plausible) ist noch nicht "
                "anschließbar. Interne Shop-/Inbox-Kennzahlen erscheinen automatisch, "
                "sobald echte Ereignisse vorliegen."
            ),
            "analytics_cta": "Coming Soon",
            "analytics_cta_href": "/client/products",
        }

    def client_context(
        self,
        *,
        customer_id: str,
        email: str | None = None,
        me: dict[str, Any] | None = None,
        period: Period = "30d",
    ) -> dict[str, Any]:
        """Unified payload for BCC + future Vector — same Analytics SSOT."""
        analytics = self.overview(
            customer_id=customer_id, email=email, period=period
        )
        me = me or {}
        return {
            "ok": True,
            "engine": "b3_client_context_v1",
            "read": [
                "business",
                "products",
                "website",
                "shop",
                "ai",
                "analytics",
                "orders",
            ],
            "action": ["propose", "navigate"],
            "business": {
                "company_name": me.get("company_display_name")
                or me.get("company_name")
                or me.get("name"),
                "email": me.get("email") or email,
                "business_id": me.get("business_id"),
                "primary_niche": me.get("primary_niche") or "",
            },
            "products": analytics.get("products") or {},
            "analytics": analytics,
            "orders_summary": {
                "metric_ids": [
                    m.get("metric_id")
                    for m in (analytics.get("metrics") or [])
                    if str(m.get("source_id") or "") == "virtus_orders"
                ],
            },
        }
