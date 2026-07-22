"""AI Platform AP1.1 — Provider Layer HTTP.

GET    /portal/chatbot/providers
POST   /portal/chatbot/providers
PUT    /portal/chatbot/providers/{provider_id}
DELETE /portal/chatbot/providers/{provider_id}
POST   /portal/chatbot/providers/{provider_id}/health
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

from app.portal.ai_provider import AIProviderError
from app.portal.ai_provider_facade import AIProviderFacade
from app.portal.ai_provider_protocol import AIProviderHealth
from app.portal.ai_provider_view import AIProviderView

ENGINE_ID = "portal_chatbot_providers_router_v1"

portal_chatbot_providers_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-providers"],
)

_provider_facade: AIProviderFacade | None = None


class ProviderCreateBody(BaseModel):
    provider_type: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=200)
    status: str = Field(default="not_configured", max_length=32)
    configuration: dict[str, Any] | None = None


class ProviderUpdateBody(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=32)
    configuration: dict[str, Any] | None = None


def set_ai_provider_facade(facade: AIProviderFacade) -> None:
    global _provider_facade
    _provider_facade = facade


def clear_ai_provider_facade() -> None:
    global _provider_facade
    _provider_facade = None


def get_ai_provider_facade() -> AIProviderFacade:
    if _provider_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_providers_not_configured"
        )
    return _provider_facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


def _map_error(exc: AIProviderError) -> HTTPException:
    detail = str(exc)
    if detail == "provider_not_found":
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@portal_chatbot_providers_router.get("/providers", response_model=None)
def http_list_providers(
    request: Request,
    facade: Annotated[AIProviderFacade, Depends(get_ai_provider_facade)],
) -> list[AIProviderView]:
    _require_account(request)
    return facade.list_providers()


@portal_chatbot_providers_router.post("/providers", response_model=None)
def http_create_provider(
    body: ProviderCreateBody,
    request: Request,
    facade: Annotated[AIProviderFacade, Depends(get_ai_provider_facade)],
) -> AIProviderView:
    _require_account(request)
    try:
        return facade.create_provider(
            provider_type=body.provider_type,
            display_name=body.display_name,
            status=body.status,
            configuration=body.configuration,
        )
    except AIProviderError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_providers_router.put(
    "/providers/{provider_id}", response_model=None
)
def http_update_provider(
    provider_id: str,
    body: ProviderUpdateBody,
    request: Request,
    facade: Annotated[AIProviderFacade, Depends(get_ai_provider_facade)],
) -> AIProviderView:
    _require_account(request)
    try:
        return facade.update_provider(
            provider_id=provider_id,
            display_name=body.display_name,
            status=body.status,
            configuration=body.configuration,
        )
    except AIProviderError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_providers_router.delete(
    "/providers/{provider_id}", response_model=None
)
def http_delete_provider(
    provider_id: str,
    request: Request,
    facade: Annotated[AIProviderFacade, Depends(get_ai_provider_facade)],
) -> Response:
    _require_account(request)
    try:
        facade.delete_provider(provider_id=provider_id)
    except AIProviderError as exc:
        raise _map_error(exc) from exc
    return Response(status_code=204)


@portal_chatbot_providers_router.post(
    "/providers/{provider_id}/health", response_model=None
)
def http_provider_health(
    provider_id: str,
    request: Request,
    facade: Annotated[AIProviderFacade, Depends(get_ai_provider_facade)],
) -> AIProviderHealth:
    _require_account(request)
    try:
        return facade.health(provider_id=provider_id)
    except AIProviderError as exc:
        raise _map_error(exc) from exc
