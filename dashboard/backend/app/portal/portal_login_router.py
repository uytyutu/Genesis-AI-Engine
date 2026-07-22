"""R4.1 / R4.2 / R4.5 — HTTP Login + Logout.

POST /portal/login → AuthenticationFacade → SessionFacade → HttpOnly cookie
POST /portal/logout → SessionFacade.invalidate → clear cookie → 204

Logout is idempotent. Does not touch Authentication / Authorization Domain.
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import ValidationError

from app.portal.authentication_facade import AuthenticationFacade
from app.portal.login_api_contract import LoginRequest, LoginResponse
from app.portal.session_cookie import SessionCookieFactory
from app.portal.session_facade import SessionFacade

ENGINE_ID = "portal_login_router_v1"

portal_login_router = APIRouter(prefix="/portal", tags=["portal-login"])

_auth_facade: AuthenticationFacade | None = None
_session_facade: SessionFacade | None = None
_cookie_factory: SessionCookieFactory | None = None


def set_authentication_facade(facade: AuthenticationFacade) -> None:
    global _auth_facade
    _auth_facade = facade


def set_session_login_deps(
    session_facade: SessionFacade,
    cookie_factory: SessionCookieFactory,
) -> None:
    global _session_facade, _cookie_factory
    _session_facade = session_facade
    _cookie_factory = cookie_factory


def clear_authentication_facade() -> None:
    global _auth_facade, _session_facade, _cookie_factory
    _auth_facade = None
    _session_facade = None
    _cookie_factory = None


def get_authentication_facade() -> AuthenticationFacade:
    if _auth_facade is None:
        raise HTTPException(status_code=503, detail="portal_login_not_configured")
    return _auth_facade


def get_session_facade() -> SessionFacade:
    if _session_facade is None:
        raise HTTPException(status_code=503, detail="portal_session_not_configured")
    return _session_facade


def get_cookie_factory() -> SessionCookieFactory:
    if _cookie_factory is None:
        raise HTTPException(status_code=503, detail="portal_session_not_configured")
    return _cookie_factory


@portal_login_router.post(
    "/login",
    response_model=LoginResponse,
)
async def http_post_login(
    request: Request,
    response: Response,
    auth: Annotated[AuthenticationFacade, Depends(get_authentication_facade)],
    sessions: Annotated[SessionFacade, Depends(get_session_facade)],
    cookies: Annotated[SessionCookieFactory, Depends(get_cookie_factory)],
) -> LoginResponse:
    """200 + authenticated bool. On success: create session + HttpOnly cookie."""
    try:
        raw: Any = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="invalid_json") from exc
    if not isinstance(raw, dict):
        raise HTTPException(status_code=400, detail="invalid_request")
    try:
        body = LoginRequest.model_validate(raw)
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail="invalid_request") from exc

    account_id = auth.login(email=body.email, password=body.password)
    if account_id is None:
        return LoginResponse(authenticated=False)

    session = sessions.start_session(account_id)
    spec = cookies.build(session.session_id)
    response.set_cookie(**spec.as_set_cookie_kwargs())
    return LoginResponse(authenticated=True)


@portal_login_router.post("/logout", status_code=204)
async def http_post_logout(
    request: Request,
    response: Response,
    sessions: Annotated[SessionFacade, Depends(get_session_facade)],
    cookies: Annotated[SessionCookieFactory, Depends(get_cookie_factory)],
) -> Response:
    """Invalidate server session (if any) and clear cookie. Always 204."""
    raw = request.cookies.get(cookies.cookie_name)
    if raw:
        sessions.invalidate_session(raw)
    response.delete_cookie(**cookies.as_delete_cookie_kwargs())
    response.status_code = 204
    return response
