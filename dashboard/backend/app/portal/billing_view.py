"""Commercial Platform 6.6 — Billing View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.billing import BillingTransaction

ENGINE_ID = "billing_view_v1"


@dataclass(frozen=True)
class BillingView:
    transaction_id: str
    account_id: str
    product_id: str
    amount: int
    currency: str
    status: str
    provider: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "product_id": self.product_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "provider": self.provider,
            "created_at": self.created_at,
        }


def build_billing_view(row: BillingTransaction) -> BillingView:
    return BillingView(
        transaction_id=row.transaction_id,
        account_id=row.account_id,
        product_id=row.product_id,
        amount=row.amount,
        currency=row.currency,
        status=row.status,
        provider=row.provider,
        created_at=row.created_at,
    )
