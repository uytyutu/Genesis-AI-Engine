"""Business Product BP1.1 — ChatBot Business Profile HTTP.

GET  /portal/chatbot/profile
PUT  /portal/chatbot/profile
GET  /portal/chatbot/templates
POST /portal/chatbot/profile/bootstrap

Separate from R5.4 website integration `/portal/websites/{id}/chatbot`.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.chatbot_business_profile import ChatBotProfileError
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_view import (
    ChatBotBusinessProfileView,
    IndustryTemplateView,
)

ENGINE_ID = "portal_chatbot_product_router_v1"

portal_chatbot_product_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-product"],
)

_facade: ChatBotBusinessProfileFacade | None = None


class ProfileWriteBody(BaseModel):
    business_name: str | None = Field(default=None, max_length=200)
    industry: str | None = Field(default=None, max_length=64)
    description: str | None = Field(default=None, max_length=4000)
    language: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)


class BootstrapBody(BaseModel):
    industry: str = Field(min_length=1, max_length=64)
    business_name: str | None = Field(default=None, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    language: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)


def set_chatbot_business_profile_facade(
    facade: ChatBotBusinessProfileFacade,
) -> None:
    global _facade
    _facade = facade


def clear_chatbot_business_profile_facade() -> None:
    global _facade
    _facade = None


def get_chatbot_business_profile_facade() -> ChatBotBusinessProfileFacade:
    if _facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_product_not_configured"
        )
    return _facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


@portal_chatbot_product_router.get("/profile", response_model=None)
def http_get_profile(
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> ChatBotBusinessProfileView:
    account_id = _require_account(request)
    view = facade.get_profile(account_id=account_id)
    if view is None:
        raise HTTPException(status_code=404, detail="profile_not_found")
    return view


@portal_chatbot_product_router.put("/profile", response_model=None)
def http_put_profile(
    body: ProfileWriteBody,
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> ChatBotBusinessProfileView:
    account_id = _require_account(request)
    try:
        return facade.upsert_profile(
            account_id=account_id,
            business_name=body.business_name,
            industry=body.industry,
            description=body.description,
            language=body.language,
            timezone=body.timezone,
        )
    except ChatBotProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@portal_chatbot_product_router.get("/templates", response_model=None)
def http_list_templates(
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> list[IndustryTemplateView]:
    _require_account(request)
    return facade.list_templates()


@portal_chatbot_product_router.post("/profile/bootstrap", response_model=None)
def http_bootstrap_profile(
    body: BootstrapBody,
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> ChatBotBusinessProfileView:
    account_id = _require_account(request)
    try:
        return facade.bootstrap(
            account_id=account_id,
            industry=body.industry,
            business_name=body.business_name,
            description=body.description,
            language=body.language,
            timezone=body.timezone,
        )
    except ChatBotProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
