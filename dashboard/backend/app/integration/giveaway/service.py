"""Giveaway Basic v1 — unique link → 0€ Website Basic entitlement (not Stripe).

Law: User → Business Profile SSOT → Giveaway entitlement/order → Factory.
One successful redeem per code (v1 stream link). No second Basic from same code.
No fake 299€ Stripe charge.
"""

from __future__ import annotations

import json
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ORIGINAL_BASIC_EUR = 299.0
DEFAULT_CODE = "virtus-stream-basic"
SSOT = "customer_identity.business_profile"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class GiveawayService:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._root = memory_dir / "giveaway"
        self._codes = self._root / "codes.json"
        self._redeems = self._root / "redeems.json"
        self._root.mkdir(parents=True, exist_ok=True)

    def _load_codes(self) -> list[dict[str, Any]]:
        if not self._codes.is_file():
            return []
        try:
            data = json.loads(self._codes.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _save_codes(self, rows: list[dict[str, Any]]) -> None:
        self._codes.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def _load_redeems(self) -> list[dict[str, Any]]:
        if not self._redeems.is_file():
            return []
        try:
            data = json.loads(self._redeems.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []
        return data if isinstance(data, list) else []

    def _save_redeems(self, rows: list[dict[str, Any]]) -> None:
        self._redeems.write_text(
            json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def ensure_stream_code(self, *, label: str = "TikTok Stream Basic") -> dict[str, Any]:
        """Idempotent default stream link for owner."""
        rows = self._load_codes()
        for row in rows:
            if str(row.get("code") or "").lower() == DEFAULT_CODE:
                return row
        row = {
            "code_id": str(uuid.uuid4()),
            "code": DEFAULT_CODE,
            "label": label,
            "product": "website_basic",
            "package_id": "basic",
            "max_redeems": 1,
            "redeem_count": 0,
            "status": "active",
            "original_value_eur": ORIGINAL_BASIC_EUR,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        rows.append(row)
        self._save_codes(rows)
        return row

    def create_code(
        self,
        *,
        code: str | None = None,
        label: str = "Giveaway Basic",
        max_redeems: int = 1,
    ) -> dict[str, Any]:
        token = (code or secrets.token_urlsafe(8)).strip().lower()
        token = "".join(ch for ch in token if ch.isalnum() or ch in "-_")[:64]
        if not token:
            raise ValueError("invalid_code")
        rows = self._load_codes()
        if any(str(r.get("code") or "").lower() == token for r in rows):
            raise ValueError("code_exists")
        row = {
            "code_id": str(uuid.uuid4()),
            "code": token,
            "label": label[:120],
            "product": "website_basic",
            "package_id": "basic",
            "max_redeems": max(1, min(int(max_redeems or 1), 100)),
            "redeem_count": 0,
            "status": "active",
            "original_value_eur": ORIGINAL_BASIC_EUR,
            "created_at": _utc_now(),
            "updated_at": _utc_now(),
        }
        rows.append(row)
        self._save_codes(rows)
        return row

    def list_codes(self) -> list[dict[str, Any]]:
        self.ensure_stream_code()
        return self._load_codes()

    def get_code(self, code: str) -> dict[str, Any] | None:
        token = str(code or "").strip().lower()
        if not token:
            return None
        self.ensure_stream_code()
        for row in self._load_codes():
            if str(row.get("code") or "").lower() == token:
                return row
        return None

    def public_status(self, code: str) -> dict[str, Any]:
        row = self.get_code(code)
        if not row:
            return {"ok": False, "available": False, "reason": "code_not_found"}
        max_r = int(row.get("max_redeems") or 1)
        used = int(row.get("redeem_count") or 0)
        exhausted = used >= max_r or str(row.get("status") or "") == "exhausted"
        return {
            "ok": True,
            "available": not exhausted,
            "code": row["code"],
            "label": row.get("label"),
            "product": "Website Basic",
            "package_id": "basic",
            "original_value_eur": float(row.get("original_value_eur") or ORIGINAL_BASIC_EUR),
            "price_eur": 0.0,
            "max_redeems": max_r,
            "redeem_count": used,
            "reason": "exhausted" if exhausted else None,
            "ssot": SSOT,
        }

    def customer_has_giveaway_basic(self, customer_id: str) -> bool:
        cid = str(customer_id or "").strip()
        if not cid:
            return False
        for row in self._load_redeems():
            if str(row.get("customer_id") or "") == cid and str(row.get("package_id") or "") == "basic":
                return True
        # Also detect existing giveaway orders
        try:
            from app.integration.sales_order_service import SalesOrderService
            from app.factory.factory_service import FactoryService
            from app.integration.factory_intent_service import FactoryIntentService

            factory = FactoryService(memory_dir=self._memory)
            intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
            sales = SalesOrderService(self._memory, intent)
            for order in sales.list_orders_for_customer(customer_id=cid, limit=50):
                if (
                    str(order.get("entitlement_type") or "") == "giveaway"
                    and str(order.get("package_id") or "").lower() == "basic"
                ):
                    return True
        except Exception:
            pass
        return False

    @staticmethod
    def _profile_ready(profile: dict[str, Any] | None) -> bool:
        """Winner must fill real company facts — person name alone is not enough."""
        if not isinstance(profile, dict):
            return False
        name = str(profile.get("company_name") or "").strip()
        if len(name) < 2:
            return False
        desc = str(profile.get("description") or "").strip()
        niche = str(profile.get("niche") or "").strip()
        address = profile.get("address") if isinstance(profile.get("address"), dict) else {}
        city = str(address.get("city") or "").strip()
        services = profile.get("services") if isinstance(profile.get("services"), list) else []
        has_service = any(
            isinstance(s, dict) and str(s.get("name") or "").strip() for s in services
        )
        return bool(desc or niche or city or has_service)

    def redeem(self, code: str, *, customer_id: str) -> dict[str, Any]:
        """Auth customer claims Giveaway Basic once. Requires filled Business Profile."""
        cid = str(customer_id or "").strip()
        if not cid:
            raise ValueError("customer_required")

        row = self.get_code(code)
        if not row:
            raise ValueError("code_not_found")
        max_r = int(row.get("max_redeems") or 1)
        used = int(row.get("redeem_count") or 0)
        if used >= max_r or str(row.get("status") or "") == "exhausted":
            raise ValueError("code_exhausted")

        if self.customer_has_giveaway_basic(cid):
            raise ValueError("already_redeemed")

        from app.integration.customer_identity.service import CustomerIdentityService

        identity = CustomerIdentityService(self._memory)
        identity.ensure_business_profile(cid)
        profile = identity.get_business_profile(cid)
        if not self._profile_ready(profile):
            return {
                "ok": False,
                "need_profile": True,
                "next": f"/client/business-profile?next=/giveaway/{row['code']}",
                "message": "Bitte zuerst das Unternehmensprofil ausfüllen.",
                "code": row["code"],
            }

        assert profile is not None
        contacts = profile.get("contacts") if isinstance(profile.get("contacts"), dict) else {}
        address = profile.get("address") if isinstance(profile.get("address"), dict) else {}
        services = profile.get("services") if isinstance(profile.get("services"), list) else []
        service_names = [
            str(s.get("name") or "").strip()
            for s in services
            if isinstance(s, dict) and str(s.get("name") or "").strip()
        ]

        me = identity.me(cid)
        email = (
            str((me.get("account") or {}).get("email") or "").strip()
            or str(contacts.get("email") or "").strip()
        )

        from app.factory.factory_service import FactoryService
        from app.integration.factory_intent_service import FactoryIntentService
        from app.integration.sales_order_service import SalesOrderService

        factory = FactoryService(memory_dir=self._memory)
        intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
        sales = SalesOrderService(self._memory, intent)

        create = sales.create_order(
            {
                "package_id": "basic",
                "customer_id": cid,
                "business_name": str(profile.get("company_name") or "").strip(),
                "description": str(profile.get("description") or "").strip()
                or f"Website Basic Giveaway — {profile.get('company_name')}",
                "city": str(address.get("city") or "").strip(),
                "phone": str(contacts.get("phone") or "").strip(),
                "whatsapp": str(contacts.get("whatsapp") or "").strip(),
                "email": email,
                "niche": str(profile.get("niche") or "").strip() or None,
                "services_list": service_names,
                "market_code": str(profile.get("market") or "DE"),
                "ui_lang": str(profile.get("language") or "de"),
                "language": str(profile.get("language") or "de"),
            }
        )
        order_id = str(create.get("order_id") or "")
        if not order_id:
            raise ValueError("order_create_failed")

        order = sales.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")

        now = _utc_now()
        order["status"] = "paid"
        order["status_label"] = "Giveaway · Website Basic"
        order["paid_at"] = now
        order["price_eur"] = 0.0
        order["price_label"] = "0 € (Giveaway)"
        order["listed_price_eur"] = ORIGINAL_BASIC_EUR
        order["original_value_eur"] = ORIGINAL_BASIC_EUR
        order["entitlement_type"] = "giveaway"
        order["payment_status"] = "not_required"
        order["payment_mode"] = "giveaway"
        order["payment_provider"] = "giveaway"
        order["demo"] = False
        order["is_demo"] = False
        order["giveaway_code"] = row["code"]
        order["giveaway_code_id"] = row["code_id"]
        order["client_status_message"] = (
            "Giveaway: Website Basic (299 €) — 0 €. Keine Stripe-Zahlung. "
            "Virtus erzeugt Ihre Website aus dem Business Profile."
        )
        order["updated_at"] = now
        sales._save_order(order)

        # Consume code before Factory so entitlement cannot double-issue on Factory retry.
        rows = self._load_codes()
        for i, r in enumerate(rows):
            if str(r.get("code_id")) == str(row["code_id"]):
                r["redeem_count"] = int(r.get("redeem_count") or 0) + 1
                if r["redeem_count"] >= int(r.get("max_redeems") or 1):
                    r["status"] = "exhausted"
                r["updated_at"] = now
                r["last_redeem_customer_id"] = cid
                r["last_order_id"] = order_id
                rows[i] = r
                row = r
                break
        self._save_codes(rows)

        redeems = self._load_redeems()
        redeems.append(
            {
                "redeem_id": str(uuid.uuid4()),
                "code_id": row["code_id"],
                "code": row["code"],
                "customer_id": cid,
                "order_id": order_id,
                "package_id": "basic",
                "profile_id": profile.get("profile_id"),
                "at": now,
            }
        )
        self._save_redeems(redeems)

        production: dict[str, Any] = {}
        try:
            production = sales.start_production(order_id)
        except Exception as exc:
            fresh = sales.get_order(order_id) or order
            fresh["status"] = "in_production"
            fresh["factory_error"] = str(exc)[:500]
            fresh["client_status_message"] = (
                "Giveaway aktiv · Website Basic wird vorbereitet. "
                "Preview/ZIP erscheinen, sobald Factory fertig ist."
            )
            fresh["updated_at"] = _utc_now()
            sales._save_order(fresh)
            order = fresh
            production = {"ok": False, "error": str(exc)[:200]}

        return {
            "ok": True,
            "need_profile": False,
            "order_id": order_id,
            "product_id": (production.get("product_id") if isinstance(production, dict) else None)
            or order.get("product_id"),
            "package_id": "basic",
            "entitlement_type": "giveaway",
            "price_eur": 0.0,
            "original_value_eur": ORIGINAL_BASIC_EUR,
            "payment_status": "not_required",
            "code": row["code"],
            "code_exhausted": str(row.get("status")) == "exhausted",
            "factory_ok": bool(
                (production.get("ok") if isinstance(production, dict) else False)
                or (production.get("product_id") if isinstance(production, dict) else False)
            ),
            "next": f"/client/products?order={order_id}",
            "message": "Website Basic Giveaway gestartet — öffnen Sie Ihr Kabinett.",
        }
