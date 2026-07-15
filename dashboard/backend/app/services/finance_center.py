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
    order_id = str((session.get("metadata") or {}).get("order_id") or "").strip()

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

    sender = str(session.get("customer_details", {}).get("email") or "")
    logger.info(
        "stripe webhook checkout.session.completed — session=%s payment_intent=%s order=%s amount=%.2f",
        session_id,
        payment_intent,
        order_id,
        amount,
    )

    payment_result = revenue.apply_stripe_checkout_payment(
        order_id=order_id,
        amount_eur=amount,
        session_id=session_id,
        payment_intent=payment_intent,
        sender=sender,
    )
    return {"status": "success", **payment_result}
