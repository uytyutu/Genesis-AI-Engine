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

    def lookup(self, query: str, *, limit: int = 20) -> list[dict[str, Any]]:
        q = str(query or "").strip()
        if not q:
            return []
        hits = self._store.search_clients(q, limit=limit)
        out: list[dict[str, Any]] = []
        for card in hits:
            card = self.ensure_business_id(card)
            company = self._store.load_company_by_customer(card.customer_id)
            out.append(
                {
                    "customer_id": card.customer_id,
                    "business_id": card.business_id,
                    "name": card.name,
                    "email": card.email,
                    "phone": card.phone,
                    "company": (company.name if company else card.company_display_name)
                    or None,
                    "country": card.country,
                    "registered_at": card.registered_at,
                    "account_status": card.account_status,
                }
            )
        return out

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
            orders = self._scan_orders_fallback(customer_id, card.email)

        products = self._summarize_products(orders)
        commerce = self._commerce_snapshot(orders)
        tickets = self.list_tickets(customer_id)
        timeline = self.list_timeline(customer_id, limit=40)

        return {
            "ok": True,
            "title": "Client Card",
            "business_id": card.business_id,
            "customer_id": card.customer_id,
            "profile": {
                "name": card.name,
                "email": card.email,
                "phone": card.phone,
                "company": (company.name if company else card.company_display_name) or "",
                "country": card.country or (account.country if account else ""),
                "locale": card.locale or (account.locale if account else ""),
                "registered_at": card.registered_at or (account.created_at if account else ""),
                "last_activity_at": card.last_activity_at
                or (account.last_login_at if account else ""),
                "account_status": card.account_status,
                "tier": card.tier,
            },
            "products": products,
            "orders": orders,
            "finance": {
                "payments": [
                    {
                        "order_id": o.get("order_id"),
                        "status": o.get("status"),
                        "package": o.get("package_name") or o.get("package_id"),
                        "amount": o.get("amount_eur") or o.get("price_eur"),
                        "paid_at": o.get("paid_at"),
                    }
                    for o in orders
                ],
                "note": "Virtus never takes shop buyer funds — merchant Stripe only.",
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
            "actions": [
                {"id": "copy_business_id", "label": "Copy Business ID"},
                {"id": "email_client", "label": "Email client", "href": f"mailto:{card.email}"},
                {"id": "add_note", "label": "Add support note"},
                {"id": "open_ticket", "label": "Create ticket"},
            ],
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
        root = self._memory / "sales_orders"
        if not root.is_dir():
            return []
        cid = customer_id.strip()
        em = email.strip().lower()
        rows: list[dict[str, Any]] = []
        for path in root.glob("*.json"):
            try:
                order = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(order, dict):
                continue
            if cid and str(order.get("customer_id") or "") == cid:
                rows.append(order)
            elif em and str(order.get("email") or "").strip().lower() == em:
                rows.append(order)
        rows.sort(key=lambda o: str(o.get("created_at") or ""), reverse=True)
        return rows[:50]
