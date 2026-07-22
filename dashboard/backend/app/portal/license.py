"""Commercial Platform 6.5 — License Domain.

Answers only: does this Account have entitlement to activate/use a product?

```text
License grants entitlement.
License never creates ProductOwnership.
```

Purchase / Enterprise / Promo / Gift / Admin are sources of License — not sequential steps.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "license_domain_v1"

LicenseStatus = Literal["active", "used", "revoked"]
LicenseSource = Literal[
    "purchase",
    "enterprise",
    "promo",
    "gift",
    "admin",
]


class LicenseError(ValueError):
    """License operation rejected."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class License:
    """Entitlement to activate one catalog product — not ownership."""

    license_id: str
    account_id: str
    catalog_product_id: str
    product_type: str
    status: LicenseStatus
    source: LicenseSource
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LicenseValidationResult:
    license_id: str
    valid: bool
    status: str
    catalog_product_id: str
    product_type: str
    reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_license(
    *,
    account_id: str,
    catalog_product_id: str,
    product_type: str,
    source: LicenseSource,
) -> License:
    now = _utc_now_iso()
    return License(
        license_id=str(uuid4()),
        account_id=account_id,
        catalog_product_id=catalog_product_id,
        product_type=product_type,
        status="active",
        source=source,
        created_at=now,
        updated_at=now,
    )


def mark_license_used(license: License) -> License:
    return replace(license, status="used", updated_at=_utc_now_iso())


def validate_license_for_account(
    license: License, *, account_id: str
) -> LicenseValidationResult:
    if license.account_id != account_id:
        return LicenseValidationResult(
            license_id=license.license_id,
            valid=False,
            status=license.status,
            catalog_product_id=license.catalog_product_id,
            product_type=license.product_type,
            reason="account_mismatch",
        )
    if license.status != "active":
        return LicenseValidationResult(
            license_id=license.license_id,
            valid=False,
            status=license.status,
            catalog_product_id=license.catalog_product_id,
            product_type=license.product_type,
            reason="license_not_active",
        )
    return LicenseValidationResult(
        license_id=license.license_id,
        valid=True,
        status=license.status,
        catalog_product_id=license.catalog_product_id,
        product_type=license.product_type,
        reason=None,
    )
