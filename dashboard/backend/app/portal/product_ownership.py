"""Mission 6.2 — ProductOwnership Domain.

Answers only: which products belong to this Account?

```text
Account
    ↓
ProductOwnership
    ↓
Product (type / instance)
```

Independent of Billing · Licenses · Purchases.
Does not mutate WebsiteOwnership · AuthN · AuthZ.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "product_ownership_domain_v1"

ProductOwnershipStatus = Literal["active", "inactive", "pending"]
ProductOwnershipSource = Literal["native", "website_bridge"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProductOwnership:
    """Account ↔ product instance relationship (platform-level)."""

    ownership_id: str
    account_id: str
    product_id: str
    product_type: str
    status: ProductOwnershipStatus
    source: ProductOwnershipSource
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_product_ownership(
    *,
    account_id: str,
    product_id: str,
    product_type: str,
    status: ProductOwnershipStatus = "active",
    source: ProductOwnershipSource = "native",
    ownership_id: str | None = None,
    created_at: str | None = None,
) -> ProductOwnership:
    """Construct a native ProductOwnership row (no Website side effects)."""
    return ProductOwnership(
        ownership_id=ownership_id or str(uuid4()),
        account_id=account_id,
        product_id=product_id,
        product_type=product_type,
        status=status,
        source=source,
        created_at=created_at or _utc_now_iso(),
    )
