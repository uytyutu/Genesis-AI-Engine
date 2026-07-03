"""Revenue Pipeline v1 — payment → auto production → notifications."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.integration.finance_service import FinanceService
from app.integration.owner_notification_service import OwnerNotificationService
from app.integration.payment_checkout_service import PaymentCheckoutService


class RevenuePipelineService:
    def __init__(
        self,
        sales: object,
        finance: FinanceService,
        checkout: PaymentCheckoutService,
        notifications: OwnerNotificationService,
    ) -> None:
        self._sales = sales
        self._finance = finance
        self._checkout = checkout
        self._notifications = notifications

    def payment_status(self) -> dict:
        provider = self._checkout.provider()
        return {
            "configured": self._checkout.is_configured(),
            "provider": provider,
            "provider_label": {
                "stripe": "Stripe",
                "sandbox": "Sandbox (только тест)",
            }.get(str(provider), "Не подключено"),
            "sandbox": provider == "sandbox",
        }

    def begin_checkout(self, order_id: str, *, success_url: str, cancel_url: str) -> dict:
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") not in ("awaiting_payment", "pending_confirmation"):
            raise ValueError("invalid_status")
        if not self._checkout.is_configured():
            raise ValueError("payment_not_configured")

        label = f"{order['package_name']} — {order['business_name']}"
        session = self._checkout.create_checkout(
            order_id=order_id,
            amount_eur=float(order["price_eur"]),
            label=label,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        order["status"] = "awaiting_payment"
        order["status_label"] = "Ожидает оплаты"
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
        parsed = self._checkout.verify_stripe_webhook(payload, signature)
        if not parsed:
            raise ValueError("invalid_webhook")
        return self._apply_payment(
            order_id=parsed["order_id"],
            amount_eur=parsed["amount_eur"],
            provider="stripe",
            sender=parsed.get("sender"),
            external_id=str(parsed.get("session_id", "")),
        )

    def confirm_stripe_payment(self, order_id: str) -> dict:
        """Confirm payment after Stripe redirect when webhook has not arrived yet."""
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") in ("paid", "in_production", "ready", "delivered"):
            return {
                "ok": True,
                "already_processed": True,
                "order": self._sales.public_status(order_id),
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
    ) -> dict:
        order = self._sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") in ("paid", "in_production", "ready", "delivered"):
            return {
                "ok": True,
                "already_processed": True,
                "order": self._sales.public_status(order_id),
            }

        expected = float(order["price_eur"])
        paid = expected if amount_eur is None else round(float(amount_eur), 2)
        if abs(paid - expected) > 0.01:
            raise ValueError("amount_mismatch")

        label = f"Заказ {order_id}: {order['business_name']}"
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
        order["status_label"] = "Оплачено"
        order["paid_at"] = now.isoformat()
        order["payment_provider"] = provider
        order["payment_external_id"] = external_id
        order["updated_at"] = now.isoformat()
        eta_hours = {"basic": 48, "business": 72, "premium": 120}.get(
            str(order.get("package_id", "basic")), 48
        )
        eta = now + timedelta(hours=eta_hours)
        status_path = f"/order/status/{order_id}"
        order["estimated_delivery_at"] = eta.isoformat()
        order["estimated_hours"] = eta_hours
        order["client_status_message"] = (
            "Спасибо за оплату! Мы начали работу над вашим сайтом. "
            "Следите за прогрессом на странице статуса заказа."
        )
        order["client_receipt_text"] = (
            f"Здравствуйте!\n\n"
            f"Спасибо за заказ «{order['business_name']}».\n\n"
            f"Заказ № {order_id}\n"
            f"Пакет: {order['package_name']} — {paid:.0f} €\n"
            f"Статус: Оплачено\n"
            f"Ориентировочный срок: {eta_hours} часов\n\n"
            f"Отслеживать заказ: {status_path}\n\n"
            f"С уважением,\nGenesis"
        )
        self._sales._save_order(order)

        production = self._sales.start_production(order_id)
        product_id = production.get("product_id")

        self._notifications.notify(
            title="Новая оплата",
            message=(
                f"🟢 {order['business_name']} — {paid:.0f} € ({order['package_name']}). "
                f"Производство запущено автоматически."
            ),
            order_id=order_id,
        )

        return {
            "ok": True,
            "order_id": order_id,
            "amount_eur": paid,
            "product_id": product_id,
            "client_message": order["client_status_message"],
            "order": self._sales.public_status(order_id),
        }
