"""Mission 6.3 — ProductActivationFacade.

```text
AuthN
    ↓
ProductActivationFacade
    ↓
ProductActivationService
    ↓
ProductOwnershipStore (native)
```

Sole application entry for product activation.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.product_activation import (
    ProductActivationError,
    new_activation_request,
)
from app.portal.product_activation_service import ProductActivationService
from app.portal.product_activation_store import ProductActivationStore
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_ownership_store import ProductOwnershipStore
from app.portal.product_ownership_view import MyProductView, build_my_product_view

ENGINE_ID = "product_activation_facade_v1"


@dataclass(frozen=True)
class ProductActivationFacade:
    _service: ProductActivationService
    _catalog: ProductCatalogStore

    @classmethod
    def from_parts(
        cls,
        *,
        catalog: ProductCatalogStore,
        ownerships: ProductOwnershipStore,
        activations: ProductActivationStore,
    ) -> ProductActivationFacade:
        return cls(
            _service=ProductActivationService(
                catalog=catalog,
                ownerships=ownerships,
                activations=activations,
            ),
            _catalog=catalog,
        )

    def activate(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
        activation_code: str | None,
    ) -> MyProductView:
        channel = "activation_code"
        if activation_code and activation_code.strip().upper() == "INTERNAL-SEED":
            channel = "seed"
        request = new_activation_request(
            account_id=account_id,
            catalog_product_id=catalog_product_id,
            activation_code=activation_code,
            channel=channel,
        )
        return self._complete(request)

    def activate_from_purchase(
        self,
        *,
        account_id: str,
        catalog_product_id: str,
    ) -> MyProductView:
        """Commercial Platform entry — no activation code; still creates ownership here only."""
        request = new_activation_request(
            account_id=account_id,
            catalog_product_id=catalog_product_id,
            activation_code=None,
            channel="purchase",
        )
        return self._complete(request)

    def _complete(self, request) -> MyProductView:
        try:
            ownership = self._service.activate(request)
        except ProductActivationError:
            raise

        names = {
            p.product_type: p.display_name for p in self._catalog.list_products()
        }
        display = names.get(ownership.product_type, ownership.product_type)
        return build_my_product_view(ownership, display_name=display)
