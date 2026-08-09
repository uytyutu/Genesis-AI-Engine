"""Client transactional emails (Resend API v1)."""

from __future__ import annotations

import html
import os
from pathlib import Path

from app.factory.market_delivery import order_ui_lang
from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.product_line import project_awaiting_payment_message
from app.legal.service import LegalFoundationService

_DEFAULT_MEMORY = Path(__file__).resolve().parent.parent / "memory"

# Language Consistency Gate L4 — one pack per CEO locale.
_EMAIL_PACKS: dict[str, dict[str, str]] = {
    "de": {
        "received_title": "Projekt erfasst",
        "received_subject": "Projekt erfasst — {business} (Nr. {order_id})",
        "received_hello": "Guten Tag!",
        "received_body": "Wir haben Ihr Projekt «{business}» erhalten.",
        "received_cta": "Projekt bezahlen",
        "received_status": "Projektstatus",
        "received_regards": "Mit freundlichen Grüßen",
        "row_order": "Bestellung",
        "row_business": "Geschäft",
        "row_package": "Paket",
        "row_status": "Status",
        "status_awaiting": "Wartet auf Zahlung",
        "receipt_title": "Zahlung bestätigt",
        "receipt_subject": "Zahlung erhalten — {business} (Nr. {order_id})",
        "receipt_intro": "Danke für Ihre Zahlung! Wir haben mit der Arbeit begonnen.",
        "receipt_cta": "Bestellstatus",
        "status_paid": "Bezahlt",
        "row_eta": "Lieferzeit",
        "eta_hours": "~{eta} Stunden",
    },
    "en": {
        "received_title": "Project registered",
        "received_subject": "Project registered — {business} (#{order_id})",
        "received_hello": "Hello!",
        "received_body": "We received your project «{business}».",
        "received_cta": "Pay for project",
        "received_status": "Project status",
        "received_regards": "Best regards",
        "row_order": "Order",
        "row_business": "Business",
        "row_package": "Package",
        "row_status": "Status",
        "status_awaiting": "Awaiting payment",
        "receipt_title": "Payment confirmed",
        "receipt_subject": "Payment received — {business} (#{order_id})",
        "receipt_intro": "Thank you for your payment! We have started work.",
        "receipt_cta": "Order status",
        "status_paid": "Paid",
        "row_eta": "Delivery time",
        "eta_hours": "~{eta} hours",
    },
    "ru": {
        "received_title": "Проект зафиксирован",
        "received_subject": "Проект зафиксирован — {business} (№ {order_id})",
        "received_hello": "Здравствуйте!",
        "received_body": "Мы получили ваш проект «{business}».",
        "received_cta": "Оплатить проект",
        "received_status": "Статус проекта",
        "received_regards": "С уважением",
        "row_order": "Заказ",
        "row_business": "Бизнес",
        "row_package": "Пакет",
        "row_status": "Статус",
        "status_awaiting": "Ожидает оплаты",
        "receipt_title": "Оплата подтверждена",
        "receipt_subject": "Оплата получена — {business} (№ {order_id})",
        "receipt_intro": "Спасибо за оплату! Мы приступили к работе.",
        "receipt_cta": "Статус заказа",
        "status_paid": "Оплачено",
        "row_eta": "Срок",
        "eta_hours": "~{eta} ч.",
    },
    "uk": {
        "received_title": "Проєкт зафіксовано",
        "received_subject": "Проєкт зафіксовано — {business} (№ {order_id})",
        "received_hello": "Вітаємо!",
        "received_body": "Ми отримали ваш проєкт «{business}».",
        "received_cta": "Оплатити проєкт",
        "received_status": "Статус проєкту",
        "received_regards": "З повагою",
        "row_order": "Замовлення",
        "row_business": "Бізнес",
        "row_package": "Пакет",
        "row_status": "Статус",
        "status_awaiting": "Очікує оплати",
        "receipt_title": "Оплату підтверджено",
        "receipt_subject": "Оплату отримано — {business} (№ {order_id})",
        "receipt_intro": "Дякуємо за оплату! Ми розпочали роботу.",
        "receipt_cta": "Статус замовлення",
        "status_paid": "Оплачено",
        "row_eta": "Строк",
        "eta_hours": "~{eta} год.",
    },
}


