"""Mission 6.3 — ProductActivationService (domain orchestration).

Creates native ProductOwnership. No payments · no WebsiteOwnership mutation.
"""

from __future__ import annotations

from app.portal.product import Product
from app.portal.product_activation import (
    ProductActivationError,
    ProductActivationRequest,
    native_instance_product_id,
    new_activation_record,
)
from app.portal.product_activation_store import ProductActivationStore
from app.portal.product_catalog_store import ProductCatalogStore
from app.portal.product_ownership import ProductOwnership, new_product_ownership
from app.portal.product_ownership_store import ProductOwnershipStore

ENGINE_ID = "product_activation_service_v1"


class ProductActivationService:
    """Activation → native ProductOwnership only."""

    def __init__(
        self,
        *,
        catalog: ProductCatalogStore,
        ownerships: ProductOwnershipStore,
        activations: ProductActivationStore,
    ) -> None:
        self._catalog = catalog
        self._ownerships = ownerships
        self._activations = activations

    def activate(self, request: ProductActivationRequest) -> ProductOwnership:
        product = self._require_catalog_product(request.catalog_product_id)
        if product.availability != "available":
            raise ProductActivationError("product_not_activatable")

        self._validate_code(request, product)

        existing = self._native_for_type(request.account_id, product.product_type)
        if existing is not None:
            return existing

        ownership = new_product_ownership(
            account_id=request.account_id,
            product_id=native_instance_product_id(product.product_type),
            product_type=product.product_type,
            status="active",
            source="native",
        )
        self._ownerships.save(ownership)
        self._activations.save_activation(
            new_activation_record(
                account_id=request.account_id,
                catalog_product_id=product.product_id,
                ownership_id=ownership.ownership_id,
                product_id=ownership.product_id,
                product_type=ownership.product_type,
                channel=request.channel,
            )
        )
        return ownership

    def _require_catalog_product(self, catalog_product_id: str) -> Product:
        for product in self._catalog.list_products():
            if product.product_id == catalog_product_id:
                return product
        raise ProductActivationError("product_not_found")

    def _validate_code(
        self, request: ProductActivationRequest, product: Product
    ) -> None:
        code = request.activation_code
        if not code:
            raise ProductActivationError("activation_code_required")
        resolved = self._activations.resolve_code(code)
        if resolved is None:
            raise ProductActivationError("activation_code_invalid")
        if resolved != "*" and resolved != product.product_id:
            raise ProductActivationError("activation_code_mismatch")

    def _native_for_type(
        self, account_id: str, product_type: str
    ) -> ProductOwnership | None:
        for row in self._ownerships.list_for_account(account_id):
            if row.source == "native" and row.product_type == product_type:
                return row
        return None
