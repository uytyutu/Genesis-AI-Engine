"""Checkout 1.0 — place order without live PSP."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.platform_global_analytics import (
    PlatformGlobalAnalyticsService,
    build_platform_funnel,
    build_revenue_dashboard,
)
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_checkout import StoreCheckoutService
from app.integration.store_customer.service import StoreCustomerService


@pytest.fixture()
def buyer_secret(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STORE_BUYER_JWT_SECRET", "test-checkout-secret-key")


def test_checkout_options_defaults(tmp_path: Path):
    svc = StoreCheckoutService(tmp_path)
    out = svc.checkout_options("shop-1")
    assert out["ok"] is True
    assert out["shipping_methods"] == []
    assert out["shipping_ready"] is False
    assert out["payment_methods"]
    assert any(p["id"] in {"invoice", "cash_on_delivery"} for p in out["payment_methods"])


def test_place_order_full_path(tmp_path: Path, buyer_secret, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")
    from app.integration.store_admin.shipping_api_service import StoreShippingApiService

    commerce = StoreCommerceSettingsService(tmp_path)
    commerce.apply_stripe_oauth(
        "shop-1",
        stripe_user_id="acct_mock_shop1",
        account_label="owner@shop.de",
        mock=True,
    )
    StoreShippingApiService(tmp_path).connect_carrier(
        "shop-1", "dhl", {"account_name": "dhl@shop.de"}
    )
    commerce.update_shipping_config(
        "shop-1",
        {
            "free_shipping_from_eur": 100,
            "methods": [
                {
                    "id": "dhl_standard",
                    "carrier": "dhl",
                    "label": "DHL Standard",
                    "days_min": 3,
                    "days_max": 5,
                    "price_eur": 7.9,
                    "enabled": True,
                }
            ],
        },
    )

    customers = StoreCustomerService(tmp_path)
    reg = customers.register(
        "shop-1",
        {
            "email": "buyer@example.de",
            "password": "password123",
            "first_name": "Anna",
            "last_name": "M",
        },
    )
    buyer_id = reg["buyer"]["id"]

    checkout = StoreCheckoutService(tmp_path)
    placed = checkout.place_order(
        "shop-1",
        buyer_id,
        {
            "items": [
                {"id": "p1", "name": "Tee", "price": 29.9, "qty": 2},
            ],
            "address": {
                "full_name": "Anna M",
                "line1": "Hauptstr. 1",
                "city": "Berlin",
                "postal_code": "10115",
                "country": "DE",
            },
            "shipping_method_id": "dhl_standard",
            "payment_method_id": "stripe",
            "save_address": True,
        },
    )
    assert placed["ok"] is True
    assert placed["order"]["total_eur"] == round(29.9 * 2 + 7.9, 2)
    assert placed["order"]["live_charge"] is False
    assert placed["email"]["delivery"] == "outbox_stub"

    orders = customers.get_orders("shop-1", buyer_id)
    assert len(orders["orders"]) == 1
    assert orders["orders"][0]["id"] == placed["order"]["id"]

    admin = checkout.list_shop_orders("shop-1")
    assert admin["count"] == 1
    mail = checkout.list_mail_outbox("shop-1")
    assert mail["messages"]

    rev = build_revenue_dashboard(tmp_path)
    assert rev["metrics"]["shop_orders_total"] == 1
    assert rev["metrics"]["shop_gmv_eur"] == placed["order"]["total_eur"]
    assert rev["metrics"]["pending_orders"] >= 1

    funnel = build_platform_funnel(tmp_path)
    assert funnel["counts"].get("checkout_completed", 0) >= 1
    assert any(s["id"] == "first_order" for s in funnel["stages"])

    snap = PlatformGlobalAnalyticsService(tmp_path).global_snapshot()
    assert "revenue" in snap
    assert "funnel" in snap


def test_place_order_requires_auth_buyer(tmp_path: Path, buyer_secret):
    checkout = StoreCheckoutService(tmp_path)
    with pytest.raises(ValueError, match="buyer_not_found"):
        checkout.place_order(
            "shop-x",
            "missing",
            {
                "items": [{"id": "1", "name": "X", "price": 10, "qty": 1}],
                "address": {"line1": "A", "city": "B"},
                "shipping_method_id": "pickup_free",
                "payment_method_id": "invoice",
            },
        )


def test_composer_writes_checkout_js():
    from app.factory.store_factory.composer import compose_checkout_js

    js = compose_checkout_js({})
    assert "/checkout/place" in js
    assert "/checkout/options" in js
