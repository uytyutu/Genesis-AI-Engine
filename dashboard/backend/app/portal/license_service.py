"""Commercial Platform 6.5 — LicenseService.

```text
License grants entitlement.
Redeem → ProductActivation (never ProductOwnershipStore).
```
"""

from __future__ import annotations

from app.portal.license import (
    License,
    LicenseError,
    LicenseSource,
    LicenseValidationResult,
    mark_license_used,
    new_license,
    validate_license_for_account,
)
from app.portal.license_store import LicenseStore
from app.portal.license_view import LicenseView, build_license_view
from app.portal.product_activation import ProductActivationError
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_ownership_view import MyProductView

ENGINE_ID = "license_service_v1"


class LicenseService:
    def __init__(
        self,
        *,
        catalog: ProductCatalogStore,
        licenses: LicenseStore,
        activation: ProductActivationFacade,
    ) -> None:
        self._catalog = catalog
        self._licenses = licenses
        self._activation = activation

    def grant(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
        source: LicenseSource,
    ) -> License:
        product = None
        for row in self._catalog.list_products():
            if row.product_id == catalog_product_id:
                product = row
                break
        if product is None:
            raise LicenseError("product_not_found")
        if product.availability != "available" and source == "purchase":
            raise LicenseError("product_not_licensable")

        license = new_license(
            account_id=account_id,
            catalog_product_id=product.product_id,
            product_type=product.product_type,
            source=source,
        )
        self._licenses.save(license)
        return license

    def list_for_account(self, account_id: str) -> list[LicenseView]:
        rows = sorted(
            self._licenses.list_for_account(account_id),
            key=lambda item: item.created_at,
            reverse=True,
        )
        return [build_license_view(row) for row in rows]

    def validate(
        self, *, account_id: str, license_id: str
    ) -> LicenseValidationResult:
        license = self._licenses.get(license_id)
        if license is None:
            return LicenseValidationResult(
                license_id=license_id,
                valid=False,
                status="missing",
                catalog_product_id="",
                product_type="",
                reason="license_not_found",
            )
        return validate_license_for_account(license, account_id=account_id)

    def redeem(
        self, *, account_id: str, license_id: str
    ) -> MyProductView:
        """Apply entitlement: validate → Activation → mark license used."""
        license = self._licenses.get(license_id)
        if license is None:
            raise LicenseError("license_not_found")
        result = validate_license_for_account(license, account_id=account_id)
        if not result.valid:
            raise LicenseError(result.reason or "license_invalid")

        try:
            activated = self._activation.activate_from_purchase(
                account_id=account_id,
                catalog_product_id=license.catalog_product_id,
            )
        except ProductActivationError as exc:
            raise LicenseError(f"activation_failed:{exc}") from exc

        self._licenses.save(mark_license_used(license))
        return activated
