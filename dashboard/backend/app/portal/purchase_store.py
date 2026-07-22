"""Commercial Platform 6.4 — PurchaseStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.purchase import Purchase

ENGINE_ID = "purchase_store_v1"


class PurchaseStore(Protocol):
    def save(self, purchase: Purchase) -> None: ...

    def get(self, purchase_id: str) -> Purchase | None: ...

    def list_for_account(self, account_id: str) -> tuple[Purchase, ...]: ...


class InMemoryPurchaseStore:
    def __init__(self) -> None:
        self._rows: dict[str, Purchase] = {}

    def save(self, purchase: Purchase) -> None:
        self._rows[purchase.purchase_id] = purchase

    def get(self, purchase_id: str) -> Purchase | None:
        return self._rows.get(purchase_id)

    def list_for_account(self, account_id: str) -> tuple[Purchase, ...]:
        return tuple(
            row for row in self._rows.values() if row.account_id == account_id
        )
