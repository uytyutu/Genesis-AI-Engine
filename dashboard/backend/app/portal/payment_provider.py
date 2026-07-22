"""Commercial Platform 6.4 — Stub Payment Provider (Integration Boundary).

```text
PurchaseService
    ↓
PaymentProvider (Protocol)
    ↓
StubPaymentProvider | Stripe (future)
```

No Stripe/Paddle SDK in this slice.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import uuid4

ENGINE_ID = "payment_provider_v1"


@dataclass(frozen=True)
class PaymentChargeResult:
    succeeded: bool
    provider_reference: str | None
    failure_reason: str | None = None


class PaymentProvider(Protocol):
    def charge(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
        purchase_id: str,
    ) -> PaymentChargeResult: ...


class StubPaymentProvider:
    """Always succeeds — demo commerce only."""

    def charge(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
        purchase_id: str,
    ) -> PaymentChargeResult:
        return PaymentChargeResult(
            succeeded=True,
            provider_reference=f"stub_{uuid4().hex[:12]}",
        )
