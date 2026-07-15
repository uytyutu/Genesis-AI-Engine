"""Client transactional emails (Resend API v1)."""

from __future__ import annotations

import html
import os
from pathlib import Path

import httpx

from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.product_line import project_awaiting_payment_message
from app.legal.service import LegalFoundationService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"


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
    footer_html: str = "",
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
color:#fff;font-weight:700;font-size:16px;line-height:40px;text-align:center">V</div>
<h1 style="margin:20px 0 0;color:#ececf1;font-size:22px">{html.escape(title)}</h1>
<p style="margin:12px 0 0;color:#8b8b9a;font-size:15px;line-height:1.5">{html.escape(intro)}</p>
<table style="margin:24px 0 0;width:100%;font-size:14px">{row_html}</table>
{cta}
{footer_html}
<p style="margin:32px 0 0;font-size:12px;color:#52525b">{BRAND_NAME} · hello@genesis-ai-engine.com</p>
</td></tr></table>
</td></tr></table>
</body></html>"""


class ReceiptEmailService:
    def __init__(self, memory_dir: Path | None = None) -> None:
        raw = os.getenv("GENESIS_MEMORY_DIR", "").strip()
        if memory_dir is not None:
            self._memory = memory_dir
        elif raw:
            self._memory = Path(raw).expanduser()
        else:
            self._memory = _DEFAULT_MEMORY

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
        intro = str(
            order.get("client_status_message")
            or project_awaiting_payment_message(launch_mode=bool(order.get("launch_mode")))
        )
        text = (
            f"Здравствуйте!\n\n"
            f"Мы получили ваш проект «{order['business_name']}».\n\n"
            f"Проект № {order_id}\n"
            f"Сумма: {order['price_eur']} €\n\n"
            f"{intro}\n{_public_url(status_path)}\n\n"
            f"Статус проекта: {_public_url(status_path)}\n\n"
            f"С уважением,\n{BRAND_NAME}"
        )
        html_body = _html_email(
            title="Проект зафиксирован",
            intro=intro,
            rows=rows,
            cta_href=_public_url(status_path),
            cta_label="Оплатить проект",
        )
        return self._send(
            to=str(order.get("email") or "").strip(),
            subject=f"Проект зафиксирован — {order.get('business_name', BRAND_NAME)} (№ {order_id})",
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

    def send_outreach(self, *, to: str, subject: str, text: str) -> dict:
        """CEO-approved cold outreach — Impressum + UWG opt-out footer required."""
        legal = LegalFoundationService(self._memory)
        footer = legal.email_footer_de(include_opt_out=True, for_outreach=True)
        if not footer.get("ready_for_outreach"):
            return {
                "ok": False,
                "skipped": True,
                "reason": "impressum_not_ready",
                "detail": (
                    "Legal Foundation unvollständig — Gewerbedaten ergänzen "
                    "(py scripts/bootstrap_legal_from_env.py)"
                ),
                "missing_impressum": not footer.get("impressum_publishable"),
            }

        body_text = text.rstrip() + "\n\n" + footer["text"]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        intro = paragraphs[0] if paragraphs else text[:200]
        html_body = _html_email(
            title=subject,
            intro=intro,
            rows=[("Nachricht", text.replace("\n", " ")[:500] + ("…" if len(text) > 500 else ""))],
            footer_html=str(footer.get("html") or ""),
        )
        return self._send(
            to=to,
            subject=subject,
            text=body_text,
            html=html_body,
            list_unsubscribe=str(footer.get("list_unsubscribe") or ""),
        )

    def _send(
        self,
        *,
        to: str,
        subject: str,
        text: str,
        html: str,
        list_unsubscribe: str = "",
    ) -> dict:
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
        headers = {"Authorization": f"Bearer {api_key}"}
        if list_unsubscribe.strip():
            headers["List-Unsubscribe"] = list_unsubscribe.strip()
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                "https://api.resend.com/emails",
                json=payload,
                headers=headers,
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
