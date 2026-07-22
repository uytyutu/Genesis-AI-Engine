"""R3.7.4 — Portal Composition Root.

Single place that assembles the Portal Read stack:

    PortalCatalog (or PortalCatalogView)
            ↓
    PortalReadService
            ↓
    PortalReadHandlers
            ↓
    portal_read_router  (wired via set_portal_read_handlers)

No Auth · no Persistence · not mounted in main.py.
No business logic — wiring only.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import APIRouter

from app.portal.portal_read_router import (
    clear_portal_read_handlers,
    portal_read_router,
    set_portal_read_handlers,
)
from app.portal.read_api_handlers import PortalReadHandlers
from app.portal.read_service import PortalCatalog, PortalCatalogView, PortalReadService

ENGINE_ID = "portal_bootstrap_v1"


@dataclass(frozen=True)
class PortalReadStack:
    """Assembled read stack — router remains unmounted until app wiring."""

    catalog: PortalCatalogView
    service: PortalReadService
    handlers: PortalReadHandlers
    router: APIRouter


def empty_portal_catalog() -> PortalCatalog:
    """In-memory empty snapshot — not a database."""
    return PortalCatalog(
        clients={},
        websites={},
        deployments={},
        assets={},
        edit_sessions={},
    )


def compose_portal_read(
    catalog: PortalCatalogView | None = None,
    *,
    wire_router: bool = True,
) -> PortalReadStack:
    """Compose Catalog → Service → Handlers → (optional) router handler slot."""
    resolved = catalog if catalog is not None else empty_portal_catalog()
    service = PortalReadService(resolved)
    handlers = PortalReadHandlers(service)
    if wire_router:
        set_portal_read_handlers(handlers)
    return PortalReadStack(
        catalog=resolved,
        service=service,
        handlers=handlers,
        router=portal_read_router,
    )


def teardown_portal_read() -> None:
    """Clear router handler slot (tests / shutdown)."""
    clear_portal_read_handlers()
