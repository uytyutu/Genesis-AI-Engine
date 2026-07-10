"""File store for customer identity (M2)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from app.integration.customer_identity.schema import (
    CustomerAccount,
    CustomerCard,
    DigitalCompany,
    MarketingConsent,
    WelcomeSession,
)

_EMAIL_SAFE = re.compile(r"[^a-z0-9@._+-]", re.I)


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

    def email_index_path(self, email: str) -> Path:
        normalized = email.strip().lower()
        safe = _EMAIL_SAFE.sub("_", normalized)[:120]
        return self._index / f"email_{safe}.txt"

    def find_customer_by_email(self, email: str) -> str | None:
        path = self.email_index_path(email)
        if not path.is_file():
            return None
        return path.read_text(encoding="utf-8").strip() or None

    def bind_email(self, email: str, customer_id: str) -> None:
        self.email_index_path(email).write_text(customer_id, encoding="utf-8")

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

    def load_card(self, customer_id: str) -> CustomerCard | None:
        path = self._cards / f"{customer_id}.json"
        if not path.is_file():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        marketing = data.pop("marketing", {})
        card = CustomerCard(**data)
        card.marketing = MarketingConsent(**marketing) if marketing else MarketingConsent()
        return card

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
