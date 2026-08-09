"""File store for customer identity (M2)."""

from __future__ import annotations

import json
import re
from dataclasses import fields
from pathlib import Path

from app.integration.customer_identity.business_id import normalize_business_id
from app.integration.customer_identity.schema import (
    CustomerAccount,
    CustomerCard,
    DigitalCompany,
    MarketingConsent,
    WelcomeSession,
)

_EMAIL_SAFE = re.compile(r"[^a-z0-9@._+-]", re.I)
_ID_SAFE = re.compile(r"[^a-zA-Z0-9_-]+")


class CustomerIdentityStore:
    def __init__(self, memory_dir: Path) -> None:
        self._root = memory_dir / "customer_identity"
        self._accounts = self._root / "accounts"
        self._cards = self._root / "cards"
        self._companies = self._root / "companies"
        self._welcome = self._root / "welcome"
        self._index = self._root / "index"
        for d in (self._accounts, self._cards, self._companies, self._welcome, self._index):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    def email_index_path(self, email: str) -> Path:
        normalized = email.strip().lower()
        safe = _EMAIL_SAFE.sub("_", normalized)[:120]
        return self._index / f"email_{safe}.txt"

    def business_index_path(self, business_id: str) -> Path:
        bid = normalize_business_id(business_id)
        safe = _ID_SAFE.sub("_", bid)[:64]
        return self._index / f"business_{safe}.txt"

    def find_customer_by_email(self, email: str) -> str | None:
        path = self.email_index_path(email)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip() or None

    def find_customer_by_business_id(self, business_id: str) -> str | None:
        path = self.business_index_path(business_id)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip() or None

    def bind_email(self, email: str, customer_id: str) -> None:
        self.email_index_path(email).write_text(customer_id, encoding="utf-8")

    def bind_business_id(self, business_id: str, customer_id: str) -> None:
        bid = normalize_business_id(business_id)
        if not bid:
            return
        self.business_index_path(bid).write_text(customer_id, encoding="utf-8")

    def save_account(self, account: CustomerAccount) -> None:
        path = self._accounts / f"{account.customer_id}.json"
        path.write_text(json.dumps(account.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self.bind_email(account.email, account.customer_id)

    def load_account(self, customer_id: str) -> CustomerAccount | None:
        path = self._accounts / f"{customer_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return CustomerAccount(**data)

    def save_card(self, card: CustomerCard) -> None:
        path = self._cards / f"{card.customer_id}.json"
        payload = card.to_dict()
        payload["marketing"] = card.marketing.to_dict()
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if card.business_id:
            self.bind_business_id(card.business_id, card.customer_id)

    def load_card(self, customer_id: str) -> CustomerCard | None:
        path = self._cards / f"{customer_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        marketing = data.pop("marketing", {})
        known = {f.name for f in fields(CustomerCard)}
        filtered = {k: v for k, v in data.items() if k in known}
        card = CustomerCard(**filtered)
        card.marketing = (
            MarketingConsent(**marketing) if isinstance(marketing, dict) else MarketingConsent()
        )
        return card

    def iter_cards(self, *, limit: int = 500) -> list[CustomerCard]:
        rows: list[CustomerCard] = []
        for path in sorted(self._cards.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            cid = path.stem
            card = self.load_card(cid)
            if card:
                rows.append(card)
            if len(rows) >= limit:
                break
        return rows

    def search_clients(self, query: str, *, limit: int = 20) -> list[CustomerCard]:
        q = str(query or "").strip().lower()
        if not q:
            return []
        bid = normalize_business_id(query)
        if bid.startswith("VC-") and len(bid) >= 10:
            cid = self.find_customer_by_business_id(bid)
            if cid:
                card = self.load_card(cid)
                return [card] if card else []
        email_hit = self.find_customer_by_email(q)
        if email_hit:
            card = self.load_card(email_hit)
            if card:
                return [card]

        hits: list[CustomerCard] = []
        for card in self.iter_cards(limit=800):
            company = self.load_company_by_customer(card.customer_id)
            blob = " ".join(
                [
                    card.business_id or "",
                    card.customer_id,
                    card.email or "",
                    card.name or "",
                    card.phone or "",
                    card.company_display_name or "",
                    company.name if company else "",
                    card.country or "",
                ]
            ).lower()
            if q in blob:
                hits.append(card)
            if len(hits) >= limit:
                break
        return hits

    def save_company(self, company: DigitalCompany) -> None:
        path = self._companies / f"{company.company_id}.json"
        path.write_text(json.dumps(company.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load_company_by_customer(self, customer_id: str) -> DigitalCompany | None:
        for path in self._companies.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            if data.get("customer_id") == customer_id:
                return DigitalCompany(**data)
        return None

    def save_welcome(self, session: WelcomeSession) -> None:
        path = self._welcome / f"{session.customer_id}.json"
        path.write_text(json.dumps(session.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def load_welcome(self, customer_id: str) -> WelcomeSession | None:
        path = self._welcome / f"{customer_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return WelcomeSession(**data)
