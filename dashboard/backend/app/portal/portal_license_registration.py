"""Commercial Platform 6.5 — Register Licenses."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.license_facade import LicenseFacade
from app.portal.license_store import InMemoryLicenseStore, LicenseStore
from app.portal.portal_license_router import (
    portal_license_router,
    set_license_facade,
)
from app.portal.product_activation_facade import ProductActivationFacade
from app.portal.product_catalog_store import (
    InMemoryProductCatalogStore,
    ProductCatalogStore,
)

ENGINE_ID = "portal_license_registration_v1"


def register_portal_licenses(
    app: FastAPI,
    *,
    activation: ProductActivationFacade,
    catalog: ProductCatalogStore | None = None,
    license_store: LicenseStore | None = None,
) -> LicenseFacade:
    catalog_store = (
        catalog if catalog is not None else InMemoryProductCatalogStore()
    )
    store = license_store if license_store is not None else InMemoryLicenseStore()
    facade = LicenseFacade.from_parts(
        catalog=catalog_store,
        licenses=store,
        activation=activation,
    )
    set_license_facade(facade)
    app.include_router(portal_license_router)
    return facade
