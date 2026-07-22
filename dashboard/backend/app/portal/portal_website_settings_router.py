"""R5.1 — Protected Website Settings HTTP (reference module).

GET/PUT /portal/websites/{website_id}/settings
→ RequestPrincipal → AuthorizationFacade → WebsiteSettingsFacade

Invariant:
  Authentication = who · Authorization = may · Module = what
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.website_settings import WebsiteSettingsError
from app.portal.website_settings_facade import WebsiteSettingsFacade
from app.portal.website_settings_view import WebsiteSettingsView

ENGINE_ID = "portal_website_settings_router_v1"

portal_website_settings_router = APIRouter(
    prefix="/portal",
    tags=["portal-website-settings"],
)

_settings_facade: WebsiteSettingsFacade | None = None
_authz_facade: AuthorizationFacade | None = None


class WebsiteSettingsWriteBody(BaseModel):
    """HTTP DTO — Basic Profile only."""

    website_name: str = Field(default="", max_length=200)
    company_name: str = Field(default="", max_length=200)
    contact_email: str = Field(default="", max_length=320)
    phone: str = Field(default="", max_length=64)
    social_links: dict[str, str] = Field(default_factory=dict)


def set_website_settings_facade(facade: WebsiteSettingsFacade) -> None:
    global _settings_facade
    _settings_facade = facade


def set_authorization_facade(facade: AuthorizationFacade) -> None:
    global _authz_facade
    _authz_facade = facade


def clear_website_settings_facade() -> None:
    global _settings_facade, _authz_facade
    _settings_facade = None
    _authz_facade = None


def get_website_settings_facade() -> WebsiteSettingsFacade:
    if _settings_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_website_settings_not_configured"
        )
    return _settings_facade


def get_authorization_facade() -> AuthorizationFacade:
    if _authz_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_authorization_not_configured"
        )
    return _authz_facade


def _require_authorized(
    request: Request,
    website_id: str,
    authz: AuthorizationFacade,
) -> None:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    decision = authz.check_website_access(account, website_id)
    if not decision.is_allowed:
        raise HTTPException(status_code=403, detail="forbidden")


@portal_website_settings_router.get(
    "/websites/{website_id}/settings",
    response_model=None,
)
def http_get_settings(
    website_id: str,
    request: Request,
    settings: Annotated[
        WebsiteSettingsFacade, Depends(get_website_settings_facade)
    ],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> WebsiteSettingsView:
    _require_authorized(request, website_id, authz)
    return settings.get_settings(website_id)


@portal_website_settings_router.put(
    "/websites/{website_id}/settings",
    response_model=None,
)
def http_put_settings(
    website_id: str,
    body: WebsiteSettingsWriteBody,
    request: Request,
    settings: Annotated[
        WebsiteSettingsFacade, Depends(get_website_settings_facade)
    ],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> WebsiteSettingsView:
    _require_authorized(request, website_id, authz)
    try:
        return settings.update_settings(
            website_id,
            website_name=body.website_name,
            company_name=body.company_name,
            contact_email=body.contact_email,
            phone=body.phone,
            social_links=body.social_links,
        )
    except WebsiteSettingsError:
        raise HTTPException(status_code=400, detail="invalid_settings") from None
