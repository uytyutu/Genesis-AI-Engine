"""R4.3 — Authentication Middleware.

Answers only: who is making this request?

```text
Request → cookie → SessionFacade → Account | Anonymous → next
```

Never returns 401/403. Never authorizes. Never redirects.
Does not change Session Domain.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

from app.portal.authentication_facade import AuthenticationDirectory
from app.portal.request_principal import ANONYMOUS, RequestPrincipal
from app.portal.session_cookie import DEFAULT_COOKIE_NAME
from app.portal.session_facade import SessionFacade

ENGINE_ID = "portal_authentication_middleware_v1"

# Populated by register_portal_authentication_middleware / login registration.
_session_facade: SessionFacade | None = None
_directory: AuthenticationDirectory | None = None
_cookie_name: str = DEFAULT_COOKIE_NAME


def configure_portal_authentication_middleware(
    *,
    session_facade: SessionFacade,
    directory: AuthenticationDirectory,
    cookie_name: str = DEFAULT_COOKIE_NAME,
) -> None:
    global _session_facade, _directory, _cookie_name
    _session_facade = session_facade
    _directory = directory
    _cookie_name = cookie_name


def clear_portal_authentication_middleware() -> None:
    global _session_facade, _directory, _cookie_name
    _session_facade = None
    _directory = None
    _cookie_name = DEFAULT_COOKIE_NAME


def resolve_request_principal(request: Request) -> RequestPrincipal:
    """Pure identity resolution — used by middleware and tests."""
    if _session_facade is None or _directory is None:
        return ANONYMOUS
    raw = request.cookies.get(_cookie_name)
    if not raw:
        return ANONYMOUS
    session = _session_facade.get_active_session(raw)
    if session is None:
        return ANONYMOUS
    account = _directory.find_account_by_id(session.account_id)
    if account is None:
        return ANONYMOUS
    return RequestPrincipal(account=account)


def attach_principal(request: Request, principal: RequestPrincipal) -> None:
    """Place identity on request.state for downstream handlers."""
    request.state.portal_principal = principal
    request.state.account = principal.account  # Account | None (Anonymous)


class PortalAuthenticationMiddleware(BaseHTTPMiddleware):
    """Identify caller; never block the request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        principal = resolve_request_principal(request)
        attach_principal(request, principal)
        return await call_next(request)


def register_portal_authentication_middleware(app: ASGIApp) -> bool:
    """Mount identity middleware. Returns True when added."""
    # FastAPI / Starlette
    app.add_middleware(PortalAuthenticationMiddleware)  # type: ignore[attr-defined]
    return True
