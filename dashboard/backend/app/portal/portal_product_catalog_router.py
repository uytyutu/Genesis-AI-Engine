"""Mission 6.1 — Product Catalog HTTP.

GET /portal/products
→ RequestPrincipal (authenticated) → ProductCatalogFacade

Platform-level catalog — not website-scoped.
Requires Authentication (account). Does **not** use AuthorizationFacade /
WebsiteOwnership (Product is independent of Website).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.product_catalog_facade import ProductCatalogFacade
from app.portal.product_catalog_view import ProductCatalogItemView

ENGINE_ID = "portal_product_catalog_router_v1"

portal_product_catalog_router = APIRouter(
    prefix="/portal",
    tags=["portal-product-catalog"],
)

_catalog_facade: ProductCatalogFacade | None = None


def set_product_catalog_facade(facade: ProductCatalogFacade) -> None:
    global _catalog_facade
    _catalog_facade = facade


def clear_product_catalog_facade() -> None:
    global _catalog_facade
    _catalog_facade = None


def get_product_catalog_facade() -> ProductCatalogFacade:
    if _catalog_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_product_catalog_not_configured"
        )
    return _catalog_facade


@portal_product_catalog_router.get(
    "/products",
    response_model=None,
)
def http_get_products(
    request: Request,
    catalog: Annotated[ProductCatalogFacade, Depends(get_product_catalog_facade)],
) -> list[ProductCatalogItemView]:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return catalog.list_products()
