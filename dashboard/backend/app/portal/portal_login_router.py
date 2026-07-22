"""R4.1 — HTTP Login Endpoint.

POST /portal/login → AuthenticationFacade → {authenticated: bool}

No Session · Cookie · JWT · Middleware · Protected routes.
Malformed body → 400 (not domain failure details).
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import ValidationError

from app.portal.authentication_facade import AuthenticationFacade
from app.portal.login_api_contract import LoginRequest, LoginResponse

ENGINE_ID = "portal_login_router_v1"

portal_login_router = APIRouter(prefix="/portal", tags=["portal-login"])

_facade: AuthenticationFacade | None = None


def set_authentication_facade(facade: AuthenticationFacade) -> None:
    global _facade
    _facade = facade


def clear_authentication_facade() -> None:
    global _facade
    _facade = None


def get_authentication_facade() -> AuthenticationFacade:
    if _facade is None:
        raise HTTPException(status_code=503, detail="portal_login_not_configured")
    return _facade


@portal_login_router.post(
    "/login",
    response_model=LoginResponse,
)
async def http_post_login(
    request: Request,
    facade: Annotated[AuthenticationFacade, Depends(get_authentication_facade)],
) -> LoginResponse:
    """200 + authenticated bool when body OK. 400 for bad format. No cookies."""
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

    ok = facade.login(email=body.email, password=body.password)
    return LoginResponse(authenticated=ok)
