"""Mission 6.2 — ProductOwnershipStore (native rows only).

Bridge-sourced ownerships are NOT stored here — they come from
WebsiteOwnershipBridge at read time.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.product_ownership import ProductOwnership

ENGINE_ID = "product_ownership_store_v1"


class ProductOwnershipStore(Protocol):
    def list_for_account(self, account_id: str) -> tuple[ProductOwnership, ...]: ...

    def save(self, ownership: ProductOwnership) -> None: ...


class InMemoryProductOwnershipStore:
    """Process-local native ProductOwnership map."""

    def __init__(self) -> None:
        self._rows: dict[str, ProductOwnership] = {}

    def list_for_account(self, account_id: str) -> tuple[ProductOwnership, ...]:
        return tuple(
            row
            for row in self._rows.values()
            if row.account_id == account_id
        )

    def save(self, ownership: ProductOwnership) -> None:
        self._rows[ownership.ownership_id] = ownership
