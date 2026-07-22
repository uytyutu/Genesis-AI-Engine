"""Mission 6.3 — ProductActivationStore (codes + activation audit).

Temporary seed / code directory — replaceable by purchase provider later.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.product_activation import ProductActivationRecord

ENGINE_ID = "product_activation_store_v1"

# Temporary activators — not billing. Replaceable without API change.
DEFAULT_ACTIVATION_CODES: dict[str, str] = {
    "DEMO-CHATBOT": "prod_chatbot",
    "DEMO-ANALYTICS": "prod_analytics",
    "DEMO-CRM": "prod_crm",
    "INTERNAL-SEED": "*",  # any available catalog product (test/seed channel)
}


class ProductActivationStore(Protocol):
    def resolve_code(self, code: str) -> str | None:
        """Return catalog product_id, '*' for any, or None if invalid."""
        ...

    def save_activation(self, record: ProductActivationRecord) -> None: ...

    def list_for_account(
        self, account_id: str
    ) -> tuple[ProductActivationRecord, ...]: ...


class InMemoryProductActivationStore:
    """In-memory codes + activation history."""

    def __init__(
        self,
        *,
        codes: dict[str, str] | None = None,
    ) -> None:
        self._codes = dict(codes if codes is not None else DEFAULT_ACTIVATION_CODES)
        self._rows: list[ProductActivationRecord] = []

    def resolve_code(self, code: str) -> str | None:
        key = code.strip().upper()
        return self._codes.get(key)

    def save_activation(self, record: ProductActivationRecord) -> None:
        self._rows.append(record)

    def list_for_account(
        self, account_id: str
    ) -> tuple[ProductActivationRecord, ...]:
        return tuple(r for r in self._rows if r.account_id == account_id)
