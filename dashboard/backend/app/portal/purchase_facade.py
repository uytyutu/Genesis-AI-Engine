"""Commercial Platform 6.4 — PurchaseFacade.

Sole application entry for purchases. Does not own products.
Grants a License after payment, then redeems it via Activation.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.license_facade import LicenseFacade
from app.portal.payment_provider import PaymentProvider, StubPaymentProvider
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.purchase import PurchaseError
from app.portal.purchase_service import PurchaseService
from app.portal.purchase_store import PurchaseStore
from app.portal.purchase_view import PurchaseView

ENGINE_ID = "purchase_facade_v1"


@dataclass(frozen=True)
class PurchaseFacade:
    _service: PurchaseService

    @classmethod
    def from_parts(
        cls,
        *,
        catalog: ProductCatalogStore,
        purchases: PurchaseStore,
        licenses: LicenseFacade,
        payments: PaymentProvider | None = None,
    ) -> PurchaseFacade:
        return cls(
            _service=PurchaseService(
                catalog=catalog,
                purchases=purchases,
                payments=payments if payments is not None else StubPaymentProvider(),
                licenses=licenses,
            )
        )

    def purchase(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
    ) -> PurchaseView:
        try:
            return self._service.purchase(
                account_id=account_id,
                catalog_product_id=catalog_product_id,
            )
        except PurchaseError:
            raise
