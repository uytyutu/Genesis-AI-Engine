"""R4.1 / R4.2 / R4.3 — Register HTTP Login + Session + Auth Middleware wiring.

Mounts POST /portal/login and configures shared SessionFacade for middleware.
Middleware itself is registered separately (order: add middleware after routes
or via register_portal_authentication_middleware).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authentication_facade import (
    AuthenticationDirectory,
    AuthenticationFacade,
    empty_authentication_directory,
)
from app.portal.portal_authentication_middleware import (
    configure_portal_authentication_middleware,
)
from app.portal.portal_login_router import (
    portal_login_router,
    set_authentication_facade,
    set_session_login_deps,
)
from app.portal.session_cookie import SessionCookieFactory
from app.portal.session_facade import SessionFacade
from app.portal.session_store import InMemorySessionStore, SessionStore

ENGINE_ID = "portal_login_registration_v1"

_shared_session_facade: SessionFacade | None = None
_shared_directory: AuthenticationDirectory | None = None


def get_shared_session_facade() -> SessionFacade | None:
    return _shared_session_facade


def get_shared_auth_directory() -> AuthenticationDirectory | None:
    return _shared_directory


def register_portal_login(
    app: FastAPI,
    *,
    directory: AuthenticationDirectory | None = None,
    session_store: SessionStore | None = None,
    cookie_factory: SessionCookieFactory | None = None,
) -> bool:
    """Wire auth + session facades, configure middleware deps, mount login."""
    global _shared_session_facade, _shared_directory
    resolved_dir = (
        directory if directory is not None else empty_authentication_directory()
    )
    store = session_store if session_store is not None else InMemorySessionStore()
    cookies = cookie_factory if cookie_factory is not None else SessionCookieFactory()
    session_facade = SessionFacade(store)
    _shared_session_facade = session_facade
    _shared_directory = resolved_dir
    set_authentication_facade(AuthenticationFacade(resolved_dir))
    set_session_login_deps(session_facade, cookies)
    configure_portal_authentication_middleware(
        session_facade=session_facade,
        directory=resolved_dir,
        cookie_name=cookies.cookie_name,
    )
    app.include_router(portal_login_router)
    return True
