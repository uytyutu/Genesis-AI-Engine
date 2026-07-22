"""Commercial Platform 6.6 — BillingFacade.

Financial ledger entry point. No License · no Activation · no Ownership.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.billing import BillingError, BillingTransaction
from app.portal.billing_service import BillingService
from app.portal.billing_store import BillingStore
from app.portal.billing_view import BillingView

ENGINE_ID = "billing_facade_v1"


@dataclass(frozen=True)
class BillingFacade:
    _service: BillingService

    @classmethod
    def from_store(cls, store: BillingStore) -> BillingFacade:
        return cls(_service=BillingService(store=store))

    def record_pending(
        self,
        *,
        account_id: str,
        product_id: str,
        purchase_id: str | None = None,
        amount: int | None = None,
        currency: str = "EUR",
    ) -> BillingTransaction:
        return self._service.record_pending(
            account_id=account_id,
            product_id=product_id,
            purchase_id=purchase_id,
            amount=amount,
            currency=currency,
        )

    def mark_paid(
        self, transaction_id: str, *, provider_reference: str
    ) -> BillingTransaction:
        try:
            return self._service.mark_paid(
                transaction_id, provider_reference=provider_reference
            )
        except BillingError:
            raise

    def mark_failed(self, transaction_id: str) -> BillingTransaction:
        try:
            return self._service.mark_failed(transaction_id)
        except BillingError:
            raise

    def list_transactions(self, *, account_id: str) -> list[BillingView]:
        return self._service.list_for_account(account_id)

    def get_transaction(
        self, *, account_id: str, transaction_id: str
    ) -> BillingView | None:
        return self._service.get_for_account(
            account_id=account_id, transaction_id=transaction_id
        )
