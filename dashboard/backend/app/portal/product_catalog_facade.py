"""Mission 6.1 — ProductCatalogFacade.

```text
Platform
    ↓
ProductCatalogFacade
    ↓
Product Domain + Store
```

Sole application entry for Product Catalog reads.
Does not know Website · Ownership · Billing · purchase.
Does not authenticate · authorize (caller gates HTTP).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_catalog_view import (
    ProductCatalogItemView,
    build_product_catalog_item_view,
)

ENGINE_ID = "product_catalog_facade_v1"


@dataclass(frozen=True)
class ProductCatalogFacade:
    """Platform-level catalog Facade — independent of Website modules."""

    _store: ProductCatalogStore

    @classmethod
    def from_store(cls, store: ProductCatalogStore) -> ProductCatalogFacade:
        return cls(_store=store)

    def list_products(self) -> list[ProductCatalogItemView]:
        return [
            build_product_catalog_item_view(product)
            for product in self._store.list_products()
        ]
