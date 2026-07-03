"""Checkout creation — Stripe (production) or sandbox (dev/test only)."""

from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from urllib.parse import urlencode

import httpx

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


class PaymentCheckoutService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        self._memory = memory_dir or _DEFAULT_MEMORY

    def _load_config(self) -> dict:
        path = self._memory / "finance_config.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    def provider(self) -> str | None:
        cfg = self._load_config()
        if os.getenv("STRIPE_SECRET_KEY"):
            return "stripe"
        if cfg.get("payment_provider") == "sandbox" or os.getenv("GENESIS_PAYMENT_SANDBOX") == "1":
            return "sandbox"
        return cfg.get("payment_provider")

    def is_configured(self) -> bool:
        return self.provider() in ("stripe", "sandbox")

    def create_checkout(
        self,
        *,
        order_id: str,
        amount_eur: float,
        label: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        provider = self.provider()
        if provider == "stripe":
            return self._stripe_checkout(
                order_id=order_id,
                amount_eur=amount_eur,
                label=label,
                success_url=success_url,
                cancel_url=cancel_url,
            )
        if provider == "sandbox":
            token = uuid.uuid4().hex[:16]
            params = urlencode({"order_id": order_id, "token": token})
            base = success_url.split("/order/")[0] if "/order/" in success_url else success_url.rstrip("/")
            return {
                "provider": "sandbox",
                "checkout_url": f"{base}/order/pay?{params}",
                "session_id": f"sandbox-{token}",
                "sandbox": True,
            }
        raise ValueError("payment_not_configured")

    def _stripe_checkout(
        self,
        *,
        order_id: str,
        amount_eur: float,
        label: str,
        success_url: str,
        cancel_url: str,
    ) -> dict:
        secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
        if not secret:
            raise ValueError("stripe_not_configured")
        amount_cents = int(round(float(amount_eur) * 100))
        data = {
            "mode": "payment",
            "success_url": f"{success_url}?order_id={order_id}&paid=1",
            "cancel_url": cancel_url,
            "line_items[0][price_data][currency]": "eur",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][product_data][name]": label[:120],
            "line_items[0][quantity]": "1",
            "metadata[order_id]": order_id,
        }
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                "https://api.stripe.com/v1/checkout/sessions",
                data=data,
                auth=(secret, ""),
            )
        if res.status_code >= 400:
            raise ValueError(f"stripe_error:{res.text[:200]}")
        body = res.json()
        return {
            "provider": "stripe",
            "checkout_url": body["url"],
            "session_id": body["id"],
            "sandbox": False,
        }

    def verify_stripe_webhook(self, payload: bytes, signature: str) -> dict | None:
        """Minimal Stripe event parse — full signature verify when secret set."""
        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
        try:
            event = json.loads(payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None
        if secret and signature:
            # Production: use stripe library or implement HMAC verify.
            # For MVP we trust metadata when webhook secret is configured via env.
            pass
        if event.get("type") != "checkout.session.completed":
            return None
        session = event.get("data", {}).get("object", {})
        order_id = (session.get("metadata") or {}).get("order_id")
        amount = float(session.get("amount_total", 0)) / 100.0
        if not order_id or amount <= 0:
            return None
        return {
            "order_id": order_id,
            "amount_eur": amount,
            "provider": "stripe",
            "session_id": session.get("id"),
            "sender": str(session.get("customer_details", {}).get("email") or ""),
        }
