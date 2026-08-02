"""Stripe webhook handling — verify, settle, confirm orders."""

from __future__ import annotations

import logging
import os
from typing import Any

import stripe

from app.integration.revenue_pipeline_service import RevenuePipelineService

logger = logging.getLogger(__name__)


class StripeWebhookError(Exception):
    """Invalid signature or malformed Stripe webhook payload."""


class StripeWebhookCriticalError(Exception):
    """Verified event missing required metadata (e.g. order_id)."""


def handle_stripe_webhook_event(
    payload: bytes,
    signature: str,
    revenue: RevenuePipelineService,
) -> dict[str, Any]:
    """Verify Stripe webhook and confirm order on checkout.session.completed."""
    secret = os.getenv("STRIPE_WEBHOOK_SECRET", "").strip()
    if not secret:
        logger.error("stripe webhook: STRIPE_WEBHOOK_SECRET not configured")
        raise StripeWebhookError("webhook_secret_missing")

    try:
        event = stripe.Webhook.construct_event(payload, signature, secret)
    except stripe.error.SignatureVerificationError as exc:
        logger.error("stripe webhook: signature verification failed — %s", exc)
        raise StripeWebhookError("invalid_signature") from exc
    except ValueError as exc:
        logger.error("stripe webhook: invalid payload — %s", exc)
        raise StripeWebhookError("invalid_payload") from exc

    event_type = str(event.get("type") or "")
    if event_type != "checkout.session.completed":
        logger.info("stripe webhook: ignored event type %s", event_type)
        return {"status": "ignored", "event_type": event_type}

    session = event.get("data", {}).get("object", {}) or {}
    session_id = str(session.get("id") or "")
    payment_intent = str(session.get("payment_intent") or "")
    meta = session.get("metadata") or {}
    order_id = str(meta.get("order_id") or "").strip()
    product = str(meta.get("product") or "").strip()

    if not order_id:
        logger.critical(
            "stripe webhook checkout.session.completed missing order_id — session=%s payment_intent=%s",
            session_id,
            payment_intent,
        )
        raise StripeWebhookCriticalError("missing_order_id")

    amount = float(session.get("amount_total", 0)) / 100.0
    if amount <= 0:
        logger.critical(
            "stripe webhook checkout.session.completed invalid amount — session=%s order=%s",
            session_id,
            order_id,
        )
        raise StripeWebhookCriticalError("invalid_amount")

    currency = str(session.get("currency") or "eur").strip().lower() or "eur"
    sender = str(session.get("customer_details", {}).get("email") or "")
    logger.info(
        "stripe webhook checkout.session.completed — session=%s payment_intent=%s order=%s amount=%.2f currency=%s product=%s",
        session_id,
        payment_intent,
        order_id,
        amount,
        currency,
        product or "-",
    )

    # Platform API packages use synthetic api_* order ids — not Sales orders.
    if product == "commercial_api_package" or order_id.startswith("api_"):
        from pathlib import Path

        from app.commercial_api.platform_billing import PlatformApiBilling

        memory = getattr(revenue, "_memory", None) or getattr(
            getattr(revenue, "_sales", None), "_memory", None
        )
        if memory is None:
            mem_env = os.getenv("GENESIS_MEMORY_DIR", "").strip()
            memory = (
                Path(mem_env)
                if mem_env
                else Path(__file__).resolve().parent.parent / "memory"
            )
        package_id = str(meta.get("package_id") or "").strip()
        if not package_id and order_id.startswith("api_"):
            parts = order_id.split("_")
            package_id = parts[1] if len(parts) >= 2 else ""
        email = str(meta.get("customer_email") or sender or "").strip()
        fulfilled = PlatformApiBilling(Path(memory)).fulfill_package_payment(
            package_id=package_id,
            customer_email=email,
            amount_eur=amount,
            session_id=session_id,
            payment_intent=payment_intent,
            order_id=order_id,
            sender=email,
        )
        if not fulfilled.get("ok"):
            logger.error(
                "platform api fulfill failed — session=%s reason=%s",
                session_id,
                fulfilled.get("reason"),
            )
            raise StripeWebhookCriticalError(
                str(fulfilled.get("reason") or "platform_api_fulfill_failed")
            )
        return {
            "status": "success",
            "product": "commercial_api_package",
            "package_id": package_id,
            "key_id": fulfilled.get("key_id"),
            "already_processed": bool(fulfilled.get("already_processed")),
            "order_id": order_id,
        }

    payment_result = revenue.apply_stripe_checkout_payment(
        order_id=order_id,
        amount_eur=amount,
        currency=currency,
        session_id=session_id,
        payment_intent=payment_intent,
        sender=sender,
    )
    return {"status": "success", **payment_result}
