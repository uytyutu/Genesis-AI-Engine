"""Commercial Platform 6.5 — LicenseFacade.

Sole commercial entry for entitlements. Never writes ProductOwnershipStore.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.license import LicenseError, LicenseSource, LicenseValidationResult
from app.portal.license_service import LicenseService
from app.portal.license_store import LicenseStore
from app.portal.license_view import LicenseView
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_ownership_view import MyProductView

ENGINE_ID = "license_facade_v1"


@dataclass(frozen=True)
class LicenseFacade:
    _service: LicenseService

    @classmethod
    def from_parts(
        cls,
        *,
        catalog: ProductCatalogStore,
        licenses: LicenseStore,
        activation: ProductActivationFacade,
    ) -> LicenseFacade:
        return cls(
            _service=LicenseService(
                catalog=catalog,
                licenses=licenses,
                activation=activation,
            )
        )

    def grant(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
        source: LicenseSource,
    ) -> LicenseView:
        from app.portal.license_view import build_license_view

        try:
            return build_license_view(
                self._service.grant(
                    account_id=account_id,
                    catalog_product_id=catalog_product_id,
                    source=source,
                )
            )
        except LicenseError:
            raise

    def list_licenses(self, *, account_id: str) -> list[LicenseView]:
        return self._service.list_for_account(account_id)

    def validate(
        self, *, account_id: str, license_id: str
    ) -> LicenseValidationResult:
        return self._service.validate(
            account_id=account_id, license_id=license_id
        )

    def redeem(
        self, *, account_id: str, license_id: str
    ) -> MyProductView:
        try:
            return self._service.redeem(
                account_id=account_id, license_id=license_id
            )
        except LicenseError:
            raise
