"""Checkout 1.0 — place shop orders without live PSP charges.

Buyer path: cart → auth → address → shipping → payment → confirm → order → mail stub.
"""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.store_admin.commerce_settings import StoreCommerceSettingsService
from app.integration.store_customer.service import StoreCustomerService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_order_id(order_id: str) -> str:
    return re.sub(r"[^\w\-]", "_", order_id)[:80]


class StoreCheckoutService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._commerce = StoreCommerceSettingsService(self._memory)
        self._customers = StoreCustomerService(self._memory)

    def _shop_dir(self, order_id: str) -> Path:
        d = self._memory / "store_admin" / _safe_order_id(order_id)
        d.mkdir(parents=True, exist_ok=True)
        return d

    def _orders_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "orders.json"

    def _mail_path(self, order_id: str) -> Path:
        return self._shop_dir(order_id) / "mail_outbox.json"

    def _funnel_path(self) -> Path:
        p = self._memory / "platform_funnel.json"
        return p

    def _load_orders(self, order_id: str) -> list[dict[str, Any]]:
        path = self._orders_path(order_id)
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        rows = data.get("orders") if isinstance(data, dict) else data
        if not isinstance(rows, list):
            return []
        return [o for o in rows if isinstance(o, dict)]

    def _save_orders(self, order_id: str, orders: list[dict[str, Any]]) -> None:
        self._orders_path(order_id).write_text(
            json.dumps(
                {
                    "version": 1,
                    "order_id": order_id,
                    "updated_at": _now(),
                    "orders": orders,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def _append_mail(self, order_id: str, message: dict[str, Any]) -> None:
        path = self._mail_path(order_id)
        rows: list[dict[str, Any]] = []
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                rows = list(data.get("messages") or [])
            except (OSError, json.JSONDecodeError):
                rows = []
        rows.append(message)
        path.write_text(
            json.dumps(
                {"version": 1, "order_id": order_id, "messages": rows[-200:]},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    def track_funnel(self, stage: str, *, meta: dict[str, Any] | None = None) -> None:
        path = self._funnel_path()
        data: dict[str, Any] = {"version": 1, "counts": {}, "events": []}
        if path.is_file():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(raw, dict):
                    data = raw
            except (OSError, json.JSONDecodeError):
                pass
        counts = data.get("counts") if isinstance(data.get("counts"), dict) else {}
        counts[stage] = int(counts.get(stage) or 0) + 1
        data["counts"] = counts
        events = list(data.get("events") or [])
        events.append({"stage": stage, "at": _now(), "meta": meta or {}})
        data["events"] = events[-500:]
        data["updated_at"] = _now()
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def checkout_options(self, order_id: str) -> dict[str, Any]:
        self._commerce.ensure_saved(order_id)
        settings = self._commerce._load_raw(order_id)  # noqa: SLF001
        ship_cfg = settings.get("shipping_config") or {}
        shipping = settings.get("shipping") or {}
        connected_carriers = {
            pid
            for pid, row in shipping.items()
            if isinstance(row, dict) and row.get("status") == "connected"
        }
        methods = [
            m
            for m in (ship_cfg.get("methods") or [])
            if isinstance(m, dict)
            and m.get("enabled", True)
            and str(m.get("carrier") or "") in connected_carriers
        ]
        # Connected carriers with no method rows yet → expose catalog defaults
        if not methods and connected_carriers:
            for pid in connected_carriers:
                row = shipping.get(pid) if isinstance(shipping.get(pid), dict) else {}
                methods.append(
                    {
                        "id": f"{pid}_default",
                        "carrier": pid,
                        "label": (row or {}).get("label") or pid,
                        "days_min": 0 if pid == "pickup" else 2,
                        "days_max": 0 if pid == "pickup" else 5,
                        "price_eur": 0.0 if pid == "pickup" else 7.9,
                        "enabled": True,
                    }
                )

        payments_out = []
        payments = settings.get("payments") or {}
        for pid, row in payments.items():
            if not isinstance(row, dict):
                continue
            if row.get("status") != "connected":
                continue
            mode = "manual_pending"
            note = "Checkout 1.0 — order recorded; live charge comes with Stripe OAuth."
            if pid in {"invoice", "cash_on_delivery"}:
                mode = "offline"
                note = "Pay offline / on delivery."
            elif pid == "stripe" and str(row.get("stripe_user_id") or "").startswith(
                "acct_"
            ):
                mode = "stripe_connect"
                note = (
                    "Stripe Connect linked — order recorded; Direct Charge on "
                    "merchant account is next."
                )
            payments_out.append(
                {
                    "id": pid,
                    "label": row.get("label") or pid,
                    "mode": mode,
                    "note": note,
                    "stripe_user_id": row.get("stripe_user_id")
                    if pid == "stripe"
                    else None,
                }
            )
        if not payments_out:
            payments_out = [
                {
                    "id": "invoice",
                    "label": "Invoice",
                    "mode": "offline",
                    "note": "No PSP connected — Invoice fallback for Checkout 1.0.",
                },
                {
                    "id": "cash_on_delivery",
                    "label": "Cash on Delivery",
                    "mode": "offline",
                    "note": "Pay on delivery.",
                },
            ]

        tax = settings.get("tax_config") or {}
        free_from = ship_cfg.get("free_shipping_from_eur")
        note = (
            "Shipping methods appear after merchant connects a carrier."
            if not methods
            else "No live card charge in Checkout 1.0 — merchant PSP OAuth is next."
        )
        return {
            "ok": True,
            "order_id": order_id,
            "phase": "Checkout 1.0",
            "shipping_methods": methods,
            "payment_methods": payments_out,
            "free_shipping_from_eur": free_from,
            "min_order_eur": ship_cfg.get("min_order_eur"),
            "processing_days": ship_cfg.get("processing_days", 1),
            "tax": {
                "profile": tax.get("profile") or "de_standard",
                "standard_rate_pct": float(tax.get("standard_rate_pct") or 19),
                "vat_exempt": bool(tax.get("vat_exempt")),
            },
            "shipping_ready": bool(methods),
            "note": note,
        }

    def place_order(
        self,
        order_id: str,
        buyer_id: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        buyer = self._customers._find(order_id, buyer_id=buyer_id)  # noqa: SLF001
        if not buyer:
            raise ValueError("buyer_not_found")

        items_raw = payload.get("items")
        if not isinstance(items_raw, list) or not items_raw:
            raise ValueError("cart_empty")

        lines: list[dict[str, Any]] = []
        subtotal = 0.0
        for raw in items_raw[:50]:
            if not isinstance(raw, dict):
                continue
            qty = max(1, int(raw.get("qty") or 1))
            price = float(raw.get("price") or 0)
            title = str(raw.get("name") or raw.get("title") or "Item")[:160]
            pid = str(raw.get("id") or raw.get("product_id") or uuid.uuid4().hex[:8])
            line_total = round(price * qty, 2)
            subtotal += line_total
            lines.append(
                {
                    "product_id": pid,
                    "title": title,
                    "unit_price_eur": price,
                    "qty": qty,
                    "line_total_eur": line_total,
                }
            )
        if not lines:
            raise ValueError("cart_empty")

        options = self.checkout_options(order_id)
        min_order = options.get("min_order_eur")
        if min_order is not None and subtotal < float(min_order):
            raise ValueError("below_min_order")

        ship_id = str(payload.get("shipping_method_id") or "").strip()
        ship_methods = {m["id"]: m for m in options["shipping_methods"]}
        if ship_id not in ship_methods:
            raise ValueError("shipping_required")
        ship = ship_methods[ship_id]
        shipping_eur = float(ship.get("price_eur") or 0)
        free_from = options.get("free_shipping_from_eur")
        if free_from is not None and subtotal >= float(free_from):
            shipping_eur = 0.0

        pay_id = str(payload.get("payment_method_id") or "").strip()
        pay_methods = {p["id"]: p for p in options["payment_methods"]}
        if pay_id not in pay_methods:
            raise ValueError("payment_required")
        pay = pay_methods[pay_id]

        address = payload.get("address") if isinstance(payload.get("address"), dict) else {}
        line1 = str(address.get("line1") or "").strip()
        city = str(address.get("city") or "").strip()
        if not line1 or not city:
            # allow pickup without full street
            if ship.get("carrier") != "pickup":
                raise ValueError("address_incomplete")

        tax = options["tax"]
        rate = 0.0 if tax.get("vat_exempt") else float(tax.get("standard_rate_pct") or 19) / 100.0
        # Prices treated as gross (DE B2C typical) — tax portion informational
        taxable = subtotal + shipping_eur
        tax_eur = round(taxable - (taxable / (1 + rate)) if rate > 0 else 0.0, 2)
        total = round(subtotal + shipping_eur, 2)

        shop_order_id = f"so-{uuid.uuid4().hex[:10]}"
        status = "pending_payment"
        if pay.get("mode") == "offline" and pay_id == "cash_on_delivery":
            status = "awaiting_delivery"
        elif pay.get("mode") == "offline":
            status = "awaiting_invoice"

        record = {
            "id": shop_order_id,
            "shop_order_id": order_id,
            "buyer_id": buyer_id,
            "buyer_email": buyer.get("email"),
            "status": status,
            "payment_status": "pending",
            "payment_method": pay,
            "shipping_method": {
                "id": ship["id"],
                "label": ship.get("label"),
                "carrier": ship.get("carrier"),
                "price_eur": shipping_eur,
                "days_min": ship.get("days_min"),
                "days_max": ship.get("days_max"),
            },
            "address": {
                "full_name": str(address.get("full_name") or "").strip()[:120],
                "line1": line1[:160],
                "line2": str(address.get("line2") or "").strip()[:160],
                "city": city[:80],
                "postal_code": str(address.get("postal_code") or "").strip()[:20],
                "country": str(address.get("country") or "DE").strip()[:2].upper(),
                "phone": str(address.get("phone") or "").strip()[:40],
            },
            "items": lines,
            "subtotal_eur": round(subtotal, 2),
            "shipping_eur": shipping_eur,
            "tax_eur": tax_eur,
            "total_eur": total,
            "currency": "EUR",
            "customer_note": str(payload.get("note") or "").strip()[:500],
            "created_at": _now(),
            "updated_at": _now(),
            "checkout_phase": "1.0",
            "live_charge": False,
            "note": "Checkout 1.0 — order stored; live PSP charge later.",
        }

        orders = self._load_orders(order_id)
        orders.insert(0, record)
        self._save_orders(order_id, orders)

        summary = {
            "id": shop_order_id,
            "status": status,
            "total_eur": total,
            "currency": "EUR",
            "created_at": record["created_at"],
            "item_count": sum(int(i["qty"]) for i in lines),
            "payment_method": pay.get("label"),
            "shipping_method": ship.get("label"),
            "carrier": ship.get("carrier"),
            "tracking_number": None,
            "tracking_url": None,
            "shipping_status": None,
        }
        self._customers.attach_order(order_id, buyer_id, summary)

        # Optional: save address to cabinet
        if payload.get("save_address") and line1 and city:
            try:
                self._customers.save_address(
                    order_id,
                    buyer_id,
                    {**address, "is_default": True, "label": "Checkout"},
                )
            except ValueError:
                pass

        mail = {
            "id": f"mail-{uuid.uuid4().hex[:8]}",
            "type": "order_confirmation",
            "to": buyer.get("email"),
            "subject": f"Order confirmation {shop_order_id}",
            "body": (
                f"Thank you for your order {shop_order_id}.\n"
                f"Total: {total:.2f} EUR\n"
                f"Status: {status}\n"
            ),
            "status": "queued_stub",
            "created_at": _now(),
            "order_id": shop_order_id,
        }
        delivery = "outbox_stub"
        try:
            from app.integration.store_admin.commerce_settings import (
                StoreCommerceSettingsService,
            )
            from app.integration.store_admin.email_templates import EmailTemplatesService
            from app.integration.store_admin.merchant_smtp import send_merchant_smtp

            commerce = StoreCommerceSettingsService(self._memory)
            settings = commerce.get(order_id)["settings"]
            transport = settings.get("email_transport") or {}
            if transport.get("host") and transport.get("password"):
                profile_name = transport.get("from_name") or "Store"
                templates = EmailTemplatesService(self._memory)
                rendered = templates.render(
                    order_id,
                    "order_confirmation",
                    {
                        "order_id": shop_order_id,
                        "company_name": profile_name,
                        "buyer_name": buyer.get("name") or buyer.get("email") or "",
                        "total": f"{total:.2f}",
                        "currency": "EUR",
                        "support_email": transport.get("support_email")
                        or transport.get("from_email")
                        or "",
                    },
                )
                mail["subject"] = rendered["subject"]
                mail["body"] = rendered["body"]
                sent = send_merchant_smtp(
                    transport=transport,
                    to=str(buyer.get("email") or ""),
                    subject=rendered["subject"],
                    text=rendered["body"],
                )
                if sent.get("ok"):
                    mail["status"] = "sent"
                    mail["sent_at"] = sent.get("sent_at")
                    delivery = "smtp"
                else:
                    mail["status"] = "failed"
                    mail["error"] = sent.get("title") or sent.get("reason")
                    delivery = "smtp_failed"
        except Exception:  # noqa: BLE001 — never break checkout on mail
            delivery = "outbox_stub"

        self._append_mail(order_id, mail)

        self.track_funnel(
            "first_order" if len(orders) == 1 else "repeat_order",
            meta={"shop": order_id, "total_eur": total},
        )
        self.track_funnel("checkout_completed", meta={"shop": order_id})

        return {
            "ok": True,
            "order": record,
            "email": {
                "queued": delivery == "outbox_stub",
                "delivery": delivery,
                "message_id": mail["id"],
                "note": (
                    "Sent via merchant SMTP."
                    if delivery == "smtp"
                    else "Queued — connect SMTP + Test Email in Store Admin."
                ),
            },
            "redirect": "account.html#orders",
        }

    def list_shop_orders(self, order_id: str) -> dict[str, Any]:
        orders = self._load_orders(order_id)
        return {
            "ok": True,
            "order_id": order_id,
            "count": len(orders),
            "orders": orders,
        }

    def list_mail_outbox(self, order_id: str) -> dict[str, Any]:
        path = self._mail_path(order_id)
        messages: list[dict[str, Any]] = []
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                messages = list(data.get("messages") or [])
            except (OSError, json.JSONDecodeError):
                messages = []
        return {"ok": True, "order_id": order_id, "messages": messages}
