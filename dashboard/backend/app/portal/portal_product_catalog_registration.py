"""Mission 6.1 — Register Product Catalog (platform-level).

Mounts GET /portal/products. No OwnershipDirectory wiring.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.portal_product_catalog_router import (
    portal_product_catalog_router,
    set_product_catalog_facade,
)
from app.portal.product_catalog_facade import ProductCatalogFacade
from app.portal.product_catalog_store import (
    InMemoryProductCatalogStore,
    ProductCatalogStore,
)

ENGINE_ID = "portal_product_catalog_registration_v1"


def register_portal_product_catalog(
    app: FastAPI,
    *,
    store: ProductCatalogStore | None = None,
) -> bool:
    """Wire Product Catalog facade and mount router."""
    catalog_store = (
        store if store is not None else InMemoryProductCatalogStore()
    )
    set_product_catalog_facade(ProductCatalogFacade.from_store(catalog_store))
    app.include_router(portal_product_catalog_router)
    return True
