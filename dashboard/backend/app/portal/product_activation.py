"""Mission 6.3 — Product Activation Domain.

Answers only: how does a Product become owned by an Account?

```text
Account
    ↓
Product Activation
    ↓
ProductOwnership (native)
```

Not purchase · billing · provisioning · Website setup.
Does not mutate WebsiteOwnershipBridge.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "product_activation_domain_v1"

ActivationChannel = Literal["seed", "activation_code", "manual", "test"]


class ProductActivationError(ValueError):
    """Activation rejected."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ProductActivationRequest:
    """Intent to activate one catalog product for one Account."""

    account_id: str
    catalog_product_id: str
    activation_code: str | None
    channel: ActivationChannel
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductActivationRecord:
    """Audit row for one successful activation attempt."""

    activation_id: str
    account_id: str
    catalog_product_id: str
    ownership_id: str
    product_id: str
    product_type: str
    channel: ActivationChannel
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_activation_request(
    *,
    account_id: str,
    catalog_product_id: str,
    activation_code: str | None = None,
    channel: ActivationChannel = "activation_code",
) -> ProductActivationRequest:
    return ProductActivationRequest(
        account_id=account_id,
        catalog_product_id=catalog_product_id,
        activation_code=(activation_code.strip() if activation_code else None),
        channel=channel,
        created_at=_utc_now_iso(),
    )


def new_activation_record(
    *,
    account_id: str,
    catalog_product_id: str,
    ownership_id: str,
    product_id: str,
    product_type: str,
    channel: ActivationChannel,
) -> ProductActivationRecord:
    return ProductActivationRecord(
        activation_id=str(uuid4()),
        account_id=account_id,
        catalog_product_id=catalog_product_id,
        ownership_id=ownership_id,
        product_id=product_id,
        product_type=product_type,
        channel=channel,
        created_at=_utc_now_iso(),
    )


def native_instance_product_id(product_type: str) -> str:
    return f"native_{product_type}_{uuid4().hex[:8]}"
