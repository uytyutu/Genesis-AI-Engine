"""Stripe Connect OAuth — merchant Connect / Connected / Disconnect / Sync."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration import stripe_connect_oauth as stripe_oauth
from app.integration.platform_global_analytics import build_gen1_readiness
from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService


@pytest.fixture(autouse=True)
def _mock_stripe_connect(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_STRIPE_CONNECT_MOCK", "1")
    monkeypatch.delenv("STRIPE_CONNECT_CLIENT_ID", raising=False)


def test_oauth_client_ready_in_mock():
    assert stripe_oauth.oauth_client_ready() is True
    assert stripe_oauth.mock_enabled() is True


def test_manual_stripe_connect_rejected(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    with pytest.raises(ValueError, match="oauth_required"):
        svc.connect("ord-1", "stripe", account="shop@example.de")


def test_apply_stripe_oauth_connect_disconnect_sync(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    exchanged = stripe_oauth.exchange_code(code="tok_test", redirect_uri="http://localhost/cb")
    assert exchanged["ok"] is True
    acct = exchanged["stripe_user_id"]
    assert acct.startswith("acct_")

    out = svc.apply_stripe_oauth(
        "ord-1",
        stripe_user_id=acct,
        account_label="shop@nordlicht.de",
        livemode=False,
        scope="read_write",
        mock=True,
    )
    assert out["provider"]["status"] == "connected"
    assert out["provider"]["stripe_user_id"] == acct
    assert out["provider"]["connect_mode"] == "oauth"

    hub = svc.integrations_hub("ord-1")
    stripe = next(
        i
        for s in hub["sections"]
        if s["id"] == "payments"
        for i in s["items"]
        if i["id"] == "stripe"
    )
    assert stripe["status"] == "connected"
    assert stripe["oauth_ready"] is True

    synced = svc.sync("ord-1", "stripe")
    assert synced["provider"]["status"] == "connected"
    assert synced["provider"]["last_sync_label"]

    disc = svc.disconnect("ord-1", "stripe")
    assert disc["provider"]["status"] == "not_connected"
    assert disc["provider"]["stripe_user_id"] is None
    assert disc.get("deauthorize", {}).get("ok") is True


def test_oauth_state_roundtrip():
    state = stripe_oauth.create_oauth_state(order_id="ord-abc", return_url="http://x/y")
    payload = stripe_oauth.consume_oauth_state(state)
    assert payload is not None
    assert payload["order_id"] == "ord-abc"
    assert stripe_oauth.consume_oauth_state(state) is None


def test_gen1_readiness_stripe_pending_then_done(tmp_path: Path):
    before = build_gen1_readiness(tmp_path)
    assert before["title"] == "Gen1 Readiness"
    stripe_item = next(i for i in before["items"] if i["id"] == "stripe_oauth")
    assert stripe_item["status"] == "pending"
    assert before["done"] == 6
    assert before["next"]["id"] == "stripe_oauth"

    svc = StoreCommerceSettingsService(tmp_path)
    svc.apply_stripe_oauth(
        "ord-ready",
        stripe_user_id="acct_mock_ready01",
        account_label="ready@example.de",
        mock=True,
    )
    after = build_gen1_readiness(tmp_path)
    stripe_after = next(i for i in after["items"] if i["id"] == "stripe_oauth")
    assert stripe_after["status"] == "done"
    assert after["done"] == 7
    assert after["next"]["id"] == "smtp"


def test_stripe_user_id_persisted(tmp_path: Path):
    svc = StoreCommerceSettingsService(tmp_path)
    svc.apply_stripe_oauth(
        "ord-chk",
        stripe_user_id="acct_mock_chk01",
        account_label="chk@example.de",
        mock=True,
    )
    svc.connect("ord-chk", "pickup")
    settings = svc.get("ord-chk")["settings"]
    assert settings["payments"]["stripe"]["stripe_user_id"] == "acct_mock_chk01"
