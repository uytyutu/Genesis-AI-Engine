"""Data-source registry — only real Virtus-backed sources in v1.

website_traffic: not_connected until an external tracker exists (no fake visits).
store_checkout: real buyer orders from Store Checkout memory.
virtus_inbox: real AI Employee / inbox threads.
virtus_orders: Virtus sales orders owned by the customer (operational).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from app.integration.client_analytics.contracts import (
    ConnectionState,
    DataSourceStatus,
    MetricContract,
    MetricPoint,
    Period,
    ProductFlags,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _is_shop(o: dict[str, Any]) -> bool:
    kind = str(o.get("product_kind") or "").lower()
    pkg = str(o.get("package_id") or "").lower()
    return kind == "shop" or "store" in kind or pkg == "ecommerce_shop"


def _is_bot(o: dict[str, Any]) -> bool:
    return str(o.get("product_kind") or "").lower().startswith("bot")


def _is_website(o: dict[str, Any]) -> bool:
    return not _is_shop(o) and not _is_bot(o)


def resolve_product_flags(orders: list[dict[str, Any]]) -> ProductFlags:
    flags = ProductFlags()
    for o in orders:
        if not isinstance(o, dict):
            continue
        st = str(o.get("status") or "").lower()
        if st in {"superseded", "cancelled", "canceled"}:
            continue
        oid = str(o.get("order_id") or "") or None
        if _is_shop(o):
            flags.has_shop = True
            if not flags.shop_order_id and oid:
                flags.shop_order_id = oid
        elif _is_bot(o):
            flags.has_ai = True
        elif _is_website(o):
            flags.has_website = True
            if not flags.website_order_id and oid:
                flags.website_order_id = oid
            if o.get("published_at") or o.get("domain"):
                flags.has_domain = True
    return flags


class DataSourceRegistry:
    """Collect MetricContracts from registered adapters."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)

    def collect(
        self,
        *,
        customer_id: str,
        orders: list[dict[str, Any]],
        period: Period = "30d",
        load_shop_orders: Callable[[str], list[dict[str, Any]]] | None = None,
        count_inbox_threads: Callable[[str], int] | None = None,
        analytics_traffic_connected: bool = False,
    ) -> tuple[list[DataSourceStatus], list[MetricContract], ProductFlags]:
        flags = resolve_product_flags(orders)
        sources: list[DataSourceStatus] = []
        metrics: list[MetricContract] = []
        as_of = _utc_now()

        # 1) Website traffic — no tracker in Gen1 → never invent visitors
        if flags.has_website:
            if analytics_traffic_connected:
                # Reserved for future pixel/GA — still no fake points
                sources.append(
                    DataSourceStatus(
                        source_id="website_traffic",
                        label="Website Traffic",
                        status="connected_no_data",
                        reason="tracker_connected_awaiting_events",
                        product="website",
                    )
                )
            else:
                sources.append(
                    DataSourceStatus(
                        source_id="website_traffic",
                        label="Website Traffic",
                        status="not_connected",
                        reason="no_visitor_tracker",
                        product="website",
                    )
                )
        else:
            sources.append(
                DataSourceStatus(
                    source_id="website_traffic",
                    label="Website Traffic",
                    status="coming_soon",
                    reason="website_not_owned",
                    product="website",
                )
            )

        # 2) Virtus sales orders (operational — real order rows)
        if orders:
            ready = sum(
                1
                for o in orders
                if isinstance(o, dict)
                and (
                    o.get("download_ready")
                    or str(o.get("status") or "").lower()
                    in {"ready", "completed", "delivered", "active"}
                )
            )
            points = (
                MetricPoint(t=as_of[:10], v=float(len(orders))),
            )
            metrics.append(
                MetricContract(
                    metric_id="virtus_orders_total",
                    label="Virtus-Aufträge",
                    unit="count",
                    period=period,
                    points=points,
                    source_id="virtus_orders",
                    as_of=as_of,
                    product="platform",
                )
            )
            metrics.append(
                MetricContract(
                    metric_id="virtus_orders_ready",
                    label="Bereite Aufträge",
                    unit="count",
                    period=period,
                    points=(MetricPoint(t=as_of[:10], v=float(ready)),),
                    source_id="virtus_orders",
                    as_of=as_of,
                    product="platform",
                )
            )
            sources.append(
                DataSourceStatus(
                    source_id="virtus_orders",
                    label="Virtus Aufträge",
                    status="connected_with_data",
                    reason="sales_orders_present",
                    product="platform",
                )
            )
        else:
            sources.append(
                DataSourceStatus(
                    source_id="virtus_orders",
                    label="Virtus Aufträge",
                    status="connected_no_data"
                    if (flags.has_website or flags.has_shop or flags.has_ai)
                    else "not_connected",
                    reason="no_sales_orders",
                    product="platform",
                )
            )

        # 3) Store checkout — real buyer orders
        if flags.has_shop and flags.shop_order_id and load_shop_orders:
            shop_rows = load_shop_orders(flags.shop_order_id) or []
            if shop_rows:
                revenue = 0.0
                for row in shop_rows:
                    if not isinstance(row, dict):
                        continue
                    for key in ("total", "amount_total", "grand_total", "total_eur"):
                        raw = row.get(key)
                        if raw is None:
                            continue
                        try:
                            revenue += float(raw)
                            break
                        except (TypeError, ValueError):
                            continue
                metrics.append(
                    MetricContract(
                        metric_id="shop_orders_count",
                        label="Shop-Bestellungen",
                        unit="count",
                        period=period,
                        points=(MetricPoint(t=as_of[:10], v=float(len(shop_rows))),),
                        source_id="store_checkout",
                        as_of=as_of,
                        product="shop",
                    )
                )
                metrics.append(
                    MetricContract(
                        metric_id="shop_revenue",
                        label="Shop-Umsatz",
                        unit="eur",
                        period=period,
                        points=(MetricPoint(t=as_of[:10], v=revenue),),
                        source_id="store_checkout",
                        as_of=as_of,
                        product="shop",
                    )
                )
                sources.append(
                    DataSourceStatus(
                        source_id="store_checkout",
                        label="Store Checkout",
                        status="connected_with_data",
                        reason="shop_orders_present",
                        product="shop",
                    )
                )
            else:
                sources.append(
                    DataSourceStatus(
                        source_id="store_checkout",
                        label="Store Checkout",
                        status="connected_no_data",
                        reason="shop_owned_zero_orders",
                        product="shop",
                    )
                )
        elif flags.has_shop:
            sources.append(
                DataSourceStatus(
                    source_id="store_checkout",
                    label="Store Checkout",
                    status="connected_no_data",
                    reason="shop_owned_checkout_unavailable",
                    product="shop",
                )
            )
        else:
            sources.append(
                DataSourceStatus(
                    source_id="store_checkout",
                    label="Store Checkout",
                    status="coming_soon",
                    reason="shop_not_owned",
                    product="shop",
                )
            )

        # 4) Inbox / Anfragen
        if flags.has_ai and count_inbox_threads:
            n = int(count_inbox_threads(customer_id) or 0)
            if n > 0:
                metrics.append(
                    MetricContract(
                        metric_id="ai_inbox_threads",
                        label="Inbox-Anfragen",
                        unit="count",
                        period=period,
                        points=(MetricPoint(t=as_of[:10], v=float(n)),),
                        source_id="virtus_inbox",
                        as_of=as_of,
                        product="ai",
                    )
                )
                sources.append(
                    DataSourceStatus(
                        source_id="virtus_inbox",
                        label="AI Inbox",
                        status="connected_with_data",
                        reason="inbox_threads_present",
                        product="ai",
                    )
                )
            else:
                sources.append(
                    DataSourceStatus(
                        source_id="virtus_inbox",
                        label="AI Inbox",
                        status="connected_no_data",
                        reason="ai_owned_zero_threads",
                        product="ai",
                    )
                )
        elif flags.has_ai:
            sources.append(
                DataSourceStatus(
                    source_id="virtus_inbox",
                    label="AI Inbox",
                    status="connected_no_data",
                    reason="ai_owned_inbox_unavailable",
                    product="ai",
                )
            )
        else:
            sources.append(
                DataSourceStatus(
                    source_id="virtus_inbox",
                    label="AI Inbox",
                    status="coming_soon",
                    reason="ai_not_owned",
                    product="ai",
                )
            )

        # CRM / Marketing — honest coming_soon (no backends)
        for sid, label, product in (
            ("crm_pipeline", "CRM", "crm"),
            ("marketing_campaigns", "Marketing", "marketing"),
        ):
            sources.append(
                DataSourceStatus(
                    source_id=sid,
                    label=label,
                    status="coming_soon",
                    reason="module_not_shipped",
                    product=product,
                )
            )

        return sources, metrics, flags


def derive_analytics_state(
    *,
    flags: ProductFlags,
    sources: list[DataSourceStatus],
    analytics_traffic_connected: bool,
) -> ConnectionState:
    """Analytics module state shown on BCC (traffic-focused)."""
    if not (flags.has_website or flags.has_shop or flags.has_ai):
        return "coming_soon"

    traffic = next((s for s in sources if s.source_id == "website_traffic"), None)
    if analytics_traffic_connected:
        if traffic and traffic.status == "connected_with_data":
            return "connected_with_data"
        return "connected_no_data"

    # Website Aktiv but traffic not connected → not_connected (Hinzufügen)
    if flags.has_website:
        return "not_connected"

    # Shop/AI only: still not_connected for dedicated Analytics until traffic/source linked
    return "not_connected"
