"""Commercial Platform 6.6 — Billing Domain (financial ledger).

Answers only: which financial events occurred?

```text
Billing records financial events.
Billing never creates ProductOwnership.
Billing never activates products.
Billing never grants License.
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "billing_domain_v1"

BillingStatus = Literal["pending", "paid", "failed"]
BillingProvider = Literal["stub"]


class BillingError(ValueError):
    """Billing operation rejected."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class BillingTransaction:
    """One financial event — not entitlement, not ownership."""

    transaction_id: str
    account_id: str
    product_id: str
    purchase_id: str | None
    amount: int
    currency: str
    status: BillingStatus
    provider: BillingProvider
    provider_reference: str | None
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_billing_transaction(
    *,
    account_id: str,
    product_id: str,
    amount: int,
    currency: str = "EUR",
    purchase_id: str | None = None,
    provider: BillingProvider = "stub",
) -> BillingTransaction:
    now = _utc_now_iso()
    return BillingTransaction(
        transaction_id=str(uuid4()),
        account_id=account_id,
        product_id=product_id,
        purchase_id=purchase_id,
        amount=amount,
        currency=currency.upper(),
        status="pending",
        provider=provider,
        provider_reference=None,
        created_at=now,
        updated_at=now,
    )


def mark_billing_paid(
    row: BillingTransaction, *, provider_reference: str
) -> BillingTransaction:
    return replace(
        row,
        status="paid",
        provider_reference=provider_reference,
        updated_at=_utc_now_iso(),
    )


def mark_billing_failed(row: BillingTransaction) -> BillingTransaction:
    return replace(row, status="failed", updated_at=_utc_now_iso())


# Demo catalog amounts in minor units (cents) — not real pricing.
STUB_PRODUCT_AMOUNTS_CENTS: dict[str, int] = {
    "prod_website": 4900,
    "prod_chatbot": 2900,
    "prod_analytics": 1900,
    "prod_crm": 9900,
    "prod_automation": 3900,
}


def stub_amount_for_product(product_id: str) -> int:
    return STUB_PRODUCT_AMOUNTS_CENTS.get(product_id, 1000)
