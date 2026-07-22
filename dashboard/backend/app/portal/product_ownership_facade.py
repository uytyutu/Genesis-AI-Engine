"""Mission 6.2 — ProductOwnershipFacade.

```text
Account
    ↓
ProductOwnershipFacade
    ├── native ProductOwnershipStore
    └── WebsiteOwnershipBridge
    ↓
Product Catalog (display enrichment)
```

Sole application entry for ``list_my_products``.
Does not purchase · license · bill · mutate WebsiteOwnership.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_ownership import ProductOwnership
from app.portal.product_ownership_store import ProductOwnershipStore
from app.portal.product_ownership_view import MyProductView, build_my_product_view
from app.portal.website_ownership_bridge import WebsiteOwnershipBridge

ENGINE_ID = "product_ownership_facade_v1"


@dataclass(frozen=True)
class ProductOwnershipFacade:
    """Unified My Products entry — Bridge today, native store tomorrow."""

    _store: ProductOwnershipStore
    _bridge: WebsiteOwnershipBridge
    _catalog: ProductCatalogStore

    @classmethod
    def from_parts(
        cls,
        store: ProductOwnershipStore,
        bridge: WebsiteOwnershipBridge,
        catalog: ProductCatalogStore,
    ) -> ProductOwnershipFacade:
        return cls(_store=store, _bridge=bridge, _catalog=catalog)

    def list_my_products(self, account_id: str) -> list[MyProductView]:
        names = {
            product.product_type: product.display_name
            for product in self._catalog.list_products()
        }
        merged: dict[str, ProductOwnership] = {}
        for row in self._bridge.list_for_account(account_id):
            merged[row.product_id] = row
        for row in self._store.list_for_account(account_id):
            # Native wins over bridge on same product_id.
            merged[row.product_id] = row

        views: list[MyProductView] = []
        for ownership in sorted(
            merged.values(),
            key=lambda item: (item.product_type, item.product_id),
        ):
            display = names.get(ownership.product_type, ownership.product_type)
            views.append(
                build_my_product_view(ownership, display_name=display)
            )
        return views
