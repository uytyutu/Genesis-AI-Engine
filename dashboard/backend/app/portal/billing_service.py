"""Commercial Platform 6.6 — BillingService (ledger writes/reads only).

Never grants License · never activates · never writes ProductOwnership.
"""

from __future__ import annotations

from app.portal.billing import (
    BillingError,
    BillingTransaction,
    mark_billing_failed,
    mark_billing_paid,
    new_billing_transaction,
    stub_amount_for_product,
)
from app.portal.billing_store import BillingStore
from app.portal.billing_view import BillingView, build_billing_view

ENGINE_ID = "billing_service_v1"


class BillingService:
    def __init__(self, *, store: BillingStore) -> None:
        self._store = store

    def record_pending(
        self,
        *,
        account_id: str,
        product_id: str,
        purchase_id: str | None = None,
        amount: int | None = None,
        currency: str = "EUR",
    ) -> BillingTransaction:
        row = new_billing_transaction(
            account_id=account_id,
            product_id=product_id,
            purchase_id=purchase_id,
            amount=amount if amount is not None else stub_amount_for_product(product_id),
            currency=currency,
        )
        self._store.save(row)
        return row

    def mark_paid(
        self, transaction_id: str, *, provider_reference: str
    ) -> BillingTransaction:
        row = self._store.get(transaction_id)
        if row is None:
            raise BillingError("transaction_not_found")
        paid = mark_billing_paid(row, provider_reference=provider_reference)
        self._store.save(paid)
        return paid

    def mark_failed(self, transaction_id: str) -> BillingTransaction:
        row = self._store.get(transaction_id)
        if row is None:
            raise BillingError("transaction_not_found")
        failed = mark_billing_failed(row)
        self._store.save(failed)
        return failed

    def list_for_account(self, account_id: str) -> list[BillingView]:
        rows = sorted(
            self._store.list_for_account(account_id),
            key=lambda item: item.created_at,
            reverse=True,
        )
        return [build_billing_view(row) for row in rows]

    def get_for_account(
        self, *, account_id: str, transaction_id: str
    ) -> BillingView | None:
        row = self._store.get(transaction_id)
        if row is None or row.account_id != account_id:
            return None
        return build_billing_view(row)
