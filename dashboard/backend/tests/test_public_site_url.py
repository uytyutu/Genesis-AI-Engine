"""Public storefront URL must not fall back to retired Vercel host."""

from __future__ import annotations

import pytest

from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.public_site_url import (
    canonicalize_storefront_url,
    configured_public_base,
)


def test_configured_public_base_ignores_legacy_vercel(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PUBLIC_URL", "https://genesis-ai-engine.vercel.app")
    assert configured_public_base() == "https://beta.genesis-ai-engine.com"


def test_configured_public_base_rejects_any_vercel_app(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PUBLIC_URL", "https://foo.vercel.app")
    assert configured_public_base() == "https://beta.genesis-ai-engine.com"


def test_canonicalize_rewrites_vercel_success_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("GENESIS_PUBLIC_URL", "https://beta.genesis-ai-engine.com")
    out = canonicalize_storefront_url(
        "https://genesis-ai-engine.vercel.app/order/status/ord-1?paid=1"
    )
    assert out.startswith("https://beta.genesis-ai-engine.com/")
    assert "ord-1" in out
    assert "paid=1" in out
    assert "vercel.app" not in out


def test_stripe_checkout_rewrites_legacy_success_url(
    monkeypatch: pytest.MonkeyPatch, tmp_path
):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.setenv("GENESIS_PUBLIC_URL", "https://beta.genesis-ai-engine.com")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)
    captured: dict = {}

    class _FakeResp:
        status_code = 200

        def json(self):
            return {"id": "cs_test", "url": "https://checkout.stripe.com/c/pay/cs_test"}

    class _FakeClient:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def post(self, url, data=None, auth=None):
            captured["data"] = data
            return _FakeResp()

    import app.integration.payment_checkout_service as mod

    monkeypatch.setattr(mod.httpx, "Client", _FakeClient)
    checkout = PaymentCheckoutService(tmp_path)
    out = checkout.create_checkout(
        order_id="ord-legacy",
        amount_eur=1200,
        label="Landing Premium",
        success_url="https://genesis-ai-engine.vercel.app/order/status/ord-legacy?paid=1",
        cancel_url="https://genesis-ai-engine.vercel.app/order/status/ord-legacy",
        currency="eur",
    )
    assert out["checkout_url"].startswith("https://checkout.stripe.com/")
    assert "vercel.app" not in captured["data"]["success_url"]
    assert captured["data"]["success_url"].startswith("https://beta.genesis-ai-engine.com/")
    assert "vercel.app" not in captured["data"]["cancel_url"]
