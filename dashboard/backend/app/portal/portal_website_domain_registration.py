"""R5.3 — Register Website Domain module (resource-state reference).

Mounts GET/PUT /portal/websites/{id}/domain with AuthorizationFacade gate.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_website_domain_router import (
    portal_website_domain_router,
    set_authorization_facade,
    set_website_domain_facade,
)
from app.portal.website_domain_facade import WebsiteDomainFacade
from app.portal.website_domain_store import (
    InMemoryWebsiteDomainStore,
    WebsiteDomainStore,
)

ENGINE_ID = "portal_website_domain_registration_v1"


def register_portal_website_domain(
    app: FastAPI,
    *,
    ownerships: OwnershipDirectory | None = None,
    store: WebsiteDomainStore | None = None,
) -> bool:
    """Wire Domain + Authorization facades and mount router."""
    ownership_dir = (
        ownerships if ownerships is not None else empty_ownership_directory()
    )
    domain_store = store if store is not None else InMemoryWebsiteDomainStore()
    set_website_domain_facade(WebsiteDomainFacade.from_store(domain_store))
    set_authorization_facade(AuthorizationFacade(ownership_dir))
    app.include_router(portal_website_domain_router)
    return True
