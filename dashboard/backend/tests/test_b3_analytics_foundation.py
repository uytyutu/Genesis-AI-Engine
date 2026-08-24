"""B3 Analytics Foundation — MetricContract, sources, no fake KPIs."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.client_analytics.contracts import MetricContract, MetricPoint
from app.integration.client_analytics.service import ClientAnalyticsService
from app.integration.client_analytics.sources import (
    DataSourceRegistry,
    derive_analytics_state,
    resolve_product_flags,
)
from app.integration.customer_identity.b3_review_fixture import (
    seed_b3_empty_client,
    seed_b3_review_client,
)
from app.integration.sales_order_service import SalesOrderService
from app.integration.factory_intent_service import FactoryIntentService
from app.factory.factory_service import FactoryService


@pytest.fixture()
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!")
    root = tmp_path / "memory"
    root.mkdir()
    return root


def _sales(memory: Path) -> SalesOrderService:
    factory = FactoryService(memory_dir=memory, sandbox_dir=memory / "sandbox")
    intent = FactoryIntentService(memory_dir=memory, factory=factory)
    return SalesOrderService(memory, intent)


def test_metric_contract_requires_source_id():
    m = MetricContract(
        metric_id="shop_orders_count",
        label="Shop-Bestellungen",
        unit="count",
        period="30d",
        points=(MetricPoint(t="2026-08-24", v=3.0),),
        source_id="store_checkout",
        as_of="2026-08-24T12:00:00Z",
        product="shop",
    )
    d = m.to_dict()
    assert d["source_id"] == "store_checkout"
    assert d["point_count"] == 1
    assert d["points"][0]["v"] == 3.0


def test_website_owned_traffic_not_connected_no_fake_visitors(mem: Path):
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    orders = sales.list_orders_for_customer(
        customer_id=fx.customer_id, email=fx.email, limit=20
    )
    flags = resolve_product_flags(orders)
    assert flags.has_website is True

    sources, metrics, _ = DataSourceRegistry(mem).collect(
        customer_id=fx.customer_id,
        orders=orders,
        analytics_traffic_connected=False,
    )
    traffic = next(s for s in sources if s.source_id == "website_traffic")
    assert traffic.status == "not_connected"

    # No invented visitor series
    assert not any(m.metric_id.startswith("website_visitor") for m in metrics)
    assert not any("besucher" in m.label.lower() for m in metrics)

    state = derive_analytics_state(
        flags=flags, sources=sources, analytics_traffic_connected=False
    )
    assert state == "not_connected"


def test_overview_has_virtus_orders_metric_when_fixture_ready(mem: Path):
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    svc = ClientAnalyticsService(mem, sales=sales)
    overview = svc.overview(customer_id=fx.customer_id, email=fx.email)
    assert overview["ok"] is True
    assert overview["analytics_state"] == "not_connected"
    assert overview["analytics_cta"] == "Analytics hinzufügen"
    assert overview["products"]["website"]["owned"] is True

    ids = {m["metric_id"] for m in overview["metrics"]}
    assert "virtus_orders_total" in ids
    # Every metric must cite a source
    for m in overview["metrics"]:
        assert m.get("source_id")
        assert isinstance(m.get("points"), list)


def test_empty_client_coming_soon_or_not_connected(mem: Path):
    fx = seed_b3_empty_client(mem)
    sales = _sales(mem)
    svc = ClientAnalyticsService(mem, sales=sales)
    overview = svc.overview(customer_id=fx.customer_id, email=fx.email)
    assert overview["analytics_state"] == "coming_soon"
    assert overview["metrics"] == [] or all(
        m.get("source_id") for m in overview["metrics"]
    )


def test_connect_traffic_refuses_fake_success(mem: Path):
    fx = seed_b3_review_client(mem)
    svc = ClientAnalyticsService(mem, sales=_sales(mem))
    out = svc.connect_traffic(customer_id=fx.customer_id)
    assert out["ok"] is False
    assert out["status"] == "coming_soon"
    overview = svc.overview(customer_id=fx.customer_id, email=fx.email)
    assert overview["products"]["analytics"]["traffic_connected"] is False


def test_client_context_embeds_same_analytics(mem: Path):
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    svc = ClientAnalyticsService(mem, sales=sales)
    ctx = svc.client_context(
        customer_id=fx.customer_id,
        email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
    )
    assert ctx["ok"] is True
    assert ctx["engine"] == "b3_client_context_v1"
    assert "analytics" in ctx["read"]
    assert ctx["analytics"]["engine"] == "b3_analytics_foundation_v1"
    assert ctx["analytics"]["analytics_state"] == "not_connected"
    assert ctx["business"]["company_name"] == fx.business_name


def test_shop_owned_zero_checkout_connected_no_data(mem: Path):
    """Shop Aktiv + zero buyer orders → connected_no_data, no fake revenue points."""
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    # Attach a shop order without checkout rows
    from datetime import datetime, timezone

    created = sales.create_order(
        {
            "business_name": "B3 Shop Gate",
            "description": "Shop for analytics foundation",
            "email": fx.email,
            "package_id": "ecommerce_shop",
            "product_kind": "shop",
            "city": "Berlin",
            "niche": "handwerk",
            "market_code": "DE",
            "demo": True,
            "customer_id": fx.customer_id,
        }
    )
    oid = str(created["order_id"])
    order = sales.get_order(oid)
    assert order
    now = datetime.now(timezone.utc).isoformat()
    order["customer_id"] = fx.customer_id
    order["status"] = "ready"
    order["paid_at"] = now
    order["product_kind"] = "shop"
    order["package_id"] = "ecommerce_shop"
    sales._save_order(order)  # noqa: SLF001

    orders = sales.list_orders_for_customer(
        customer_id=fx.customer_id, email=fx.email, limit=50
    )
    sources, metrics, flags = DataSourceRegistry(mem).collect(
        customer_id=fx.customer_id,
        orders=orders,
        load_shop_orders=lambda _oid: [],
    )
    assert flags.has_shop is True
    store = next(s for s in sources if s.source_id == "store_checkout")
    assert store.status == "connected_no_data"
    assert not any(m.metric_id == "shop_revenue" for m in metrics)
    assert not any(m.metric_id == "shop_orders_count" for m in metrics)


def test_no_synthetic_visitor_points_in_any_metric(mem: Path):
    fx = seed_b3_review_client(mem)
    overview = ClientAnalyticsService(mem, sales=_sales(mem)).overview(
        customer_id=fx.customer_id, email=fx.email
    )
    forbidden = ("visitor", "besucher", "pageview", "traffic_fake")
    for m in overview["metrics"]:
        blob = f"{m.get('metric_id')} {m.get('label')}".lower()
        assert not any(f in blob for f in forbidden)


def test_shop_not_owned_store_source_coming_soon(mem: Path):
    fx = seed_b3_review_client(mem)
    sales = _sales(mem)
    orders = sales.list_orders_for_customer(
        customer_id=fx.customer_id, email=fx.email, limit=20
    )
    sources, _, flags = DataSourceRegistry(mem).collect(
        customer_id=fx.customer_id, orders=orders
    )
    assert flags.has_shop is False
    store = next(s for s in sources if s.source_id == "store_checkout")
    assert store.status == "coming_soon"
    crm = next(s for s in sources if s.source_id == "crm_pipeline")
    assert crm.status == "coming_soon"
