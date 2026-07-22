"""R4.1 — Register HTTP Login Endpoint.

Mounts POST /portal/login via AuthenticationFacade.
No Session · Cookie · JWT.
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authentication_facade import (
    AuthenticationDirectory,
    AuthenticationFacade,
    empty_authentication_directory,
)
from app.portal.portal_login_router import (
    portal_login_router,
    set_authentication_facade,
)

ENGINE_ID = "portal_login_registration_v1"


def register_portal_login(
    app: FastAPI,
    *,
    directory: AuthenticationDirectory | None = None,
) -> bool:
    """Wire facade + mount login router. Returns True when mounted."""
    resolved = directory if directory is not None else empty_authentication_directory()
    set_authentication_facade(AuthenticationFacade(resolved))
    app.include_router(portal_login_router)
    return True
