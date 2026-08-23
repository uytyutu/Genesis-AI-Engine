"""Merchant Invoice / Credit Note PDF — Gen1 professional documents.

Seller data comes from Business Profile (SSOT) + tax_config VAT ID.
PDF via fpdf2; optional payment QR via qrcode.
"""

from __future__ import annotations

import io
import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.store_admin.business_profile import BusinessProfileService
from app.integration.store_admin.commerce_settings import (
    StoreCommerceSettingsService,
    default_invoice_config,
)
from app.integration.store_admin.design_service import StoreDesignService

LANGS = ("de", "en", "ru", "uk")

I18N: dict[str, dict[str, str]] = {
    "de": {
        "invoice": "Rechnung",
        "credit_note": "Gutschrift",
        "invoice_no": "Rechnungsnr.",
        "credit_no": "Gutschriftnr.",
        "date": "Datum",
        "order": "Bestellung",
        "seller": "Verkäufer",
        "buyer": "Kunde",
        "vat_id": "USt-IdNr.",
        "item": "Artikel",
        "qty": "Menge",
        "unit": "Einzelpreis",
        "line_total": "Summe",
        "subtotal": "Zwischensumme",
        "shipping": "Versand",
        "tax": "MwSt.",
        "total": "Gesamtbetrag",
        "payment": "Zahlung",
        "reason": "Grund",
        "ref_invoice": "Bezug Rechnung",
        "refund_full": "Vollständige Rückerstattung",
        "refund_partial": "Teilrückerstattung",
        "thanks": "Vielen Dank für Ihren Einkauf.",
        "page": "Seite",
    },
    "en": {
        "invoice": "Invoice",
        "credit_note": "Credit Note",
        "invoice_no": "Invoice No.",
        "credit_no": "Credit Note No.",
        "date": "Date",
        "order": "Order",
        "seller": "Seller",
        "buyer": "Customer",
        "vat_id": "VAT ID",
        "item": "Item",
        "qty": "Qty",
        "unit": "Unit price",
        "line_total": "Amount",
        "subtotal": "Subtotal",
        "shipping": "Shipping",
        "tax": "VAT",
        "total": "Total",
        "payment": "Payment",
        "reason": "Reason",
        "ref_invoice": "Original invoice",
        "refund_full": "Full refund",
        "refund_partial": "Partial refund",
        "thanks": "Thank you for your purchase.",
        "page": "Page",
    },
    "ru": {
        "invoice": "Счёт",
        "credit_note": "Кредит-нота",
        "invoice_no": "Номер счёта",
        "credit_no": "Номер кредит-ноты",
        "date": "Дата",
        "order": "Заказ",
        "seller": "Продавец",
        "buyer": "Клиент",
        "vat_id": "ИНН/USt-IdNr.",
        "item": "Товар",
        "qty": "Кол-во",
        "unit": "Цена",
        "line_total": "Сумма",
        "subtotal": "Подытог",
        "shipping": "Доставка",
        "tax": "НДС",
        "total": "Итого",
        "payment": "Оплата",
        "reason": "Причина",
        "ref_invoice": "Исходный счёт",
        "refund_full": "Полный возврат",
        "refund_partial": "Частичный возврат",
        "thanks": "Спасибо за покупку.",
        "page": "Стр.",
    },
    "uk": {
        "invoice": "Рахунок",
        "credit_note": "Кредит-нота",
        "invoice_no": "Номер рахунку",
        "credit_no": "Номер кредит-ноти",
        "date": "Дата",
        "order": "Замовлення",
        "seller": "Продавець",
        "buyer": "Клієнт",
        "vat_id": "ІПН/USt-IdNr.",
        "item": "Товар",
        "qty": "К-сть",
        "unit": "Ціна",
        "line_total": "Сума",
        "subtotal": "Підсумок",
        "shipping": "Доставка",
        "tax": "ПДВ",
        "total": "Разом",
        "payment": "Оплата",
        "reason": "Причина",
        "ref_invoice": "Вихідний рахунок",
        "refund_full": "Повне повернення",
        "refund_partial": "Часткове повернення",
        "thanks": "Дякуємо за покупку.",
        "page": "Стор.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(order_id: str) -> str:
    return re.sub(r"[^\w\-]", "_", order_id)[:80]


def resolve_pdf_font() -> tuple[str | None, str | None]:
    """Return (regular_ttf, bold_ttf) or (None, None) for Helvetica fallback."""
    import os

    env = os.getenv("INVOICE_PDF_FONT", "").strip()
    candidates: list[tuple[Path, Path | None]] = []
    if env:
        p = Path(env)
        candidates.append((p, p))
    candidates.extend(
        [
            (Path(r"C:\Windows\Fonts\arial.ttf"), Path(r"C:\Windows\Fonts\arialbd.ttf")),
            (
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
                Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
            ),
            (
                Path("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"),
                Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
            ),
            (Path("/System/Library/Fonts/Supplemental/Arial.ttf"), None),
        ]
    )
    for regular, bold in candidates:
        if regular.is_file():
            return str(regular), str(bold) if bold and bold.is_file() else str(regular)
    return None, None


def _fmt_money(amount: float, currency: str = "EUR") -> str:
    cur = (currency or "EUR").upper()
    symbol = "EUR" if cur == "EUR" else cur
    return f"{amount:,.2f} {symbol}".replace(",", "X").replace(".", ",").replace("X", ".")


def _fmt_date(iso: str | None, fmt: str = "DD.MM.YYYY") -> str:
    if not iso:
        return datetime.now(timezone.utc).strftime("%d.%m.%Y")
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return str(iso)[:10]
    if fmt == "YYYY-MM-DD":
        return dt.strftime("%Y-%m-%d")
    if fmt == "MM/DD/YYYY":
        return dt.strftime("%m/%d/%Y")
    return dt.strftime("%d.%m.%Y")


def _t(lang: str, key: str) -> str:
    pack = I18N.get(lang) or I18N["de"]
    return pack.get(key) or I18N["en"].get(key) or key


class StoreInvoiceService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._commerce = StoreCommerceSettingsService(memory_dir)
        self._profile = BusinessProfileService(memory_dir)
        self._design = StoreDesignService(memory_dir)

    def _shop_dir(self, order_id: str) -> Path:
        d = self._memory / "store_admin" / _safe(order_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _docs_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "documents.json"

    def _pdf_dir(self, order_id: str) -> Path:
        d = self._shop_dir(order_id) / "invoices"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _load_docs(self, order_id: str) -> list[dict[str, Any]]:
        path = self._docs_path(order_id)
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data.get("documents") if isinstance(data, dict) else data
            return [r for r in (rows or []) if isinstance(r, dict)]
        except (OSError, json.JSONDecodeError):
            return []

    def _save_docs(self, order_id: str, rows: list[dict[str, Any]]) -> None:
        self._docs_path(order_id).write_text(
            json.dumps(
                {"version": 1, "order_id": order_id, "documents": rows[-500:]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _load_shop_order(self, order_id: str, shop_order_id: str) -> dict[str, Any]:
        path = self._shop_dir(order_id) / "orders.json"
        if not path.is_file():
            raise ValueError("order_not_found")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            orders = data.get("orders") if isinstance(data, dict) else data
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError("order_not_found") from exc
        for row in orders or []:
            if isinstance(row, dict) and str(row.get("id") or "") == shop_order_id:
                return row
        raise ValueError("order_not_found")

    def _invoice_cfg(self, order_id: str) -> dict[str, Any]:
        settings = self._commerce.get(order_id)["settings"]
        cfg = dict(settings.get("invoice_config") or default_invoice_config())
        # defaults for Gen1 extensions
        cfg.setdefault("language", "de")
        cfg.setdefault("currency", "EUR")
        cfg.setdefault("date_format", "DD.MM.YYYY")
        cfg.setdefault("signature_text", None)
        cfg.setdefault("stamp_enabled", False)
        cfg.setdefault("show_payment_qr", True)
        return cfg

    def _resolve_logo_flexible(self, order_id: str, cfg: dict[str, Any]) -> Path | None:
        for key in ("logo_path", "logo_asset_path"):
            raw = cfg.get(key)
            if raw:
                p = Path(str(raw))
                if p.is_file():
                    return p
        try:
            design = self._design.raw_design(order_id)
            logo = (design.get("branding") or {}).get("logo")
            if isinstance(logo, dict) and logo.get("id"):
                path = self._design.resolve_media(order_id, str(logo["id"]))
                if path.is_file():
                    return path
            if isinstance(logo, dict) and logo.get("path"):
                path = self._design._media.resolve_path(str(logo["path"]))  # noqa: SLF001
                if path.is_file():
                    return path
        except Exception:  # noqa: BLE001
            pass
        media_root = self._shop_dir(order_id) / "media"
        if media_root.is_dir():
            for p in sorted(media_root.glob("*")):
                if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"} and "logo" in p.name.lower():
                    return p
        return None

    def _logo_path(self, order_id: str, cfg: dict[str, Any]) -> Path | None:
        return self._resolve_logo_flexible(order_id, cfg)

    def update_config(self, order_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        """Extend invoice settings; company_name prefers Business Profile."""
        settings = self._commerce.get(order_id)["settings"]
        cfg = dict(settings.get("invoice_config") or default_invoice_config())
        for key in (
            "prefix",
            "credit_note_prefix",
            "company_name",
            "signature_text",
            "language",
            "currency",
            "date_format",
        ):
            if key in patch and patch[key] is not None:
                val = str(patch[key]).strip()
                if key == "language":
                    cfg[key] = val.lower()[:2] if val.lower()[:2] in LANGS else "de"
                elif key == "currency":
                    cfg[key] = (val or "EUR").upper()[:8]
                elif key == "date_format":
                    cfg[key] = val if val in {"DD.MM.YYYY", "YYYY-MM-DD", "MM/DD/YYYY"} else "DD.MM.YYYY"
                else:
                    cfg[key] = val[:200] or None
        for key in ("next_number", "next_credit_number"):
            if key in patch:
                cfg[key] = max(1, int(patch[key] or 1))
        for key in ("include_order_number", "auto_pdf", "stamp_enabled", "show_payment_qr"):
            if key in patch:
                cfg[key] = bool(patch[key])
        return self._commerce.update_invoice_config(order_id, cfg)

    def list_documents(self, order_id: str) -> dict[str, Any]:
        rows = self._load_docs(order_id)
        return {
            "ok": True,
            "order_id": order_id,
            "count": len(rows),
            "documents": rows,
            "config": self._invoice_cfg(order_id),
        }

    def get_document(self, order_id: str, doc_id: str) -> dict[str, Any]:
        for row in self._load_docs(order_id):
            if str(row.get("id")) == doc_id:
                return {"ok": True, "document": row, "order_id": order_id}
        raise ValueError("document_not_found")

    def create_invoice(
        self,
        order_id: str,
        *,
        shop_order_id: str,
        language: str | None = None,
    ) -> dict[str, Any]:
        shop_order = self._load_shop_order(order_id, shop_order_id)
        cfg = self._invoice_cfg(order_id)
        lang = (language or cfg.get("language") or "de").lower()[:2]
        if lang not in LANGS:
            lang = "de"
        allocated = self._commerce.allocate_invoice_number(order_id)
        number = allocated["invoice_number"]
        doc = self._build_document(
            order_id,
            shop_order=shop_order,
            doc_type="invoice",
            number=number,
            language=lang,
            cfg=cfg,
        )
        pdf_bytes = self.render_pdf(doc, order_id=order_id)
        rel = f"invoices/{number}.pdf"
        out_path = self._pdf_dir(order_id) / f"{number}.pdf"
        out_path.write_bytes(pdf_bytes)
        doc["pdf_path"] = rel
        doc["pdf_bytes_len"] = len(pdf_bytes)
        rows = self._load_docs(order_id)
        rows.insert(0, doc)
        self._save_docs(order_id, rows)

        profile = self._profile.get(order_id)["profile"]
        has_logo = bool(
            self._resolve_logo_flexible(order_id, cfg) or profile.get("logo_asset_id")
        )
        vector_hint = {
            "message": "✅ Первый Invoice успешно создан.",
            "suggest_logo": not has_logo,
            "logo_message": (
                "Для более профессионального вида добавьте логотип компании."
                if not has_logo
                else None
            ),
            "cta": "Открыть Branding" if not has_logo else None,
            "cta_section": "design" if not has_logo else None,
        }
        return {
            "ok": True,
            "document": doc,
            "order_id": order_id,
            "vector_hint": vector_hint,
            "download_url": f"/api/client/stores/{order_id}/admin/documents/{doc['id']}/pdf",
        }

    def create_credit_note(
        self,
        order_id: str,
        *,
        invoice_doc_id: str,
        reason: str,
        refund_type: str = "full",
        amount_eur: float | None = None,
        language: str | None = None,
    ) -> dict[str, Any]:
        inv = self.get_document(order_id, invoice_doc_id)["document"]
        if inv.get("type") != "invoice":
            raise ValueError("invoice_required")
        cfg = self._invoice_cfg(order_id)
        lang = (language or inv.get("language") or cfg.get("language") or "de").lower()[:2]
        if lang not in LANGS:
            lang = "de"
        allocated = self._commerce.allocate_credit_note(order_id)
        number = allocated["credit_note_number"]
        rtype = refund_type if refund_type in {"full", "partial"} else "full"
        totals = dict(inv.get("totals") or {})
        if rtype == "partial" and amount_eur is not None:
            amt = max(0.0, float(amount_eur))
            totals = {
                "subtotal_eur": amt,
                "shipping_eur": 0.0,
                "tax_eur": 0.0,
                "total_eur": amt,
                "currency": totals.get("currency") or cfg.get("currency") or "EUR",
            }
            lines = [
                {
                    "title": _t(lang, "refund_partial"),
                    "qty": 1,
                    "unit_price_eur": amt,
                    "line_total_eur": amt,
                }
            ]
        else:
            lines = list(inv.get("lines") or [])
            # Negate amounts for credit note display
            lines = [
                {
                    **ln,
                    "unit_price_eur": -abs(float(ln.get("unit_price_eur") or 0)),
                    "line_total_eur": -abs(float(ln.get("line_total_eur") or 0)),
                }
                for ln in lines
            ]
            totals = {
                "subtotal_eur": -abs(float(totals.get("subtotal_eur") or 0)),
                "shipping_eur": -abs(float(totals.get("shipping_eur") or 0)),
                "tax_eur": -abs(float(totals.get("tax_eur") or 0)),
                "total_eur": -abs(float(totals.get("total_eur") or 0)),
                "currency": totals.get("currency") or "EUR",
            }

        doc = {
            "id": f"doc-{uuid.uuid4().hex[:10]}",
            "type": "credit_note",
            "number": number,
            "shop_order_id": inv.get("shop_order_id"),
            "created_at": _now(),
            "language": lang,
            "currency": totals.get("currency") or "EUR",
            "status": "issued",
            "buyer": inv.get("buyer"),
            "seller": inv.get("seller"),
            "lines": lines,
            "totals": totals,
            "tax": inv.get("tax"),
            "payment": inv.get("payment"),
            "shipping_method": inv.get("shipping_method"),
            "credit_of": inv.get("number"),
            "credit_of_id": inv.get("id"),
            "reason": (reason or "").strip()[:500] or None,
            "refund_type": rtype,
            "email_sends": [],
            "date_format": cfg.get("date_format") or "DD.MM.YYYY",
            "signature_text": cfg.get("signature_text"),
            "stamp_enabled": bool(cfg.get("stamp_enabled")),
            "show_payment_qr": False,
        }
        pdf_bytes = self.render_pdf(doc, order_id=order_id)
        out_path = self._pdf_dir(order_id) / f"{number}.pdf"
        out_path.write_bytes(pdf_bytes)
        doc["pdf_path"] = f"invoices/{number}.pdf"
        doc["pdf_bytes_len"] = len(pdf_bytes)
        rows = self._load_docs(order_id)
        rows.insert(0, doc)
        self._save_docs(order_id, rows)
        return {
            "ok": True,
            "document": doc,
            "order_id": order_id,
            "download_url": f"/api/client/stores/{order_id}/admin/documents/{doc['id']}/pdf",
        }

    def _build_document(
        self,
        order_id: str,
        *,
        shop_order: dict[str, Any],
        doc_type: str,
        number: str,
        language: str,
        cfg: dict[str, Any],
    ) -> dict[str, Any]:
        contacts = self._profile.as_factory_contacts(order_id)
        settings = self._commerce.get(order_id)["settings"]
        tax_cfg = settings.get("tax_config") or {}
        profile = self._profile.get(order_id)["profile"]
        company = (
            profile.get("company_name")
            or cfg.get("company_name")
            or contacts.get("company_name")
            or "Store"
        )
        buyer = shop_order.get("buyer") if isinstance(shop_order.get("buyer"), dict) else {}
        address = shop_order.get("address") if isinstance(shop_order.get("address"), dict) else {}
        lines = []
        for item in shop_order.get("items") or []:
            if not isinstance(item, dict):
                continue
            lines.append(
                {
                    "title": str(item.get("title") or item.get("product_id") or "Item")[:120],
                    "qty": int(item.get("qty") or 1),
                    "unit_price_eur": float(item.get("unit_price_eur") or 0),
                    "line_total_eur": float(item.get("line_total_eur") or 0),
                }
            )
        currency = str(shop_order.get("currency") or cfg.get("currency") or "EUR")
        seller = {
            "company_name": company,
            "email": contacts.get("email_support") or contacts.get("email"),
            "phone": contacts.get("phone"),
            "address_line": contacts.get("address_line"),
            "vat_id": tax_cfg.get("company_vat_id"),
            "hours": contacts.get("hours"),
        }
        buyer_block = {
            "name": buyer.get("name") or buyer.get("email"),
            "email": buyer.get("email"),
            "address_line": ", ".join(
                str(x)
                for x in (
                    address.get("line1") or address.get("street"),
                    " ".join(
                        str(p)
                        for p in (address.get("postal_code"), address.get("city"))
                        if p
                    ).strip()
                    or None,
                    address.get("country"),
                )
                if x
            )
            or None,
        }
        pay = shop_order.get("payment_method")
        pay_label = pay.get("label") if isinstance(pay, dict) else pay
        return {
            "id": f"doc-{uuid.uuid4().hex[:10]}",
            "type": doc_type,
            "number": number,
            "shop_order_id": shop_order.get("id"),
            "created_at": _now(),
            "language": language,
            "currency": currency,
            "status": "issued",
            "buyer": buyer_block,
            "seller": seller,
            "lines": lines,
            "totals": {
                "subtotal_eur": float(shop_order.get("subtotal_eur") or 0),
                "shipping_eur": float(shop_order.get("shipping_eur") or 0),
                "tax_eur": float(shop_order.get("tax_eur") or 0),
                "total_eur": float(shop_order.get("total_eur") or 0),
                "currency": currency,
            },
            "tax": {
                "rate_pct": tax_cfg.get("standard_rate_pct"),
                "vat_id": tax_cfg.get("company_vat_id"),
                "profile": tax_cfg.get("profile"),
            },
            "payment": {"label": pay_label, "id": pay.get("id") if isinstance(pay, dict) else None},
            "shipping_method": (
                (shop_order.get("shipping_method") or {}).get("label")
                if isinstance(shop_order.get("shipping_method"), dict)
                else shop_order.get("shipping_method")
            ),
            "include_order_number": bool(cfg.get("include_order_number", True)),
            "date_format": cfg.get("date_format") or "DD.MM.YYYY",
            "signature_text": cfg.get("signature_text"),
            "stamp_enabled": bool(cfg.get("stamp_enabled")),
            "show_payment_qr": bool(cfg.get("show_payment_qr", True)),
            "email_sends": [],
            "logo_missing": self._resolve_logo_flexible(order_id, cfg) is None,
        }

    def read_pdf_bytes(self, order_id: str, doc_id: str) -> tuple[bytes, str]:
        doc = self.get_document(order_id, doc_id)["document"]
        rel = str(doc.get("pdf_path") or "")
        path = self._shop_dir(order_id) / rel
        if not path.is_file():
            # regenerate
            pdf = self.render_pdf(doc, order_id=order_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(pdf)
            return pdf, str(doc.get("number") or doc_id)
        return path.read_bytes(), str(doc.get("number") or doc_id)

    def send_document_email(
        self,
        order_id: str,
        doc_id: str,
        *,
        to: str | None = None,
        resend: bool = False,
    ) -> dict[str, Any]:
        from app.integration.store_admin.email_templates import EmailTemplatesService
        from app.integration.store_admin.merchant_smtp import send_merchant_smtp

        doc = self.get_document(order_id, doc_id)["document"]
        settings = self._commerce.get(order_id)["settings"]
        transport = settings.get("email_transport") or {}
        if not transport.get("host") or not transport.get("password"):
            raise ValueError("smtp_not_connected")
        dest = (
            (to or "").strip()
            or str((doc.get("buyer") or {}).get("email") or "").strip()
            or str(transport.get("support_email") or "").strip()
        )
        if not dest:
            raise ValueError("recipient_required")
        lang = str(doc.get("language") or "de")
        company = str((doc.get("seller") or {}).get("company_name") or "Store")
        templates = EmailTemplatesService(self._memory)
        tpl_id = "invoice" if doc.get("type") == "invoice" else "payment_received"
        try:
            rendered = templates.render(
                order_id,
                tpl_id,
                {
                    "invoice_number": doc.get("number"),
                    "order_id": doc.get("shop_order_id"),
                    "company_name": company,
                    "buyer_name": (doc.get("buyer") or {}).get("name") or "",
                    "support_email": (doc.get("seller") or {}).get("email") or "",
                },
            )
            subject = rendered["subject"]
            body = rendered["body"]
        except ValueError:
            subject = f"{_t(lang, doc.get('type') or 'invoice')} {doc.get('number')}"
            body = f"{subject}\n{company}\n"
        # Note: merchant_smtp currently text/html only — attach note about PDF download
        body = (
            f"{body}\n\n"
            f"PDF: {doc.get('number')}.pdf "
            f"({doc.get('pdf_bytes_len') or 0} bytes stored in Store Admin).\n"
        )
        result = send_merchant_smtp(
            transport=transport,
            to=dest,
            subject=subject,
            text=body,
        )
        sends = list(doc.get("email_sends") or [])
        sends.append(
            {
                "at": _now(),
                "to": dest,
                "ok": bool(result.get("ok")),
                "resend": bool(resend),
                "status": result.get("status"),
                "title": result.get("title"),
                "reason": result.get("reason"),
            }
        )
        doc["email_sends"] = sends[-20:]
        rows = self._load_docs(order_id)
        for i, row in enumerate(rows):
            if str(row.get("id")) == doc_id:
                rows[i] = doc
                break
        self._save_docs(order_id, rows)
        return {
            "ok": bool(result.get("ok")),
            "document": doc,
            "email": result,
            "message": (
                "Invoice emailed"
                if result.get("ok")
                else (result.get("title") or "Email failed")
            ),
        }

    def render_pdf(self, doc: dict[str, Any], *, order_id: str | None = None) -> bytes:
        # Attach logo path when store id known
        if order_id and not doc.get("_logo_path"):
            logo = self._resolve_logo_flexible(order_id, {})
            doc = {**doc, "_logo_path": str(logo) if logo else ""}
        return _render_pdf_bytes(doc)


def _render_pdf_bytes(doc: dict[str, Any]) -> bytes:
    from fpdf import FPDF

    lang = str(doc.get("language") or "de")
    currency = str(doc.get("currency") or "EUR")
    seller = doc.get("seller") or {}
    buyer = doc.get("buyer") or {}
    totals = doc.get("totals") or {}
    tax = doc.get("tax") or {}
    regular, bold = resolve_pdf_font()
    font_name = "Inv"

    class InvoicePDF(FPDF):
        def footer(self) -> None:  # noqa: N802
            self.set_y(-12)
            self.set_font(font_name if regular else "Helvetica", size=8)
            self.set_text_color(120, 120, 130)
            self.cell(
                0,
                8,
                f"{_t(lang, 'page')} {self.page_no()}",
                align="C",
            )

    pdf = InvoicePDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    if regular:
        pdf.add_font(font_name, "", regular)
        pdf.add_font(font_name, "B", bold or regular)
        use = font_name
    else:
        use = "Helvetica"

    def txt(s: Any) -> str:
        raw = str(s if s is not None else "")
        if regular:
            return raw
        return raw.encode("latin-1", "replace").decode("latin-1")

    # Header
    title = _t(lang, "credit_note" if doc.get("type") == "credit_note" else "invoice")
    logo_path = doc.get("_logo_path")
    if logo_path and Path(str(logo_path)).is_file():
        try:
            pdf.image(str(logo_path), x=pdf.l_margin, y=pdf.get_y(), h=16)
            pdf.set_y(pdf.get_y() + 18)
        except Exception:  # noqa: BLE001
            pass
    pdf.set_font(use, "B", 18)
    pdf.cell(0, 10, txt(title), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(use, "", 10)
    pdf.set_text_color(60, 60, 70)
    no_label = _t(lang, "credit_no" if doc.get("type") == "credit_note" else "invoice_no")
    pdf.cell(0, 6, txt(f"{no_label}: {doc.get('number')}"), new_x="LMARGIN", new_y="NEXT")
    pdf.cell(
        0,
        6,
        txt(
            f"{_t(lang, 'date')}: {_fmt_date(doc.get('created_at'), doc.get('date_format') or 'DD.MM.YYYY')}"
        ),
        new_x="LMARGIN",
        new_y="NEXT",
    )
    if doc.get("include_order_number") and doc.get("shop_order_id"):
        pdf.cell(
            0,
            6,
            txt(f"{_t(lang, 'order')}: {doc.get('shop_order_id')}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    if doc.get("credit_of"):
        pdf.cell(
            0,
            6,
            txt(f"{_t(lang, 'ref_invoice')}: {doc.get('credit_of')}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    if doc.get("reason"):
        pdf.cell(
            0,
            6,
            txt(f"{_t(lang, 'reason')}: {doc.get('reason')}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )
    if doc.get("refund_type"):
        key = "refund_full" if doc.get("refund_type") == "full" else "refund_partial"
        pdf.cell(0, 6, txt(_t(lang, key)), new_x="LMARGIN", new_y="NEXT")

    pdf.ln(4)
    col_w = 95
    pdf.set_font(use, "B", 11)
    pdf.cell(col_w, 6, txt(_t(lang, "seller")), new_x="RIGHT", new_y="TOP")
    pdf.cell(col_w, 6, txt(_t(lang, "buyer")), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(use, "", 9)
    seller_lines = [
        seller.get("company_name"),
        seller.get("address_line"),
        seller.get("email"),
        seller.get("phone"),
        f"{_t(lang, 'vat_id')}: {seller.get('vat_id')}" if seller.get("vat_id") else None,
    ]
    buyer_lines = [
        buyer.get("name"),
        buyer.get("address_line"),
        buyer.get("email"),
    ]
    for i in range(max(len(seller_lines), len(buyer_lines))):
        s = seller_lines[i] if i < len(seller_lines) else None
        b = buyer_lines[i] if i < len(buyer_lines) else None
        pdf.cell(col_w, 5, txt(s or ""), new_x="RIGHT", new_y="TOP")
        pdf.cell(col_w, 5, txt(b or ""), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_fill_color(240, 240, 245)
    pdf.set_font(use, "B", 9)
    pdf.cell(80, 7, txt(_t(lang, "item")), border=1, fill=True)
    pdf.cell(20, 7, txt(_t(lang, "qty")), border=1, fill=True, align="R")
    pdf.cell(40, 7, txt(_t(lang, "unit")), border=1, fill=True, align="R")
    pdf.cell(
        40,
        7,
        txt(_t(lang, "line_total")),
        border=1,
        fill=True,
        align="R",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.set_font(use, "", 9)
    for ln in doc.get("lines") or []:
        pdf.cell(80, 6, txt(str(ln.get("title") or "")[:48]), border=1)
        pdf.cell(20, 6, txt(str(ln.get("qty") or 1)), border=1, align="R")
        pdf.cell(
            40,
            6,
            txt(_fmt_money(float(ln.get("unit_price_eur") or 0), currency)),
            border=1,
            align="R",
        )
        pdf.cell(
            40,
            6,
            txt(_fmt_money(float(ln.get("line_total_eur") or 0), currency)),
            border=1,
            align="R",
            new_x="LMARGIN",
            new_y="NEXT",
        )

    pdf.ln(4)
    rate = tax.get("rate_pct")
    rows_tot = [
        (_t(lang, "subtotal"), float(totals.get("subtotal_eur") or 0)),
        (_t(lang, "shipping"), float(totals.get("shipping_eur") or 0)),
        (
            f"{_t(lang, 'tax')}" + (f" ({rate}%)" if rate is not None else ""),
            float(totals.get("tax_eur") or 0),
        ),
    ]
    pdf.set_font(use, "", 10)
    for label, val in rows_tot:
        pdf.cell(140, 6, txt(label), align="R")
        pdf.cell(40, 6, txt(_fmt_money(val, currency)), align="R", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(use, "B", 12)
    pdf.cell(140, 8, txt(_t(lang, "total")), align="R")
    pdf.cell(
        40,
        8,
        txt(_fmt_money(float(totals.get("total_eur") or 0), currency)),
        align="R",
        new_x="LMARGIN",
        new_y="NEXT",
    )

    pdf.ln(4)
    pdf.set_font(use, "", 9)
    pay = doc.get("payment") or {}
    if pay.get("label"):
        pdf.cell(0, 5, txt(f"{_t(lang, 'payment')}: {pay.get('label')}"), new_x="LMARGIN", new_y="NEXT")
    if doc.get("shipping_method"):
        pdf.cell(
            0,
            5,
            txt(f"{_t(lang, 'shipping')}: {doc.get('shipping_method')}"),
            new_x="LMARGIN",
            new_y="NEXT",
        )

    if doc.get("show_payment_qr") and doc.get("type") == "invoice":
        qr_png = _payment_qr_png(
            company=str(seller.get("company_name") or ""),
            amount=abs(float(totals.get("total_eur") or 0)),
            currency=currency,
            remittance=str(doc.get("number") or ""),
        )
        if qr_png:
            try:
                pdf.ln(2)
                pdf.image(qr_png, w=28, h=28)
                pdf.set_font(use, "", 8)
                pdf.cell(0, 5, txt(_t(lang, "payment") + " QR"), new_x="LMARGIN", new_y="NEXT")
            except Exception:  # noqa: BLE001
                pass

    if doc.get("signature_text"):
        pdf.ln(6)
        pdf.set_font(use, "", 10)
        pdf.cell(0, 6, txt(doc.get("signature_text")), new_x="LMARGIN", new_y="NEXT")
    if doc.get("stamp_enabled"):
        pdf.set_font(use, "B", 9)
        pdf.set_text_color(180, 40, 40)
        pdf.cell(0, 6, txt("[STAMP]"), new_x="LMARGIN", new_y="NEXT")
        pdf.set_text_color(0, 0, 0)

    pdf.ln(6)
    pdf.set_font(use, "", 9)
    pdf.cell(0, 5, txt(_t(lang, "thanks")), new_x="LMARGIN", new_y="NEXT")

    out = pdf.output()
    if isinstance(out, (bytes, bytearray)):
        return bytes(out)
    return bytes(out)


def _payment_qr_png(
    *,
    company: str,
    amount: float,
    currency: str,
    remittance: str,
) -> str | Path | None:
    """Build a simple payment QR as temp PNG path / BytesIO for fpdf image()."""
    try:
        import qrcode
    except ImportError:
        return None
    # EPC-ish free-text payload (not full SEPA QR without IBAN)
    payload = (
        f"BCD\n002\n1\nSCT\n\n{company[:70]}\n\n"
        f"{currency}{amount:.2f}\n\n{remittance}\n"
    )
    try:
        img = qrcode.make(payload)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        buf.seek(0)
        return buf
    except Exception:  # noqa: BLE001
        return None


def count_issued_invoices(memory_dir: Path) -> int:
    root = Path(memory_dir) / "store_admin"
    if not root.is_dir():
        return 0
    n = 0
    for shop in root.iterdir():
        path = shop / "documents.json"
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            docs = data.get("documents") if isinstance(data, dict) else data
            for d in docs or []:
                if isinstance(d, dict) and d.get("type") == "invoice" and d.get("pdf_path"):
                    n += 1
        except (OSError, json.JSONDecodeError):
            continue
    return n
