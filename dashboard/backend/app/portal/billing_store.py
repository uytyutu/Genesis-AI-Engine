"""Commercial Platform 6.6 — BillingStore (financial ledger only)."""

from __future__ import annotations

from typing import Protocol

from app.portal.billing import BillingTransaction

ENGINE_ID = "billing_store_v1"


class BillingStore(Protocol):
    def save(self, row: BillingTransaction) -> None: ...

    def get(self, transaction_id: str) -> BillingTransaction | None: ...

    def list_for_account(
        self, account_id: str
    ) -> tuple[BillingTransaction, ...]: ...


class InMemoryBillingStore:
    def __init__(self) -> None:
        self._rows: dict[str, BillingTransaction] = {}

    def save(self, row: BillingTransaction) -> None:
        self._rows[row.transaction_id] = row

    def get(self, transaction_id: str) -> BillingTransaction | None:
        return self._rows.get(transaction_id)

    def list_for_account(
        self, account_id: str
    ) -> tuple[BillingTransaction, ...]:
        return tuple(
            row for row in self._rows.values() if row.account_id == account_id
        )
