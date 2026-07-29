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


class QuestionnaireBody(BaseModel):
    business_name: str = Field(min_length=1, max_length=200)
    what_company_does: str = Field(default="", max_length=4000)
    services: str = Field(default="", max_length=4000)
    answer_topics: str = Field(default="", max_length=4000)
    avoid_topics: str = Field(default="", max_length=4000)
    working_hours: str = Field(default="", max_length=500)
    address: str = Field(default="", max_length=500)
    phone: str = Field(default="", max_length=80)
    website: str = Field(default="", max_length=300)
    language: str = Field(default="en", max_length=16)
    tone: str = Field(default="professional_friendly", max_length=64)
    industry: str = Field(default="other", max_length=64)
    book_appointments: bool = True
    take_leads: bool = True
    give_prices: bool = False
    timezone: str = Field(default="Europe/Berlin", max_length=64)

    def as_answers(self) -> dict:
        return self.model_dump()


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


@portal_chatbot_product_router.post("/setup/preview", response_model=None)
def http_setup_preview(
    body: QuestionnaireBody,
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> dict:
    """Client questionnaire → preview (no CEO)."""
    _require_account(request)
    try:
        return facade.preview_setup(answers=body.as_answers())
    except ChatBotProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@portal_chatbot_product_router.post("/setup/publish", response_model=None)
def http_setup_publish(
    body: QuestionnaireBody,
    request: Request,
    facade: Annotated[
        ChatBotBusinessProfileFacade, Depends(get_chatbot_business_profile_facade)
    ],
) -> dict:
    """Client publishes digital employee — self-serve, no owner approve."""
    account_id = _require_account(request)
    try:
        result = facade.publish_setup(account_id=account_id, answers=body.as_answers())
    except ChatBotProfileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        from app.portal.portal_chatbot_knowledge_router import get_business_knowledge_facade

        knowledge = get_business_knowledge_facade()
        for row in result.get("knowledge") or []:
            try:
                knowledge.create_knowledge(
                    account_id=account_id,
                    category=str(row.get("category") or "company"),
                    title=str(row.get("title") or "Fact"),
                    content=str(row.get("content") or ""),
                )
            except Exception:
                continue
    except Exception:
        pass

    try:
        from app.portal.portal_chatbot_channels_router import get_channel_connection_facade

        channels = get_channel_connection_facade()
        existing = channels.list_channels(account_id=account_id)
        has_website = any(
            (getattr(c, "channel", None) or "") == "website" for c in existing
        )
        if not has_website:
            channels.create_channel(
                account_id=account_id,
                channel="website",
                display_name="Website chat",
                status="connected",
            )
    except Exception:
        pass

    result["ceo_approve_required"] = False
    return result
