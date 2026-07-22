"""Commercial Platform 6.4 — PurchaseService.

```text
Purchase → Billing (ledger) → Stub Payment → License → redeem → Activation
```

Never writes ProductOwnershipStore directly.
Billing records money only — Purchase still grants License after payment.
"""

from __future__ import annotations

from app.portal.billing_facade import BillingFacade
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
        billing: BillingFacade,
    ) -> None:
        self._catalog = catalog
        self._purchases = purchases
        self._payments = payments
        self._licenses = licenses
        self._billing = billing

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

        ledger = self._billing.record_pending(
            account_id=account_id,
            product_id=product.product_id,
            purchase_id=purchase.purchase_id,
        )

        charge = self._payments.charge(
            account_id=account_id,
            catalog_product_id=product.product_id,
            purchase_id=purchase.purchase_id,
        )
        if not charge.succeeded or not charge.provider_reference:
            self._billing.mark_failed(ledger.transaction_id)
            failed = mark_purchase_failed(purchase)
            self._purchases.save(failed)
            raise PurchaseError(charge.failure_reason or "payment_failed")

        self._billing.mark_paid(
            ledger.transaction_id,
            provider_reference=charge.provider_reference,
        )
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
