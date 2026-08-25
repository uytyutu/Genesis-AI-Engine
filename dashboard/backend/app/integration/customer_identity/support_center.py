"""Gen1 Support Center — Client Card, timeline, tickets (not Gen2 CRM)."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.customer_identity.business_id import (
    generate_business_id,
    normalize_business_id,
)
from app.integration.customer_identity.schema import CustomerCard, MarketingConsent
from app.integration.customer_identity.store import CustomerIdentityStore

_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_id(value: str) -> str:
    return _SAFE.sub("_", value.strip())[:80] or "unknown"


class SupportCenterService:
    """Owner-facing client support hub keyed by Business ID."""

    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._store = CustomerIdentityStore(self._memory)
        self._timeline = self._store.root / "timeline"
        self._tickets = self._store.root / "tickets"
        self._timeline.mkdir(parents=True, exist_ok=True)
        self._tickets.mkdir(parents=True, exist_ok=True)

    def ensure_business_id(self, card: CustomerCard) -> CustomerCard:
        if normalize_business_id(card.business_id):
            card.business_id = normalize_business_id(card.business_id)
            self._store.bind_business_id(card.business_id, card.customer_id)
            return card
        for _ in range(8):
            bid = generate_business_id()
            existing = self._store.find_customer_by_business_id(bid)
            if existing and existing != card.customer_id:
                continue
            card.business_id = bid
            self._store.save_card(card)
            self.append_timeline(
                card.customer_id,
                kind="business_id_assigned",
                summary=f"Business ID {bid}",
                ref_type="business_id",
                ref_id=bid,
            )
            return card
        raise RuntimeError("Could not allocate unique Business ID")

    def backfill_missing_ids(self, *, limit: int = 500) -> int:
        n = 0
        for card in self._store.iter_cards(limit=limit):
            if normalize_business_id(card.business_id):
                self._store.bind_business_id(card.business_id, card.customer_id)
                continue
            self.ensure_business_id(card)
            n += 1
        return n

    @staticmethod
    def _is_demo_test_user(*, email: str = "", name: str = "", company: str = "") -> bool:
        blob = f"{email} {name} {company}".lower()
        markers = (
            "@test.",
            "virtuscore-test",
            "example.com",
            "example.de",
            "+test",
            "golden.",
            "gwt-",
            "b3-review",
            "rc1-cert",
            "live.d+",
            "@test.local",
        )
        return any(m in blob for m in markers)

    def _order_activity_index(self) -> dict[str, dict[str, Any]]:
        """customer_id|email → order/product activity (from sales_orders SSOT)."""
        index: dict[str, dict[str, Any]] = {}
        path = self._memory / "sales_orders.json"
        orders: list[dict[str, Any]] = []
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = None
            if isinstance(data, list):
                orders = [o for o in data if isinstance(o, dict)]
            elif isinstance(data, dict):
                if isinstance(data.get("orders"), list):
                    orders = [o for o in data["orders"] if isinstance(o, dict)]
                else:
                    orders = [v for v in data.values() if isinstance(v, dict)]
        root = self._memory / "sales_orders"
        if root.is_dir():
            for p in root.glob("*.json"):
                try:
                    row = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(row, dict):
                    orders.append(row)

        def _touch(key: str, order: dict[str, Any]) -> None:
            if not key:
                return
            slot = index.setdefault(
                key,
                {
                    "orders_count": 0,
                    "products_count": 0,
                    "last_order_id": None,
                    "last_order_at": "",
                    "last_order_status": None,
                    "last_package": None,
                },
            )
            slot["orders_count"] = int(slot["orders_count"]) + 1
            slot["products_count"] = int(slot["products_count"]) + 1
            at = str(
                order.get("paid_at")
                or order.get("updated_at")
                or order.get("created_at")
                or ""
            )
            if at >= str(slot.get("last_order_at") or ""):
                slot["last_order_at"] = at
                slot["last_order_id"] = order.get("order_id")
                slot["last_order_status"] = order.get("status")
                slot["last_package"] = (
                    order.get("package_name") or order.get("package_id") or None
                )

        for order in orders:
            cid = str(order.get("customer_id") or "").strip()
            em = str(order.get("email") or "").strip().lower()
            if cid:
                _touch(f"id:{cid}", order)
            if em:
                _touch(f"em:{em}", order)
        return index

    def _user_row(
        self,
        card: CustomerCard,
        *,
        activity: dict[str, dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        card = self.ensure_business_id(card)
        company = self._store.load_company_by_customer(card.customer_id)
        company_name = (company.name if company else card.company_display_name) or ""
        account = self._store.load_account(card.customer_id)
        act_map = activity if activity is not None else self._order_activity_index()
        act = act_map.get(f"id:{card.customer_id}") or act_map.get(
            f"em:{str(card.email or '').strip().lower()}"
        ) or {}
        demo = self._is_demo_test_user(
            email=str(card.email or ""),
            name=str(card.name or ""),
            company=str(company_name),
        )
        return {
            "customer_id": card.customer_id,
            "business_id": card.business_id,
            "name": card.name,
            "email": card.email,
            "phone": card.phone,
            "company": company_name or None,
            "country": card.country or (account.country if account else "") or None,
            "registered_at": card.registered_at
            or (account.created_at if account else "")
            or "",
            "last_activity_at": card.last_activity_at
            or (account.last_login_at if account else "")
            or act.get("last_order_at")
            or "",
            "account_status": card.account_status or "active",
            "products_count": int(act.get("products_count") or 0),
            "orders_count": int(act.get("orders_count") or 0),
            "last_order_id": act.get("last_order_id"),
            "last_order_status": act.get("last_order_status"),
            "last_package": act.get("last_package"),
            "is_demo_test": demo,
            "layer": "demo_test" if demo else "customer",
        }

    def list_users(
        self,
        *,
        query: str = "",
        limit: int = 50,
        include_demo_test: bool = True,
    ) -> dict[str, Any]:
        """Owner Users desk — registered customers from identity SSOT (not a parallel DB)."""
        self.backfill_missing_ids(limit=500)
        q = str(query or "").strip()
        activity = self._order_activity_index()
        cards = (
            self._store.search_clients(q, limit=max(limit, 1))
            if q
            else self._store.iter_cards(limit=max(limit, 1))
        )
        rows: list[dict[str, Any]] = []
        demo_hidden = 0
        for card in cards:
            row = self._user_row(card, activity=activity)
            if row["is_demo_test"] and not include_demo_test:
                demo_hidden += 1
                continue
            rows.append(row)
            if len(rows) >= limit:
                break
        rows.sort(
            key=lambda r: str(r.get("last_activity_at") or r.get("registered_at") or ""),
            reverse=True,
        )
        return {
            "ok": True,
            "module": "owner_users_v1",
            "query": q,
            "count": len(rows),
            "demo_test_hidden": demo_hidden,
            "users": rows,
            "empty": len(rows) == 0,
            "empty_message_de": (
                "Kein Kunde gefunden." if q else "Noch keine Kunden registriert."
            ),
            "quelle_de": "customer_identity cards + sales_orders (activity only)",
        }

    def lookup(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        q = str(query or "").strip()
        if not q:
            return []
        listed = self.list_users(query=q, limit=limit, include_demo_test=True)
        return list(listed.get("users") or [])

    def build_client_card(self, customer_id: str) -> dict[str, Any] | None:
        card = self._store.load_card(customer_id)
        if not card:
            return None
        card = self.ensure_business_id(card)
        account = self._store.load_account(customer_id)
        company = self._store.load_company_by_customer(customer_id)

        orders: list[dict[str, Any]] = []
        try:
            from app.factory.factory_service import FactoryService
            from app.integration.factory_intent_service import FactoryIntentService
            from app.integration.sales_order_service import SalesOrderService

            factory = FactoryService(memory_dir=self._memory)
            intent = FactoryIntentService(memory_dir=self._memory, factory=factory)
            sales = SalesOrderService(self._memory, intent)
            orders = sales.list_orders_for_customer(
                customer_id=customer_id,
                email=card.email,
                limit=50,
            )
        except Exception:
            orders = []
        if not orders:
            orders = self._scan_orders_fallback(customer_id, card.email)

        products = self._summarize_products(orders)
        websites = self._website_rows(orders)
        commerce = self._commerce_snapshot(orders)
        tickets = self.list_tickets(customer_id)
        timeline = self.list_timeline(customer_id, limit=40)
        company_name = (company.name if company else card.company_display_name) or ""
        demo = self._is_demo_test_user(
            email=str(card.email or ""),
            name=str(card.name or ""),
            company=str(company_name),
        )

        business_profile_payload: dict[str, Any] = {
            "ok": True,
            "has_profile": False,
            "profile": None,
            "ssot": "customer_identity.business_profile",
            "note": "Business Profile not filled yet — Order/Giveaway should create via upsert, not a second entity.",
        }
        try:
            from app.integration.customer_identity.service import CustomerIdentityService

            business_profile_payload = CustomerIdentityService(self._memory).business_profile_read(
                customer_id
            )
            bp = business_profile_payload.get("profile") if isinstance(business_profile_payload, dict) else None
            if isinstance(bp, dict) and bp.get("company_name"):
                company_name = str(bp.get("company_name") or company_name)
        except Exception:
            pass

        owner_actions: list[dict[str, Any]] = [
            {
                "id": "open_users",
                "label": "Users desk",
                "href": f"/users?id={card.customer_id}",
            },
            {
                "id": "open_orders",
                "label": "Orders",
                "href": "/orders",
            },
            {
                "id": "open_products",
                "label": "Products / Factory",
                "href": "/factory",
            },
            {
                "id": "open_support",
                "label": "Support",
                "href": "/support",
            },
            {
                "id": "email_client",
                "label": "Email client",
                "href": f"mailto:{card.email}" if card.email else None,
            },
            {"id": "add_note", "label": "Add support note"},
            {"id": "open_ticket", "label": "Create ticket"},
        ]
        for site in websites:
            if site.get("preview_href"):
                owner_actions.append(
                    {
                        "id": f"preview-{site.get('order_id')}",
                        "label": f"Preview · {site.get('package') or site.get('order_id')}",
                        "href": site["preview_href"],
                        "external": True,
                    }
                )
            if site.get("download_href"):
                owner_actions.append(
                    {
                        "id": f"zip-{site.get('order_id')}",
                        "label": f"ZIP · {site.get('order_id')}",
                        "href": site["download_href"],
                        "external": True,
                    }
                )
            if site.get("order_href"):
                owner_actions.append(
                    {
                        "id": f"order-{site.get('order_id')}",
                        "label": f"Order · {site.get('order_id')}",
                        "href": site["order_href"],
                    }
                )

        return {
            "ok": True,
            "title": "Owner User Card",
            "module": "owner_users_v1",
            "business_id": card.business_id,
            "customer_id": card.customer_id,
            "is_demo_test": demo,
            "layer": "demo_test" if demo else "customer",
            "chain": {
                "user": card.customer_id,
                "customer": card.customer_id,
                "orders": [o.get("order_id") for o in orders if o.get("order_id")],
                "products": [p.get("order_id") for p in products if p.get("order_id")],
                "websites": [w.get("order_id") for w in websites if w.get("order_id")],
                "support": f"/users?id={card.customer_id}",
            },
            "profile": {
                "name": card.name,
                "email": card.email,
                "phone": card.phone,
                "company": company_name,
                "country": card.country or (account.country if account else ""),
                "locale": card.locale or (account.locale if account else ""),
                "registered_at": card.registered_at or (account.created_at if account else ""),
                "last_activity_at": card.last_activity_at
                or (account.last_login_at if account else ""),
                "account_status": card.account_status,
                "tier": card.tier,
            },
            "business_profile": business_profile_payload,
            "products": products,
            "websites": websites,
            "orders": orders,
            "finance": {
                "payments": [
                    {
                        "order_id": o.get("order_id"),
                        "status": o.get("status"),
                        "package": o.get("package_name") or o.get("package_id"),
                        "amount": o.get("amount_eur") or o.get("price_eur"),
                        "paid_at": o.get("paid_at"),
                        "payment_mode": o.get("payment_mode"),
                        "entitlement_type": o.get("entitlement_type"),
                        "is_giveaway": bool(o.get("is_giveaway"))
                        or str(o.get("entitlement_type") or "") == "giveaway",
                        "href": f"/orders#{o.get('order_id')}" if o.get("order_id") else None,
                    }
                    for o in orders
                ],
                "note": (
                    "References only — REAL revenue lives in Finance Ledger. "
                    "Giveaway = 0 € entitlement (not Stripe). Demo/test marked separately."
                ),
            },
            "commerce": commerce,
            "domains": [
                {
                    "order_id": o.get("order_id"),
                    "domain": o.get("domain") or o.get("preferred_domain"),
                    "publish_status": o.get("publish_status") or o.get("status"),
                    "published_at": o.get("published_at"),
                }
                for o in orders
                if o.get("domain") or o.get("preferred_domain") or o.get("published_at")
            ],
            "vector": {
                "platform_visitor_id": card.platform_visitor_id,
                "interests": card.interests,
                "note": "Setup progress lives in Vector / store admin guidance.",
            },
            "support": {
                "notes": list(card.support_notes or [])[-30:],
                "tickets": tickets,
            },
            "timeline": timeline,
            "actions": owner_actions,
            "updated_at": _now(),
        }

    def add_note(
        self,
        customer_id: str,
        text: str,
        *,
        author: str = "owner",
    ) -> dict[str, Any] | None:
        card = self._store.load_card(customer_id)
        if not card:
            return None
        card = self.ensure_business_id(card)
        note = {
            "note_id": f"note-{uuid.uuid4().hex[:10]}",
            "at": _now(),
            "author": str(author or "owner")[:64],
            "text": str(text or "").strip()[:4000],
        }
        if not note["text"]:
            return None
        notes = list(card.support_notes or [])
        notes.append(note)
        card.support_notes = notes[-100:]
        card.last_activity_at = note["at"]
        self._store.save_card(card)
        self.append_timeline(
            customer_id,
            kind="support_note",
            summary=note["text"][:120],
            ref_type="note",
            ref_id=note["note_id"],
        )
        return note

    def create_ticket(
        self,
        customer_id: str,
        *,
        subject: str,
        body: str = "",
        status: str = "open",
    ) -> dict[str, Any] | None:
        card = self._store.load_card(customer_id)
        if not card:
            return None
        card = self.ensure_business_id(card)
        ticket_id = f"SUP-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": customer_id,
            "business_id": card.business_id,
            "subject": str(subject or "").strip()[:200] or "Support",
            "body": str(body or "").strip()[:8000],
            "status": status if status in {"open", "waiting", "closed"} else "open",
            "created_at": _now(),
            "updated_at": _now(),
            "notes": [],
        }
        path = self._tickets / f"{_safe_id(ticket_id)}.json"
        path.write_text(json.dumps(ticket, ensure_ascii=False, indent=2), encoding="utf-8")
        self.append_timeline(
            customer_id,
            kind="ticket_opened",
            summary=ticket["subject"],
            ref_type="ticket",
            ref_id=ticket_id,
        )
        return ticket

    def list_tickets(self, customer_id: str) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        for path in self._tickets.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict) and data.get("customer_id") == customer_id:
                rows.append(data)
        rows.sort(key=lambda r: str(r.get("updated_at") or ""), reverse=True)
        return rows[:50]

    def append_timeline(
        self,
        customer_id: str,
        *,
        kind: str,
        summary: str,
        ref_type: str = "",
        ref_id: str = "",
    ) -> dict[str, Any]:
        event = {
            "event_id": f"evt-{uuid.uuid4().hex[:12]}",
            "at": _now(),
            "kind": str(kind)[:64],
            "summary": str(summary)[:300],
            "ref_type": str(ref_type)[:32],
            "ref_id": str(ref_id)[:80],
        }
        path = self._timeline / f"{_safe_id(customer_id)}.jsonl"
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
        return event

    def list_timeline(self, customer_id: str, *, limit: int = 40) -> list[dict[str, Any]]:
        path = self._timeline / f"{_safe_id(customer_id)}.jsonl"
        if not path.is_file():
            return []
        rows: list[dict[str, Any]] = []
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        for line in lines[-max(limit, 1) :]:
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(data, dict):
                rows.append(data)
        rows.reverse()
        return rows[:limit]

    def record_registration(self, card: CustomerCard) -> None:
        card = self.ensure_business_id(card)
        self.append_timeline(
            card.customer_id,
            kind="registered",
            summary=f"Registered · {card.email}",
            ref_type="customer",
            ref_id=card.customer_id,
        )

    @staticmethod
    def _website_rows(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Website products with owner Preview / ZIP links (API paths)."""
        rows: list[dict[str, Any]] = []
        for o in orders:
            kind = str(o.get("product_kind") or o.get("kind") or "").lower()
            pid = str(o.get("package_id") or o.get("product_id") or "").lower()
            name = str(o.get("package_name") or o.get("product_name") or "")
            blob = f"{kind} {pid} {name}".lower()
            if any(x in blob for x in ("store", "shop", "aistore", "bot", "employee")):
                continue
            oid = str(o.get("order_id") or "")
            product_id = str(o.get("product_id") or "").strip()
            download_ready = bool(o.get("download_ready"))
            is_giveaway = bool(o.get("is_giveaway")) or str(
                o.get("entitlement_type") or ""
            ) == "giveaway"
            rows.append(
                {
                    "order_id": oid,
                    "product_id": product_id or None,
                    "package": name or pid,
                    "status": o.get("status"),
                    "download_ready": download_ready,
                    "is_giveaway": is_giveaway,
                    "entitlement_type": o.get("entitlement_type")
                    or ("giveaway" if is_giveaway else None),
                    "payment_mode": o.get("payment_mode"),
                    "original_value_eur": o.get("original_value_eur"),
                    "price_eur": o.get("price_eur"),
                    "giveaway_code": o.get("giveaway_code"),
                    "factory_label": (
                        "Ready"
                        if download_ready or str(o.get("status") or "") == "ready"
                        else (
                            "In production"
                            if str(o.get("status") or "")
                            in ("paid", "in_production")
                            else str(o.get("status") or "")
                        )
                    ),
                    "order_href": f"/orders#{oid}" if oid else None,
                    "preview_href": (
                        f"/api/factory/products/{product_id}/preview" if product_id else None
                    ),
                    "download_href": (
                        f"/api/sales/orders/{oid}/download"
                        if oid and download_ready
                        else None
                    ),
                }
            )
        return rows

    @staticmethod
    def _summarize_products(orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for o in orders:
            kind = str(o.get("product_kind") or o.get("kind") or "").lower()
            pid = str(o.get("package_id") or o.get("product_id") or "").lower()
            name = str(o.get("package_name") or o.get("product_name") or o.get("title") or "")
            blob = f"{kind} {pid} {name}".lower()
            if any(x in blob for x in ("store", "shop", "aistore")):
                label = "AI Store"
                icon = "store"
            elif "bot" in blob or "employee" in blob:
                label = "Digital Employee"
                icon = "bot"
            else:
                label = "Website"
                icon = "website"
            items.append(
                {
                    "label": label,
                    "icon": icon,
                    "order_id": o.get("order_id"),
                    "status": o.get("status"),
                    "package": name or pid,
                    "paid_at": o.get("paid_at"),
                    "published_at": o.get("published_at"),
                    "is_giveaway": bool(o.get("is_giveaway"))
                    or str(o.get("entitlement_type") or "") == "giveaway",
                    "entitlement_type": o.get("entitlement_type"),
                    "payment_mode": o.get("payment_mode"),
                }
            )
        return items

    def _commerce_snapshot(self, orders: list[dict[str, Any]]) -> dict[str, Any]:
        store_orders = [
            o
            for o in orders
            if any(
                x
                in str(
                    o.get("product_kind") or o.get("package_id") or o.get("package_name") or ""
                ).lower()
                for x in ("store", "shop")
            )
        ]
        snapshots: list[dict[str, Any]] = []
        for o in store_orders[:10]:
            oid = str(o.get("order_id") or "")
            snap: dict[str, Any] = {
                "order_id": oid,
                "stripe": None,
                "shipping": None,
                "smtp": None,
            }
            admin = self._memory / "store_admin" / oid
            commerce_path = admin / "commerce.json"
            if commerce_path.is_file():
                try:
                    data = json.loads(commerce_path.read_text(encoding="utf-8"))
                    if isinstance(data, dict):
                        snap["stripe"] = bool(
                            data.get("stripe_connected")
                            or (data.get("stripe") or {}).get("connected")
                        )
                        snap["smtp"] = bool(
                            data.get("smtp_ready") or (data.get("email") or {}).get("tested")
                        )
                        snap["shipping"] = bool(
                            data.get("shipping_ready")
                            or (data.get("shipping") or {}).get("connected")
                        )
                except (OSError, json.JSONDecodeError):
                    pass
            snapshots.append(snap)
        return {"stores": snapshots}

    def _scan_orders_fallback(self, customer_id: str, email: str) -> list[dict[str, Any]]:
        cid = customer_id.strip()
        em = email.strip().lower()
        rows: list[dict[str, Any]] = []

        def _consider(order: dict[str, Any]) -> None:
            oid_cid = str(order.get("customer_id") or "").strip()
            oid_email = str(order.get("email") or "").strip().lower()
            if cid and oid_cid == cid:
                rows.append(order)
            elif em and oid_email == em and not oid_cid:
                rows.append(order)

        path = self._memory / "sales_orders.json"
        if path.is_file():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                data = None
            orders: list[Any] = []
            if isinstance(data, list):
                orders = data
            elif isinstance(data, dict):
                if isinstance(data.get("orders"), list):
                    orders = data["orders"]
                else:
                    orders = list(data.values())
            for order in orders:
                if isinstance(order, dict):
                    _consider(order)

        root = self._memory / "sales_orders"
        if root.is_dir():
            for p in root.glob("*.json"):
                try:
                    order = json.loads(p.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                if isinstance(order, dict):
                    _consider(order)

        # de-dupe
        seen: set[str] = set()
        unique: list[dict[str, Any]] = []
        for o in rows:
            oid = str(o.get("order_id") or "")
            if oid and oid in seen:
                continue
            if oid:
                seen.add(oid)
            unique.append(o)
        unique.sort(key=lambda o: str(o.get("created_at") or ""), reverse=True)
        return unique[:50]
