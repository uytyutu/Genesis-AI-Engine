"""Revenue Pipeline v1 — payment → auto production → notifications."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path

from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.receipt_email_service import ReceiptEmailService
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.payment_checkout_service import PaymentCheckoutService

_SUPPORT_EMAIL = "hello@genesis-ai-engine.com"
_RECEIPT_TEMPLATE = (
    Path(__file__).resolve().parents[4] / "docs" / "support_templates" / "01_receipt_de.txt"
)


def _support_email() -> str:
    return (
        os.getenv("GENESIS_SUPPORT_EMAIL", "").strip()
        or os.getenv("GENESIS_OWNER_NOTIFY_EMAIL", "").strip()
        or _SUPPORT_EMAIL
    )


def _render_client_receipt(*, order: dict, status_path: str, paid: float) -> str:
    """DE receipt for the buyer — prefer docs/support_templates/01_receipt_de.txt."""
    from app.factory.motion_brief import receipt_motion_line

    name = str(order.get("business_name") or "").strip() or "Kunde"
    order_id = str(order.get("order_id") or "")
    package = str(order.get("package_name") or order.get("package_id") or "")
    amount = str(order.get("price_label") or f"{paid:.0f} {order.get('symbol') or '€'}".strip())
    support = _support_email()
    motion_line = receipt_motion_line(str(order.get("motion_level") or "none"))
    pref = str(order.get("deployment_preference") or "unset")
    if pref == "zip_only":
        delivery_line = "Lieferung: ZIP Only — Selbst-Veröffentlichung."
    elif pref == "assisted":
        delivery_line = (
            "Lieferung: Assisted Deployment — Hilfe bei der Veröffentlichung "
            "(keine Hosting-Passwörter in Virtus)."
        )
    else:
        delivery_line = ""
    tpl_path = _RECEIPT_TEMPLATE
    if tpl_path.is_file():
        text = tpl_path.read_text(encoding="utf-8")
        rendered = (
            text.replace("{{name}}", name)
            .replace("{{order_id}}", order_id)
            .replace("{{package}}", package)
            .replace("{{amount}}", amount)
            .replace("{{status_url}}", status_path)
            .replace("{{support_email}}", support)
            .replace("{{motion_line}}", motion_line)
            .replace("{{delivery_line}}", delivery_line)
        )
        # Drop blank placeholder lines when classic none / unset preference
        if not motion_line and not delivery_line:
            rendered = rendered.replace("\n\nWas als Nächstes", "\nWas als Nächstes")
        elif not motion_line:
            rendered = rendered.replace("\n\n" + delivery_line, "\n" + delivery_line)
        elif not delivery_line:
            rendered = rendered.replace(motion_line + "\n\nWas", motion_line + "\nWas")
        while "\n\n\n" in rendered:
            rendered = rendered.replace("\n\n\n", "\n\n")
        return rendered
    price_display = str(order.get("price_label") or f"{paid:.0f} €")
    motion_extra = f"{motion_line}\n" if motion_line else ""
    delivery_extra = f"{delivery_line}\n" if delivery_line else ""
    return (
        f"Guten Tag,\n\n"
        f"vielen Dank für Ihre Bestellung «{name}».\n\n"
        f"Bestellnr. {order_id}\n"
        f"Paket: {package} — {price_display}\n"
        f"{motion_extra}"
        f"{delivery_extra}"
        f"Status: Bezahlt\n\n"
        f"Status verfolgen: {status_path}\n\n"
        f"Mit freundlichen Grüßen\n{BRAND_NAME}\n{support}"
    )


class RevenuePipelineService:
    def __init__(
        self,
        sales: object,
        finance: FinanceService,
        checkout: PaymentCheckoutService,
        notifications: OwnerNotificationService,
        receipt_email: ReceiptEmailService | None = None,
    ) -> None:
        self._sales = sales
        self._finance = finance
        self._checkout = checkout
        self._notifications = notifications
        self._receipt_email = receipt_email or ReceiptEmailService()

    def payment_status(self) -> dict:
        from app.integration.public_site_url import configured_public_base

        from app.integration.payment_checkout_service import _resolve_stripe_secret

        provider = self._checkout.provider()
        stripe_live = provider == "stripe" and self._checkout.is_live_mode()
        sk = _resolve_stripe_secret()
        pk = (
            os.getenv("STRIPE_PUBLISHABLE_KEY", "").strip()
            or os.getenv("STRIPE_PUBLISHABLE_KEY_LIVE", "").strip()
        )
        return {
            "configured": self._checkout.is_configured(),
            "provider": provider,
            "provider_label": {
                "stripe": "Stripe (live)" if stripe_live else "Stripe (test)",
                "sandbox": "Sandbox (только тест)",
            }.get(str(provider), "Не подключено"),
            "sandbox": provider == "sandbox",
            "stripe_ready": provider == "stripe",
            "live_mode": stripe_live,
            "webhook_configured": self._checkout.has_webhook_secret(),
            "stripe_test_mode": sk.startswith("sk_test_"),
            "publishable_key_configured": bool(pk),
            "secret_key_configured": bool(sk),
            "public_url": configured_public_base(),
        }

    def email_status(self) -> dict:
        return self._receipt_email.configuration_status()

    def begin_checkout(self, order_id: str, *, success_url: str, cancel_url: str) -> dict:
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") not in ("awaiting_payment", "pending_confirmation"):
            raise ValueError("invalid_status")
        if not self._checkout.is_configured():
            raise ValueError("payment_not_configured")

        label = f"{order['package_name']} — {order['business_name']}"
        currency = str(order.get("currency") or "EUR").lower()
        session = self._checkout.create_checkout(
            order_id=order_id,
            amount_eur=float(order["price_eur"]),
            label=label,
            success_url=success_url,
            cancel_url=cancel_url,
            currency=currency,
            motion_level=str(order.get("motion_level") or "none"),
            market_code=str(order.get("market_code") or "DE"),
        )
        order["status"] = "awaiting_payment"
        order["status_label"] = "Wartet auf Zahlung"
        order["checkout_session_id"] = session.get("session_id")
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._sales._save_order(order)
        return {"ok": True, "order_id": order_id, **session}

    def complete_sandbox_payment(self, order_id: str, token: str | None = None) -> dict:
        if self._checkout.provider() != "sandbox":
            raise ValueError("sandbox_only")
        return self._apply_payment(
            order_id=order_id,
            amount_eur=None,
            provider="sandbox",
            sender="sandbox@test",
            external_id=f"sandbox-{order_id}",
        )

    def handle_stripe_webhook(self, payload: bytes, signature: str) -> dict:
        from app.services.finance_center import (
            StripeWebhookCriticalError,
            StripeWebhookError,
            handle_stripe_webhook_event,
        )

        try:
            return handle_stripe_webhook_event(payload, signature, self)
        except StripeWebhookCriticalError as exc:
            raise ValueError(str(exc)) from exc
        except StripeWebhookError as exc:
            raise ValueError("invalid_webhook") from exc

    def apply_stripe_checkout_payment(
        self,
        *,
        order_id: str,
        amount_eur: float,
        session_id: str,
        payment_intent: str = "",
        sender: str | None = None,
        currency: str | None = None,
    ) -> dict:
        """Confirm order after verified checkout.session.completed webhook."""
        external_id = session_id or payment_intent
        result = self._apply_payment(
            order_id=order_id,
            amount_eur=amount_eur,
            currency=currency,
            provider="stripe",
            sender=sender,
            external_id=external_id,
        )
        if payment_intent:
            order = self._sales.get_order(order_id)
            if order is not None:
                order["stripe_payment_intent"] = payment_intent
                self._sales._save_order(order)
        return result

    def confirm_stripe_payment(self, order_id: str) -> dict:
        """Confirm payment after Stripe redirect when webhook has not arrived yet."""
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") in ("paid", "in_production", "ready", "delivered"):
            self._backfill_email_from_checkout(order)
            email_result = self._send_receipt_if_needed(order)
            return {
                "ok": True,
                "already_processed": True,
                "order": self._sales.public_status(order_id),
                "receipt_email": email_result,
            }
        if self._checkout.provider() != "stripe":
            raise ValueError("stripe_only")
        session_id = str(order.get("checkout_session_id") or "").strip()
        if not session_id:
            raise ValueError("no_checkout_session")
        parsed = self._checkout.retrieve_paid_session(session_id)
        if not parsed:
            raise ValueError("payment_not_confirmed")
        if parsed["order_id"] != order_id:
            raise ValueError("order_mismatch")
        return self._apply_payment(
            order_id=order_id,
            amount_eur=parsed["amount_eur"],
            currency=parsed.get("currency"),
            provider="stripe",
            sender=parsed.get("sender"),
            external_id=str(parsed.get("session_id", "")),
        )

    def _apply_payment(
        self,
        *,
        order_id: str,
        amount_eur: float | None,
        provider: str,
        sender: str | None,
        external_id: str,
        currency: str | None = None,
    ) -> dict:
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") in ("paid", "in_production", "ready", "delivered"):
            self._ensure_order_email(order, sender)
            self._backfill_email_from_checkout(order)
            email_result = self._send_receipt_if_needed(order)
            return {
                "ok": True,
                "already_processed": True,
                "order": self._sales.public_status(order_id),
                "receipt_email": email_result,
            }

        expected = float(order["price_eur"])
        paid = expected if amount_eur is None else round(float(amount_eur), 2)
        if abs(paid - expected) > 0.01:
            raise ValueError("amount_mismatch")

        if currency is not None:
            expected_cur = str(order.get("currency") or "EUR").strip().lower()
            paid_cur = str(currency).strip().lower()
            if paid_cur != expected_cur:
                raise ValueError("currency_mismatch")

        label = f"Bestellung {order_id}: {order['business_name']}"
        self._finance.credit_order_payment(
            paid,
            label,
            provider=provider,
            order_id=order_id,
            sender=sender,
            external_id=external_id,
        )

        now = datetime.now(timezone.utc)
        order["status"] = "paid"
        order["status_label"] = "Bezahlt"
        order["paid_at"] = now.isoformat()
        order["payment_provider"] = provider
        order["payment_external_id"] = external_id
        order["updated_at"] = now.isoformat()
        # Path A Factory builds in minutes — not multi-day handoff.
        from app.factory.market_delivery import (
            PATH_A_ETA_MINUTES,
            client_post_pay_message,
            client_status_label,
            render_client_receipt_text,
        )

        eta_minutes = PATH_A_ETA_MINUTES
        eta = now + timedelta(minutes=eta_minutes)
        status_path = f"/order/status/{order_id}"
        price_display = str(order.get("price_label") or f"{paid:.0f} €")
        order["estimated_delivery_at"] = eta.isoformat()
        order["estimated_hours"] = max(1, int(round(eta_minutes / 60)))  # legacy field
        order["estimated_minutes"] = eta_minutes
        market = str(order.get("market_code") or "DE")
        order["status_label"] = client_status_label("paid", market)
        from app.factory.motion_brief import normalize_motion_level, receipt_motion_line

        motion = normalize_motion_level(str(order.get("motion_level") or "none"))
        motion_note = receipt_motion_line(motion)
        status_extra = f" {motion_note}" if motion_note else ""
        order["client_status_message"] = (
            client_post_pay_message("paid", market, download_ready=False) + status_extra
        )
        order["client_receipt_text"] = render_client_receipt_text(
            order=order, status_path=status_path, paid=paid
        )
        self._sales._save_order(order)

        production = self._sales.start_production(order_id)
        product_id = production.get("product_id")
        price_display = str(order.get("price_label") or f"{paid:.0f} €")

        self._notifications.notify(
            title="Neue Zahlung",
            message=(
                f"🟢 {order['business_name']} — {price_display} ({order['package_name']}). "
                f"Produktion automatisch gestartet."
            ),
            order_id=order_id,
        )

        order = self._sales.get_order(order_id) or order
        self._ensure_order_email(order, sender)
        self._backfill_email_from_checkout(order)
        email_result = self._send_receipt_if_needed(order)
        owner_mail = self._receipt_email.send_owner_payment_alert(
            order=order, support_email=_support_email()
        )
        order["owner_payment_alert"] = owner_mail
        self._sales._save_order(order)

        return {
            "ok": True,
            "order_id": order_id,
            "amount_eur": paid,
            "product_id": product_id,
            "client_message": order["client_status_message"],
            "order": self._sales.public_status(order_id),
            "receipt_email": email_result,
            "owner_payment_alert": owner_mail,
        }

    def _ensure_order_email(self, order: dict, sender: str | None) -> None:
        if str(order.get("email") or "").strip():
            return
        stripe_email = str(sender or "").strip()
        if not stripe_email or "@" not in stripe_email:
            return
        order["email"] = stripe_email
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._sales._save_order(order)

    def _backfill_email_from_checkout(self, order: dict) -> None:
        if str(order.get("email") or "").strip():
            return
        session_id = str(order.get("checkout_session_id") or "").strip()
        if not session_id or self._checkout.provider() != "stripe":
            return
        parsed = self._checkout.retrieve_paid_session(session_id)
        if not parsed:
            return
        self._ensure_order_email(order, parsed.get("sender"))

    def _send_receipt_if_needed(self, order: dict) -> dict:
        if order.get("receipt_email_sent"):
            return dict(order.get("receipt_email_delivery") or {"ok": True, "reason": "already_sent"})

        receipt_text = str(order.get("client_receipt_text") or "").strip()
        if not receipt_text:
            return {"ok": False, "skipped": True, "reason": "no_receipt_text"}

        result = self._receipt_email.send_order_receipt(order=order, receipt_text=receipt_text)
        order["receipt_email_delivery"] = result
        if result.get("ok"):
            order["receipt_email_sent"] = True
        self._sales._save_order(order)

        if not result.get("ok") and not result.get("skipped"):
            detail = str(result.get("detail") or result.get("reason") or "")
            self._notifications.notify(
                title="Email не отправлен",
                message=(
                    f"Заказ {order.get('order_id')}: не удалось отправить чек. "
                    f"{detail[:180]}"
                ),
                order_id=str(order.get("order_id") or ""),
            )
        elif result.get("skipped") and result.get("reason") == "no_email":
            self._notifications.notify(
                title="Email пропущен",
                message=(
                    f"Заказ {order.get('order_id')}: нет email клиента в заказе и в Stripe."
                ),
                order_id=str(order.get("order_id") or ""),
            )

        return result
