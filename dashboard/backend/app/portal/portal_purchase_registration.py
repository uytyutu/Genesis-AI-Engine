"""Commercial Platform 6.4 — Register Purchases.

Purchase → License → redeem → Activation. Never writes ProductOwnershipStore.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.license_facade import LicenseFacade
from app.portal.portal_purchase_router import (
    portal_purchase_router,
    set_purchase_facade,
)
from app.portal.product_catalog_store import (
    InMemoryProductCatalogStore,
    ProductCatalogStore,
)
from app.portal.purchase_facade import PurchaseFacade
from app.portal.purchase_store import InMemoryPurchaseStore, PurchaseStore
from app.portal.payment_provider import PaymentProvider, StubPaymentProvider

ENGINE_ID = "portal_purchase_registration_v1"


def register_portal_purchases(
    app: FastAPI,
    *,
    licenses: LicenseFacade,
    catalog: ProductCatalogStore | None = None,
    purchase_store: PurchaseStore | None = None,
    payments: PaymentProvider | None = None,
) -> bool:
    """Wire PurchaseFacade onto LicenseFacade + stub payment provider."""
    catalog_store = (
        catalog if catalog is not None else InMemoryProductCatalogStore()
    )
    store = purchase_store if purchase_store is not None else InMemoryPurchaseStore()
    set_purchase_facade(
        PurchaseFacade.from_parts(
            catalog=catalog_store,
            purchases=store,
            licenses=licenses,
            payments=payments if payments is not None else StubPaymentProvider(),
        )
    )
    app.include_router(portal_purchase_router)
    return True