def _pack(lang: str) -> dict[str, str]:
    base = (lang or "en").strip().lower().split("-")[0]
    return _EMAIL_PACKS.get(base) or _EMAIL_PACKS["en"]


def _public_url(path: str) -> str:
    from app.integration.public_site_url import configured_public_base

    base = configured_public_base()
    p = path if path.startswith("/") else f"/{path}"
    return f"{base}{p}"


def _html_email(
    *,
    lang: str,
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
    html_lang = (lang or "en").split("-")[0]
    support = (
        os.getenv("VIRTUS_SUPPORT_EMAIL", "").strip()
        or os.getenv("GENESIS_SUPPORT_EMAIL", "").strip()
        or "hello@virtuscore.com"
    )
    return f"""<!DOCTYPE html>
<html lang="{html.escape(html_lang)}">
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
<p style="margin:32px 0 0;font-size:12px;color:#52525b">{html.escape(BRAND_NAME)} · {html.escape(support)}</p>
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
        business = str(order.get("business_name", ""))
        lang = order_ui_lang(order)
        pack = _pack(lang)
        status_path = f"/order/status/{order_id}"
        price = str(
            order.get("price_label")
            or f"{order.get('price_eur', '')} {order.get('symbol') or '€'}".strip()
        )
        rows = [
            (pack["row_order"], f"№ {order_id}" if lang in ("ru", "uk", "de") else f"#{order_id}"),
            (pack["row_business"], business),
            (pack["row_package"], f"{order.get('package_name', '')} — {price}"),
            (pack["row_status"], pack["status_awaiting"]),
        ]
        intro = str(
            order.get("client_status_message")
            or project_awaiting_payment_message(
                launch_mode=bool(order.get("launch_mode")), ui_lang=lang
            )
        )
        text = (
            f"{pack['received_hello']}\n\n"
            f"{pack['received_body'].format(business=business)}\n\n"
            f"{pack['row_order']} {order_id}\n"
            f"{price}\n\n"
            f"{intro}\n{_public_url(status_path)}\n\n"
            f"{pack['received_status']}: {_public_url(status_path)}\n\n"
            f"{pack['received_regards']},\n{BRAND_NAME}"
        )
        html_body = _html_email(
            lang=lang,
            title=pack["received_title"],
            intro=intro,
            rows=rows,
            cta_href=_public_url(status_path),
            cta_label=pack["received_cta"],
        )
        return self._send(
            to=str(order.get("email") or "").strip(),
            subject=pack["received_subject"].format(business=business or BRAND_NAME, order_id=order_id),
            text=text,
            html=html_body,
        )

    def send_order_receipt(self, *, order: dict, receipt_text: str) -> dict:
        to = str(order.get("email") or "").strip()
        order_id = str(order.get("order_id", ""))
        lang = order_ui_lang(order)
        pack = _pack(lang)
        status_path = f"/order/status/{order_id}"
        status_url = _public_url(status_path)
        body = receipt_text.replace(f"/order/status/{order_id}", status_url)
        # CEO inbox sees every paid order (BCC), even when client mail is primary.
        bcc = (
            os.getenv("GENESIS_SUPPORT_EMAIL", "").strip()
            or os.getenv("GENESIS_OWNER_NOTIFY_EMAIL", "").strip()
            or "hello@virtuscore.com"
        )

        eta = order.get("estimated_hours")
        price = str(
            order.get("price_label")
            or f"{order.get('price_eur', '')} {order.get('symbol') or '€'}".strip()
        )
        rows = [
            (pack["row_order"], f"Nr. {order_id}" if lang == "de" else f"#{order_id}"),
            (pack["row_package"], f"{order.get('package_name', '')} — {price}"),
            (pack["row_status"], pack["status_paid"]),
        ]
        if eta:
            rows.append((pack["row_eta"], pack["eta_hours"].format(eta=eta)))
        html_body = _html_email(
            lang=lang,
            title=pack["receipt_title"],
            intro=str(order.get("client_status_message") or pack["receipt_intro"]),
            rows=rows,
            cta_href=status_url,
            cta_label=pack["receipt_cta"],
        )
        business = str(order.get("business_name") or pack["row_order"])
        return self._send(
            to=to,
            subject=pack["receipt_subject"].format(business=business, order_id=order_id),
            text=body,
            html=html_body,
            bcc=bcc if bcc.lower() != to.lower() else "",
        )

    def send_owner_payment_alert(self, *, order: dict, support_email: str) -> dict:
        """Direct alert to CEO inbox when a Landing order is paid."""
        from app.integration.locale_service import resolve_generation_language

        to = (support_email or "").strip() or "hello@virtuscore.com"
        order_id = str(order.get("order_id") or "")
        business = str(order.get("business_name") or "")
        package = str(order.get("package_name") or "")
        price = str(order.get("price_label") or f"{order.get('price_eur', '')} €")
        status_url = _public_url(f"/order/status/{order_id}")
        lang = resolve_generation_language(
            order.get("ui_lang"),
            order.get("language"),
            market_code=str(order.get("market_code") or "") or None,
        )
        alerts = {
            "de": {
                "title": "Neue Zahlung",
                "intro": f"{business} — {package} ({price}). Produktion gestartet.",
                "text": (
                    f"Neue Zahlung · Virtus Core\n\n"
                    f"Geschäft: {business}\n"
                    f"Bestellung: {order_id}\n"
                    f"Paket: {package} — {price}\n"
                    f"Status: {status_url}\n\n"
                    f"Produktion wurde gestartet."
                ),
                "subject": f"Neue Zahlung — {business or order_id} ({price})",
                "cta": "Bestellung öffnen",
                "rows": [
                    ("Bestellung", order_id),
                    ("Geschäft", business),
                    ("Paket", f"{package} — {price}"),
                ],
            },
            "en": {
                "title": "New payment",
                "intro": f"{business} — {package} ({price}). Production started.",
                "text": (
                    f"New payment · Virtus Core\n\n"
                    f"Business: {business}\n"
                    f"Order: {order_id}\n"
                    f"Package: {package} — {price}\n"
                    f"Status: {status_url}\n\n"
                    f"Production has started."
                ),
                "subject": f"New payment — {business or order_id} ({price})",
                "cta": "Open order",
                "rows": [
                    ("Order", order_id),
                    ("Business", business),
                    ("Package", f"{package} — {price}"),
                ],
            },
            "ru": {
                "title": "Новая оплата",
                "intro": f"{business} — {package} ({price}). Производство запущено.",
                "text": (
                    f"Новая оплата · Virtus Core\n\n"
                    f"Бизнес: {business}\n"
                    f"Заказ: {order_id}\n"
                    f"Пакет: {package} — {price}\n"
                    f"Статус: {status_url}\n\n"
                    f"Производство запущено."
                ),
                "subject": f"Новая оплата — {business or order_id} ({price})",
                "cta": "Открыть заказ",
                "rows": [
                    ("Заказ", order_id),
                    ("Бизнес", business),
                    ("Пакет", f"{package} — {price}"),
                ],
            },
            "uk": {
                "title": "Нова оплата",
                "intro": f"{business} — {package} ({price}). Виробництво запущено.",
                "text": (
                    f"Нова оплата · Virtus Core\n\n"
                    f"Бізнес: {business}\n"
                    f"Замовлення: {order_id}\n"
                    f"Пакет: {package} — {price}\n"
                    f"Статус: {status_url}\n\n"
                    f"Виробництво запущено."
                ),
                "subject": f"Нова оплата — {business or order_id} ({price})",
                "cta": "Відкрити замовлення",
                "rows": [
                    ("Замовлення", order_id),
                    ("Бізнес", business),
                    ("Пакет", f"{package} — {price}"),
                ],
            },
            "fr": {
                "title": "Nouveau paiement",
                "intro": f"{business} — {package} ({price}). Production démarrée.",
                "text": (
                    f"Nouveau paiement · Virtus Core\n\n"
                    f"Entreprise: {business}\n"
                    f"Commande: {order_id}\n"
                    f"Pack: {package} — {price}\n"
                    f"Statut: {status_url}\n\n"
                    f"La production a démarré."
                ),
                "subject": f"Nouveau paiement — {business or order_id} ({price})",
                "cta": "Ouvrir la commande",
                "rows": [
                    ("Commande", order_id),
                    ("Entreprise", business),
                    ("Pack", f"{package} — {price}"),
                ],
            },
            "pl": {
                "title": "Nowa płatność",
                "intro": f"{business} — {package} ({price}). Produkcja rozpoczęta.",
                "text": (
                    f"Nowa płatność · Virtus Core\n\n"
                    f"Firma: {business}\n"
                    f"Zamówienie: {order_id}\n"
                    f"Pakiet: {package} — {price}\n"
                    f"Status: {status_url}\n\n"
                    f"Produkcja została uruchomiona."
                ),
                "subject": f"Nowa płatność — {business or order_id} ({price})",
                "cta": "Otwórz zamówienie",
                "rows": [
                    ("Zamówienie", order_id),
                    ("Firma", business),
                    ("Pakiet", f"{package} — {price}"),
                ],
            },
        }
        pack = alerts.get(lang) or alerts["en"]
        html_body = _html_email(
            lang=lang if lang in ("de", "en", "ru", "uk", "fr", "pl") else "en",
            title=str(pack["title"]),
            intro=str(pack["intro"]),
            rows=list(pack["rows"]),
            cta_href=status_url,
            cta_label=str(pack["cta"]),
        )
        return self._send(
            to=to,
            subject=str(pack["subject"]),
            text=str(pack["text"]),
            html=html_body,
        )

    def send_outreach(
        self,
        *,
        to: str,
        subject: str,
        text: str,
        from_addr: str | None = None,
        market: str | None = None,
        language: str | None = None,
    ) -> dict:
        """CEO-approved cold outreach — market-aware legal footer (Impressum only for DE)."""
        legal = LegalFoundationService(self._memory)
        footer = legal.email_footer_for_market(
            market,
            include_opt_out=True,
            for_outreach=True,
            language=language,
        )
        if not footer.get("ready_for_outreach"):
            profile = str(footer.get("profile") or "de")
            if profile == "de":
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
            return {
                "ok": False,
                "skipped": True,
                "reason": "sender_footer_not_ready",
                "detail": "Sender contact / opt-out not ready for this market.",
            }

        body_text = text.rstrip() + "\n\n" + footer["text"]
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        intro = paragraphs[0] if paragraphs else text[:200]
        html_body = _html_email(
            lang=(language or "en"),
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
            from_addr=from_addr,
        )

    def _send(
        self,
        *,
        to: str,
        subject: str,
        text: str,
        html: str,
        list_unsubscribe: str = "",
        bcc: str = "",
        from_addr: str | None = None,
    ) -> dict:
        if not to:
            return {"ok": False, "skipped": True, "reason": "no_email"}
        from app.integration.email_provider_pool import send_via_pool

        return send_via_pool(
            to=to,
            subject=subject,
            text=text,
            html=html,
            from_addr=from_addr,
            list_unsubscribe=list_unsubscribe,
            bcc=bcc,
            memory_dir=self._memory,
        )
