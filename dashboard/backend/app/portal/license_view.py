"""Commercial Platform 6.5 — License View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.license import License, LicenseValidationResult

ENGINE_ID = "license_view_v1"


@dataclass(frozen=True)
class LicenseView:
    license_id: str
    catalog_product_id: str
    product_type: str
    status: str
    source: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "license_id": self.license_id,
            "catalog_product_id": self.catalog_product_id,
            "product_type": self.product_type,
            "status": self.status,
            "source": self.source,
            "created_at": self.created_at,
        }


def build_license_view(license: License) -> LicenseView:
    return LicenseView(
        license_id=license.license_id,
        catalog_product_id=license.catalog_product_id,
        product_type=license.product_type,
        status=license.status,
        source=license.source,
        created_at=license.created_at,
    )


def build_validation_dict(result: LicenseValidationResult) -> dict[str, Any]:
    return result.as_dict()
