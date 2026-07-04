"""Client receipt email after successful payment (Resend API v1)."""

from __future__ import annotations

import os

import httpx


class ReceiptEmailService:
    def configuration_status(self) -> dict:
        has_key = bool(os.getenv("RESEND_API_KEY", "").strip())
        has_from = bool(os.getenv("GENESIS_EMAIL_FROM", "").strip())
        return {
            "configured": has_key and has_from,
            "has_api_key": has_key,
            "has_from_address": has_from,
        }

    def send_order_receipt(self, *, order: dict, receipt_text: str) -> dict:
        to = str(order.get("email") or "").strip()
        if not to:
            return {"ok": False, "skipped": True, "reason": "no_email"}

        api_key = os.getenv("RESEND_API_KEY", "").strip()
        from_addr = os.getenv("GENESIS_EMAIL_FROM", "").strip()
        if not api_key or not from_addr:
            return {"ok": False, "skipped": True, "reason": "not_configured"}

        order_id = str(order.get("order_id", ""))
        public_url = os.getenv("GENESIS_PUBLIC_URL", "").rstrip("/")
        body = receipt_text
        if public_url and order_id:
            body = body.replace(
                f"/order/status/{order_id}",
                f"{public_url}/order/status/{order_id}",
            )

        business = str(order.get("business_name") or "заказ")
        subject = f"Подтверждение оплаты — {business} (№ {order_id})"

        payload = {
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "text": body,
        }

        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers={"Authorization": f"Bearer {api_key}"},
            )
        if res.status_code >= 400:
            return {
                "ok": False,
                "skipped": False,
                "reason": f"resend_error:{res.status_code}",
                "detail": res.text[:200],
            }
        data = res.json()
        return {"ok": True, "email_id": data.get("id"), "to": to}
