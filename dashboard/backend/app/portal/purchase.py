"""Commercial Platform 6.4 — Purchase Domain.

Answers only: how is product acquisition initiated?

```text
Purchase creates commercial intent.
Purchase never creates ProductOwnership directly.
```

```text
Purchase → Product Activation → ProductOwnership
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "purchase_domain_v1"

PurchaseStatus = Literal["pending", "paid", "failed", "cancelled"]
PaymentProviderId = Literal["stub"]


class PurchaseError(ValueError):
    """Purchase rejected."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Purchase:
    """One commercial acquisition attempt — not ownership."""

    purchase_id: str
    account_id: str
    catalog_product_id: str
    product_type: str
    status: PurchaseStatus
    provider: PaymentProviderId
    provider_reference: str | None
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_purchase(
    *,
    account_id: str,
    catalog_product_id: str,
    product_type: str,
    provider: PaymentProviderId = "stub",
) -> Purchase:
    now = _utc_now_iso()
    return Purchase(
        purchase_id=str(uuid4()),
        account_id=account_id,
        catalog_product_id=catalog_product_id,
        product_type=product_type,
        status="pending",
        provider=provider,
        provider_reference=None,
        created_at=now,
        updated_at=now,
    )


def mark_purchase_paid(
    purchase: Purchase, *, provider_reference: str
) -> Purchase:
    return Purchase(
        purchase_id=purchase.purchase_id,
        account_id=purchase.account_id,
        catalog_product_id=purchase.catalog_product_id,
        product_type=purchase.product_type,
        status="paid",
        provider=purchase.provider,
        provider_reference=provider_reference,
        created_at=purchase.created_at,
        updated_at=_utc_now_iso(),
    )


def mark_purchase_failed(purchase: Purchase) -> Purchase:
    return Purchase(
        purchase_id=purchase.purchase_id,
        account_id=purchase.account_id,
        catalog_product_id=purchase.catalog_product_id,
        product_type=purchase.product_type,
        status="failed",
        provider=purchase.provider,
        provider_reference=purchase.provider_reference,
        created_at=purchase.created_at,
        updated_at=_utc_now_iso(),
    )
