"""Mission 6.1 — ProductCatalogStore (Protocol + in-memory / static seed).

Future Marketplace / Billing can swap the store without changing
ProductCatalogFacade or GET /portal/products contract.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.product import Product, default_product_catalog

ENGINE_ID = "product_catalog_store_v1"


class ProductCatalogStore(Protocol):
    def list_products(self) -> tuple[Product, ...]: ...


class InMemoryProductCatalogStore:
    """Seeded catalog — durable / marketplace-backed store later."""

    def __init__(self, *, products: tuple[Product, ...] | None = None) -> None:
        self._products = products if products is not None else default_product_catalog()

    def list_products(self) -> tuple[Product, ...]:
        return self._products
