"""R5.1 — Register Website Settings module (reference registration).

Mounts GET/PUT /portal/websites/{id}/settings with AuthorizationFacade gate.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_website_settings_router import (
    portal_website_settings_router,
    set_authorization_facade,
    set_website_settings_facade,
)
from app.portal.website_settings_facade import WebsiteSettingsFacade
from app.portal.website_settings_store import (
    InMemoryWebsiteSettingsStore,
    WebsiteSettingsStore,
)

ENGINE_ID = "portal_website_settings_registration_v1"


def register_portal_website_settings(
    app: FastAPI,
    *,
    ownerships: OwnershipDirectory | None = None,
    store: WebsiteSettingsStore | None = None,
) -> bool:
    """Wire Settings + Authorization facades and mount router."""
    ownership_dir = (
        ownerships if ownerships is not None else empty_ownership_directory()
    )
    settings_store = store if store is not None else InMemoryWebsiteSettingsStore()
    set_website_settings_facade(WebsiteSettingsFacade.from_store(settings_store))
    set_authorization_facade(AuthorizationFacade(ownership_dir))
    app.include_router(portal_website_settings_router)
    return True
