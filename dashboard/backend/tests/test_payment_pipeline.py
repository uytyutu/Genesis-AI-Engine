"""Payment pipeline — sandbox Blind PASS (Mission 1 Stripe sprint)."""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
from pathlib import Path

import pytest

from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService
from app.integration.revenue_pipeline_service import RevenuePipelineService
from app.integration.sales_order_service import SalesOrderService


class _Factory:
    def submit(self, _intent):
        return {"product_id": "prod-test-1"}


def _pipeline(tmp_path: Path) -> tuple[SalesOrderService, RevenuePipelineService]:
    sales = SalesOrderService(tmp_path, _Factory())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)
    return sales, revenue


def _stripe_signature(payload: bytes, secret: str) -> str:
    ts = int(time.time())
    signed = f"{ts}.".encode() + payload
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    return f"t={ts},v1={sig}"


@pytest.fixture
def sandbox_env(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")


def test_sandbox_checkout_to_paid_and_production(tmp_path: Path, sandbox_env):
    sales, revenue = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Test Cafe",
            "description": "Кафе в центре",
            "email": "owner@test.com",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    order_id = created["order_id"]

    checkout = revenue.begin_checkout(
        order_id,
        success_url="http://localhost:3000/order/status",
        cancel_url="http://localhost:3000/order",
    )
    assert checkout["provider"] == "sandbox"
    assert "checkout_url" in checkout

    result = revenue.complete_sandbox_payment(order_id)
    assert result["ok"] is True
    assert result.get("already_processed") is not True

    status = sales.public_status(order_id)
    assert status["status"] == "in_production"
    assert status.get("product_id") == "prod-test-1"
    assert status["paid"] is True

    order = sales.get_order(order_id)
    assert order is not None
    receipt = str(order.get("client_receipt_text") or "")
    assert "Bestellnummer" in receipt or "Bestellnr" in receipt or "Zahlung" in receipt
    assert "Agency CSS-Motion" not in receipt  # classic none by default
    assert "Zahlung erhalten" in receipt or "vielen Dank" in receipt
    assert order_id in receipt
    assert "/order/status/" in receipt

    notes = OwnerNotificationService(tmp_path).list_recent(5)
    assert any(n.get("title") == "Neue Zahlung" for n in notes)
    assert result.get("owner_payment_alert", {}).get("reason") in (
        "not_configured",
        None,
    ) or result.get("owner_payment_alert", {}).get("ok") is True or result.get(
        "owner_payment_alert", {}
    ).get("skipped") is True


def test_stripe_webhook_signature_required(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    checkout = PaymentCheckoutService(tmp_path)

    payload = json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_test",
                    "amount_total": 35000,
                    "metadata": {"order_id": "ord-abc"},
                    "customer_details": {"email": "pay@test.com"},
                }
            },
        }
    ).encode()

    assert checkout.verify_stripe_webhook(payload, "") is None

    sig = _stripe_signature(payload, "whsec_test")
    parsed = checkout.verify_stripe_webhook(payload, sig)
    assert parsed is not None
    assert parsed["order_id"] == "ord-abc"
    assert parsed["amount_eur"] == 350.0


def test_stripe_webhook_rejects_without_secret(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("STRIPE_WEBHOOK_SECRET", raising=False)
    checkout = PaymentCheckoutService(tmp_path)
    payload = json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_unsigned",
                    "amount_total": 35000,
                    "metadata": {"order_id": "ord-x"},
                }
            },
        }
    ).encode()
    assert checkout.verify_stripe_webhook(payload, "") is None
    assert checkout.verify_stripe_webhook(payload, "t=1,v1=dead") is None


