"""Commercial Platform 6.4 — PurchaseService.

```text
Purchase → Stub PaymentProvider → License (entitlement) → redeem → Activation
```

Never writes ProductOwnershipStore directly.
Purchase is one source of License — not a required step before License.
"""

from __future__ import annotations

from app.portal.license import LicenseError
from app.portal.license_facade import LicenseFacade
from app.portal.payment_provider import PaymentProvider
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.purchase import (
    PurchaseError,
    mark_purchase_failed,
    mark_purchase_paid,
    new_purchase,
)
from app.portal.purchase_store import PurchaseStore
from app.portal.purchase_view import PurchaseView, build_purchase_view

ENGINE_ID = "purchase_service_v1"


class PurchaseService:
    def __init__(
        self,
        *,
        catalog: ProductCatalogStore,
        purchases: PurchaseStore,
        payments: PaymentProvider,
        licenses: LicenseFacade,
    ) -> None:
        self._catalog = catalog
        self._purchases = purchases
        self._payments = payments
        self._licenses = licenses

    def purchase(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
    ) -> PurchaseView:
        product = None
        for row in self._catalog.list_products():
            if row.product_id == catalog_product_id:
                product = row
                break
        if product is None:
            raise PurchaseError("product_not_found")
        if product.availability != "available":
            raise PurchaseError("product_not_purchasable")

        purchase = new_purchase(
            account_id=account_id,
            catalog_product_id=product.product_id,
            product_type=product.product_type,
        )
        self._purchases.save(purchase)

        charge = self._payments.charge(
            account_id=account_id,
            catalog_product_id=product.product_id,
            purchase_id=purchase.purchase_id,
        )
        if not charge.succeeded or not charge.provider_reference:
            failed = mark_purchase_failed(purchase)
            self._purchases.save(failed)
            raise PurchaseError(charge.failure_reason or "payment_failed")

        paid = mark_purchase_paid(
            purchase, provider_reference=charge.provider_reference
        )
        self._purchases.save(paid)

        try:
            granted = self._licenses.grant(
                account_id=account_id,
                catalog_product_id=product.product_id,
                source="purchase",
            )
            activated = self._licenses.redeem(
                account_id=account_id,
                license_id=granted.license_id,
            )
        except LicenseError as exc:
            raise PurchaseError(f"license_failed:{exc}") from exc

        return build_purchase_view(paid, activated_product=activated)
