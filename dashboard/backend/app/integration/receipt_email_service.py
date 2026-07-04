"""Client transactional emails (Resend API v1)."""

from __future__ import annotations

import html
import os

import httpx


def _public_url(path: str) -> str:
    base = os.getenv("GENESIS_PUBLIC_URL", "").rstrip("/")
    return f"{base}{path}" if base else path


def _html_email(
    *,
    title: str,
    intro: str,
    rows: list[tuple[str, str]],
    cta_href: str | None = None,
    cta_label: str | None = None,
) -> str:
    row_html = "".join(
        f'<tr><td style="padding:8px 12px 8px 0;color:#8b8b9a;vertical-align:top">{html.escape(k)}</td>'
        f'<td style="padding:8px 0;color:#ececf1">{html.escape(v)}</td></tr>'
        for k, v in rows
    )
    cta = ""
    if cta_href and cta_label:
        cta = (
            f'<p style="margin:28px 0 0">'
            f'<a href="{html.escape(cta_href)}" style="display:inline-block;background:#5b8def;color:#fff;'
            f'text-decoration:none;padding:14px 28px;border-radius:12px;font-weight:600">'
            f"{html.escape(cta_label)}</a></p>"
        )
    return f"""<!DOCTYPE html>
<html lang="ru">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;background:#050508;font-family:system-ui,-apple-system,sans-serif">
<table width="100%" cellpadding="0" cellspacing="0" style="background:#050508;padding:32px 16px">
<tr><td align="center">
<table width="100%" style="max-width:520px;background:#111118;border:1px solid #27272f;border-radius:16px">
<tr><td style="padding:32px 28px">
<div style="width:40px;height:40px;border-radius:10px;background:linear-gradient(135deg,#5b8def,#4f46e5);
color:#fff;font-weight:700;font-size:16px;line-height:40px;text-align:center">G</div>
<h1 style="margin:20px 0 0;color:#ececf1;font-size:22px">{html.escape(title)}</h1>
<p style="margin:12px 0 0;color:#8b8b9a;font-size:15px;line-height:1.5">{html.escape(intro)}</p>
<table style="margin:24px 0 0;width:100%;font-size:14px">{row_html}</table>
{cta}
<p style="margin:32px 0 0;font-size:12px;color:#52525b">Genesis AI Engine · hello@genesis-ai-engine.com</p>
</td></tr></table>
</td></tr></table>
</body></html>"""


class ReceiptEmailService:
    def configuration_status(self) -> dict:
        has_key = bool(os.getenv("RESEND_API_KEY", "").strip())
        has_from = bool(os.getenv("GENESIS_EMAIL_FROM", "").strip())
        return {
            "configured": has_key and has_from,
            "has_api_key": has_key,
            "has_from_address": has_from,
        }

    def send_order_received(self, *, order: dict) -> dict:
        order_id = str(order.get("order_id", ""))
        status_path = f"/order/status/{order_id}"
        rows = [
            ("Заказ", f"№ {order_id}"),
            ("Бизнес", str(order.get("business_name", ""))),
            ("Пакет", f"{order.get('package_name', '')} — {order.get('price_eur', '')} €"),
            ("Статус", "Ожидает оплаты"),
        ]
        text = (
            f"Здравствуйте!\n\n"
            f"Мы получили ваш заказ «{order['business_name']}».\n\n"
            f"Заказ № {order_id}\n"
            f"Пакет: {order['package_name']} — {order['price_eur']} €\n\n"
            f"Оплатите, чтобы мы начали работу:\n{_public_url(status_path)}\n\n"
            f"Статус заказа: {_public_url(status_path)}\n\n"
            f"С уважением,\nGenesis"
        )
        html_body = _html_email(
            title="Заказ получен",
            intro="Спасибо! Оплатите заказ — и мы сразу начнём работу над сайтом.",
            rows=rows,
            cta_href=_public_url(status_path),
            cta_label="Оплатить заказ",
        )
        return self._send(
            to=str(order.get("email") or "").strip(),
            subject=f"Заказ получен — {order.get('business_name', 'Genesis')} (№ {order_id})",
            text=text,
            html=html_body,
        )

    def send_order_receipt(self, *, order: dict, receipt_text: str) -> dict:
        to = str(order.get("email") or "").strip()
        order_id = str(order.get("order_id", ""))
        status_path = f"/order/status/{order_id}"
        status_url = _public_url(status_path)
        body = receipt_text.replace(f"/order/status/{order_id}", status_url)

        eta = order.get("estimated_hours")
        rows = [
            ("Заказ", f"№ {order_id}"),
            ("Пакет", f"{order.get('package_name', '')} — {order.get('price_eur', '')} €"),
            ("Статус", "Оплачено"),
        ]
        if eta:
            rows.append(("Срок", f"~{eta} часов"))
        html_body = _html_email(
            title="Оплата подтверждена",
            intro=str(order.get("client_status_message") or "Спасибо за оплату! Мы начали работу."),
            rows=rows,
            cta_href=status_url,
            cta_label="Статус заказа",
        )
        business = str(order.get("business_name") or "заказ")
        return self._send(
            to=to,
            subject=f"Подтверждение оплаты — {business} (№ {order_id})",
            text=body,
            html=html_body,
        )

    def _send(self, *, to: str, subject: str, text: str, html: str) -> dict:
        if not to:
            return {"ok": False, "skipped": True, "reason": "no_email"}
        api_key = os.getenv("RESEND_API_KEY", "").strip()
        from_addr = os.getenv("GENESIS_EMAIL_FROM", "").strip()
        if not api_key or not from_addr:
            return {"ok": False, "skipped": True, "reason": "not_configured"}

        payload = {
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "text": text,
            "html": html,
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
