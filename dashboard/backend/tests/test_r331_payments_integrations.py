"""R3.3.1 Payments + Integrations connection cards."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.vector.capabilities import action_for, is_live


def test_payments_stripe_capability_live():
    assert is_live("payments_stripe") is True
    action = action_for("payments_stripe")
    assert action["kind"] == "navigate_section"
    assert action["section"] == "payments"


def test_shipping_capability_live_in_r331_compat():
    assert is_live("shipping_carriers") is True
    assert action_for("shipping_carriers")["kind"] == "navigate_section"


def test_connect_stripe_requires_oauth(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="oauth_required"):
        svc.connect("ord-1", "stripe")
    with pytest.raises(ValueError, match="oauth_required"):
        svc.connect("ord-1", "stripe", account="shop@example.de")


def test_connect_disconnect_stripe_via_oauth(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STRIPE_CONNECT_MOCK", "1")
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.apply_stripe_oauth(
        "ord-1",
        stripe_user_id="acct_mock_shop01",
        account_label="shop@example.de",
        mock=True,
    )
    assert out["provider"]["status"] == "connected"
    assert out["provider"]["account"] == "shop@example.de"
    assert out["provider"]["last_sync_label"]
    assert "reconnect" in out["provider"]["actions"]

    hub = svc.integrations_hub("ord-1")
    payments = next(s for s in hub["sections"] if s["id"] == "payments")
    stripe = next(i for i in payments["items"] if i["id"] == "stripe")
    assert stripe["status"] == "connected"
    assert stripe["connect_mode"] == "oauth"

    got = svc.get("ord-1")
    assert got["commerce_ready"] is True

    disc = svc.disconnect("ord-1", "stripe")
    assert disc["provider"]["status"] == "not_connected"
    got_after = svc.get("ord-1")
    assert got_after["commerce_ready"] is False


def test_invoice_connect_without_account(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.connect("ord-1", "invoice")
    assert out["provider"]["status"] == "connected"


def test_dhl_connectable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_SHIPPING_MOCK", "1")
    from app.integration.store_admin.shipping_api_service import StoreShippingApiService

    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="shipping_api_required"):
        svc.connect("ord-1", "dhl", account="dhl@x.de")
    out = StoreShippingApiService(tmp_path).connect_carrier(
        "ord-1", "dhl", {"account_name": "dhl@x.de"}
    )
    assert out["provider"]["status"] == "connected"


def test_pickup_connectable(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    out = svc.connect("ord-1", "pickup")
    assert out["provider"]["status"] == "connected"


def test_unified_card_shape(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    hub = svc.integrations_hub("ord-x")
    labels = [s["label"] for s in hub["sections"]]
    assert "Payments" in labels
    assert "Shipping" in labels
    assert "Email" in labels
    pay = next(s for s in hub["sections"] if s["id"] == "payments")
    ids = {i["id"] for i in pay["items"]}
    assert {"stripe", "paypal", "klarna", "sepa", "invoice", "cash_on_delivery"} <= ids
    for item in pay["items"]:
        assert "status" in item
        assert "account" in item
        assert "last_sync_label" in item
        assert "actions" in item
    stripe = next(i for i in pay["items"] if i["id"] == "stripe")
    assert stripe["connect_mode"] == "oauth"