def test_farm_auto_prepare_outreach_opt_in(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.integration.micro_farm_service import MicroFarmService
    from app.integration.opportunity_service import OpportunityService

    farm = MicroFarmService(
        OpportunityService(tmp_path),
        FinanceService(tmp_path),
        memory_dir=tmp_path,
    )
    state: dict = {}
    monkeypatch.delenv("FARM_AUTO_PREPARE_OUTREACH", raising=False)
    assert farm._maybe_auto_prepare_outreach(state) is None

    monkeypatch.setenv("FARM_AUTO_PREPARE_OUTREACH", "1")

    class _Acq:
        def auto_prepare_discovery_leads(self, limit=2):
            return {"prepared": 1, "limit": limit}

    class _Ctx:
        acquisition = _Acq()

    monkeypatch.setattr(
        "app.integration.context.get_integration",
        lambda: _Ctx(),
    )
    result = farm._maybe_auto_prepare_outreach(state)
    assert result is not None
    assert result.get("prepared") == 1
    assert state.get("last_auto_outreach_at")


def test_stripe_webhook_confirms_order(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)

    sales, revenue = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Webhook Cafe",
            "description": "Test",
            "email": "webhook@test.com",
            "package_id": "basic",
            "city": "Berlin",
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    order["status"] = "awaiting_payment"
    order["price_eur"] = 350.0
    sales._save_order(order)

    payload = json.dumps(
        {
            "type": "checkout.session.completed",
            "data": {
                "object": {
                    "id": "cs_live_test",
                    "payment_intent": "pi_live_test",
                    "amount_total": 35000,
                    "metadata": {"order_id": order_id},
                    "customer_details": {"email": "webhook@test.com"},
                }
            },
        }
    ).encode()
    sig = _stripe_signature(payload, "whsec_test")

    from app.services.finance_center import handle_stripe_webhook_event

    result = handle_stripe_webhook_event(payload, sig, revenue)
    assert result["status"] == "success"
    assert result["ok"] is True

    updated = sales.get_order(order_id)
    assert updated["status"] in ("paid", "in_production")
    assert updated.get("paid_at")

    settlements_path = tmp_path / "finance_settlements.jsonl"
    assert settlements_path.is_file()
    rows = [json.loads(line) for line in settlements_path.read_text(encoding="utf-8").splitlines()]
    assert any(r.get("order_id") == order_id and r.get("amount_eur") == 350.0 for r in rows)


def test_payment_status_stripe_test_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_abc")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_test_xyz")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_test")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)

    sales = SalesOrderService(tmp_path, _Factory())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)

    status = revenue.payment_status()
    assert status["provider"] == "stripe"
    assert status["sandbox"] is False
    assert status["stripe_test_mode"] is True
    assert status["publishable_key_configured"] is True
    assert status["secret_key_configured"] is True
    assert status["webhook_configured"] is True


def test_payment_status_live_mode_fields(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_live_abc")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_live_xyz")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_live")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)

    sales = SalesOrderService(tmp_path, _Factory())
    checkout = PaymentCheckoutService(tmp_path)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue = RevenuePipelineService(sales, finance, checkout, notifications)

    status = revenue.payment_status()
    assert status["live_mode"] is True
    assert status["stripe_test_mode"] is False
    assert status["provider_label"] == "Stripe (live)"


def test_begin_checkout_passes_order_currency(tmp_path: Path, sandbox_env, monkeypatch: pytest.MonkeyPatch):
    sales, revenue = _pipeline(tmp_path)
    created = sales.create_order(
        {
            "business_name": "Krakow Shop",
            "description": "Sklep",
            "email": "pl@test.com",
            "package_id": "basic",
            "city": "Kraków",
        }
    )
    order = sales.get_order(created["order_id"])
    assert order["currency"] == "PLN"

    captured: dict = {}

    def _fake_stripe(**kwargs):
        captured.update(kwargs)
        return {"provider": "stripe", "checkout_url": "https://stripe.test", "session_id": "cs_x"}

    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_fake")
    monkeypatch.delenv("GENESIS_PAYMENT_SANDBOX", raising=False)
    checkout_svc = PaymentCheckoutService(tmp_path)
    monkeypatch.setattr(checkout_svc, "_stripe_checkout", _fake_stripe)
    finance = FinanceService(tmp_path)
    notifications = OwnerNotificationService(tmp_path)
    revenue2 = RevenuePipelineService(sales, finance, checkout_svc, notifications)

    revenue2.begin_checkout(
        created["order_id"],
        success_url="http://localhost:3000/order/status",
        cancel_url="http://localhost:3000/order",
    )
    assert captured.get("currency") == "pln"
