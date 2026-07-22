"""Mission 6.2 — Register My Products (Product Ownership).

Mounts GET /portal/my-products with WebsiteOwnershipBridge + native store.
Does not migrate WebsiteOwnership.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_my_products_router import (
    portal_my_products_router,
    set_product_ownership_facade,
)
from app.portal.product_catalog_store import (
    InMemoryProductCatalogStore,
    ProductCatalogStore,
)
from app.portal.product_ownership_facade import ProductOwnershipFacade
from app.portal.product_ownership_store import (
    InMemoryProductOwnershipStore,
    ProductOwnershipStore,
)
from app.portal.website_ownership_bridge import WebsiteOwnershipBridge

ENGINE_ID = "portal_my_products_registration_v1"


def register_portal_my_products(
    app: FastAPI,
    *,
    website_ownerships: OwnershipDirectory | None = None,
    ownership_store: ProductOwnershipStore | None = None,
    catalog: ProductCatalogStore | None = None,
) -> bool:
    """Wire Product Ownership facade (native + bridge) and mount router."""
    ownership_dir = (
        website_ownerships
        if website_ownerships is not None
        else empty_ownership_directory()
    )
    store = (
        ownership_store
        if ownership_store is not None
        else InMemoryProductOwnershipStore()
    )
    catalog_store = (
        catalog if catalog is not None else InMemoryProductCatalogStore()
    )
    set_product_ownership_facade(
        ProductOwnershipFacade.from_parts(
            store,
            WebsiteOwnershipBridge(ownership_dir),
            catalog_store,
        )
    )
    app.include_router(portal_my_products_router)
    return True
