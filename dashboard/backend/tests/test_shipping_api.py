"""Gen1 Shipping APIs — connect, rates, create shipment, track."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.integration.platform_global_analytics import (
    build_gen1_readiness,
    build_shipping_analytics,
)
from app.integration.store_admin.commerce_settings import (
    StoreCommerceSettingsService,
    shipping_guidance,
)
from app.integration.store_admin.shipping_api_service import StoreShippingApiService
from app.integration.store_checkout import StoreCheckoutService
from app.integration.store_customer.service import StoreCustomerService


@pytest.fixture()
def shipping_mock(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")


@pytest.fixture()
def buyer_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STORE_BUYER_JWT_SECRET", "test-shipping-secret-key")


def _seed_order(memory: Path, store_id: str, shop_order_id: str = "so-ship1") -> dict:
    shop = memory / "store_admin" / store_id
    shop.mkdir(parents=True, exist_ok=True)
    order = {
        "id": shop_order_id,
        "status": "awaiting_invoice",
        "buyer_id": "buyer-1",
        "buyer_email": "anna@example.de",
        "shipping_method": {
            "id": "dhl_standard",
            "carrier": "dhl",
            "label": "DHL Standard",
            "price_eur": 7.9,
        },
        "total_eur": 50.0,
    }
    (shop / "orders.json").write_text(
        json.dumps({"orders": [order]}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return order


def test_shipping_api_required_on_manual_connect(tmp_path: Path):
    commerce = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="shipping_api_required"):
        commerce.connect("shop-ship", "dhl", account="dhl@x.de")


def test_connect_quote_create_track(tmp_path: Path, shipping_mock):
    store_id = "shop-ship"
    ship = StoreShippingApiService(tmp_path)
    connected = ship.connect_carrier(
        store_id, "dhl", {"account_name": "DHL Business"}
    )
    assert connected["ok"] is True
    assert connected["provider"]["status"] == "connected"
    assert connected["services"]
    assert "✅" in (connected.get("vector_hint") or {}).get("message", "")

    quotes = ship.quote_rates(store_id)
    assert quotes["count"] >= 1
    assert any(q["carrier"] == "dhl" for q in quotes["quotes"])

    _seed_order(tmp_path, store_id)
    created = ship.create_shipment(store_id, shop_order_id="so-ship1")
    assert created["ok"] is True
    tracking = created["shipment"]["tracking_number"]
    assert tracking
    assert created["order"]["status"] == "shipped"

    tracked = ship.track_shipment(
        store_id, tracking_number=tracking, advance=True
    )
    assert tracked["shipment"]["status"] == "picked_up"

    stats = build_shipping_analytics(tmp_path)
    assert stats["dhl"] == 1
    assert stats["shipments_created"] == 1

    ready = build_gen1_readiness(tmp_path)
    ship_item = next(i for i in ready["items"] if i["id"] == "shipping_api")
    assert ship_item["status"] == "done"


def test_checkout_only_connected_carriers(tmp_path: Path, shipping_mock):
    checkout = StoreCheckoutService(tmp_path)
    empty = checkout.checkout_options("shop-co")
    assert empty["shipping_methods"] == []
    assert empty["shipping_ready"] is False

    StoreShippingApiService(tmp_path).connect_carrier(
        "shop-co", "dhl", {"account_name": "DHL Business"}
    )
    StoreCommerceSettingsService(tmp_path).connect("shop-co", "pickup")

    opts = checkout.checkout_options("shop-co")
    carriers = {m["carrier"] for m in opts["shipping_methods"]}
    assert "dhl" in carriers
    assert "pickup" in carriers
    assert "fedex" not in carriers


def test_vector_shipping_none_message(tmp_path: Path):
    commerce = StoreCommerceSettingsService(tmp_path)
    settings = commerce.get("shop-v")["settings"]
    tips = shipping_guidance(settings)
    none = next(t for t in tips if t["id"] == "ship_none")
    assert "не может отправлять" in none["message"]
    assert none["cta_label"] == "Открыть Shipping"


def test_buyer_sees_tracking(
    tmp_path: Path, shipping_mock, buyer_secret
):
    store_id = "shop-buyer-ship"
    customers = StoreCustomerService(tmp_path)
    reg = customers.register(
        store_id,
        {
            "email": "buyer@ship.de",
            "password": "password123",
            "first_name": "A",
            "last_name": "B",
        },
    )
    buyer_id = reg["buyer"]["id"]
    customers.attach_order(
        store_id,
        buyer_id,
        {
            "id": "so-ship1",
            "status": "awaiting_invoice",
            "total_eur": 40,
            "shipping_method": "DHL Standard",
            "carrier": "dhl",
        },
    )
    StoreShippingApiService(tmp_path).connect_carrier(
        store_id, "dhl", {"account_name": "DHL Business"}
    )
    _seed_order(tmp_path, store_id)
    # fix buyer_id on seeded order
    path = tmp_path / "store_admin" / store_id / "orders.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data["orders"][0]["buyer_id"] = buyer_id
    path.write_text(json.dumps(data), encoding="utf-8")

    StoreShippingApiService(tmp_path).create_shipment(
        store_id, shop_order_id="so-ship1"
    )
    orders = customers.get_orders(store_id, buyer_id)
    row = orders["orders"][0]
    assert row.get("tracking_number")
    assert row.get("carrier") == "dhl"
    assert row.get("shipping_status") == "label_created"
