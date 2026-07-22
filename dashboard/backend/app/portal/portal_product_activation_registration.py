"""Mission 6.3 — Register Product Activation.

Mounts POST /portal/products/{product_id}/activate.
Must share ProductOwnershipStore with My Products registration.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.portal_product_activation_router import (
    portal_product_activation_router,
    set_product_activation_facade,
)
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_activation_store import (
    InMemoryProductActivationStore,
    ProductActivationStore,
)
from app.portal.product_catalog_store import (
    InMemoryProductCatalogStore,
    ProductCatalogStore,
)
from app.portal.product_ownership_store import (
    InMemoryProductOwnershipStore,
    ProductOwnershipStore,
)

ENGINE_ID = "portal_product_activation_registration_v1"


def register_portal_product_activation(
    app: FastAPI,
    *,
    ownership_store: ProductOwnershipStore | None = None,
    catalog: ProductCatalogStore | None = None,
    activation_store: ProductActivationStore | None = None,
    facade: ProductActivationFacade | None = None,
) -> ProductActivationFacade:
    """Wire activation facade onto shared ownership store and mount router."""
    store = (
        ownership_store
        if ownership_store is not None
        else InMemoryProductOwnershipStore()
    )
    catalog_store = (
        catalog if catalog is not None else InMemoryProductCatalogStore()
    )
    activations = (
        activation_store
        if activation_store is not None
        else InMemoryProductActivationStore()
    )
    resolved = facade or ProductActivationFacade.from_parts(
        catalog=catalog_store,
        ownerships=store,
        activations=activations,
    )
    set_product_activation_facade(resolved)
    app.include_router(portal_product_activation_router)
    return resolved
