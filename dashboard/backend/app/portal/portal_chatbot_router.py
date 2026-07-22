"""R5.4 — Protected ChatBot Integration HTTP (integration reference module).

GET/PUT /portal/websites/{website_id}/chatbot
→ RequestPrincipal → AuthorizationFacade → ChatBotFacade

Invariant:
  Authentication = who · Authorization = may · Module = what
  Provider SDKs never appear in this router.
"""

from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.chatbot import ChatBotError
from app.portal.chatbot_facade import ChatBotFacade
from app.portal.chatbot_view import ChatBotView

ENGINE_ID = "portal_chatbot_router_v1"

portal_chatbot_router = APIRouter(
    prefix="/portal",
    tags=["portal-chatbot"],
)

_chatbot_facade: ChatBotFacade | None = None
_authz_facade: AuthorizationFacade | None = None


class ChatBotWriteBody(BaseModel):
    """HTTP DTO — integration config only (stable when real providers arrive)."""

    enabled: bool = False
    provider: Literal["none", "openai", "local"] = "none"
    status: Literal["disconnected", "pending", "connected", "error"] = "disconnected"
    assistant_id: str | None = Field(default=None, max_length=200)


def set_chatbot_facade(facade: ChatBotFacade) -> None:
    global _chatbot_facade
    _chatbot_facade = facade


def set_authorization_facade(facade: AuthorizationFacade) -> None:
    global _authz_facade
    _authz_facade = facade


def clear_chatbot_facade() -> None:
    global _chatbot_facade, _authz_facade
    _chatbot_facade = None
    _authz_facade = None


def get_chatbot_facade() -> ChatBotFacade:
    if _chatbot_facade is None:
        raise HTTPException(status_code=503, detail="portal_chatbot_not_configured")
    return _chatbot_facade


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


@portal_chatbot_router.get(
    "/websites/{website_id}/chatbot",
    response_model=None,
)
def http_get_chatbot(
    website_id: str,
    request: Request,
    chatbot: Annotated[ChatBotFacade, Depends(get_chatbot_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> ChatBotView:
    _require_authorized(request, website_id, authz)
    return chatbot.get_chatbot(website_id)


@portal_chatbot_router.put(
    "/websites/{website_id}/chatbot",
    response_model=None,
)
def http_put_chatbot(
    website_id: str,
    body: ChatBotWriteBody,
    request: Request,
    chatbot: Annotated[ChatBotFacade, Depends(get_chatbot_facade)],
    authz: Annotated[AuthorizationFacade, Depends(get_authorization_facade)],
) -> ChatBotView:
    _require_authorized(request, website_id, authz)
    try:
        return chatbot.update_chatbot(
            website_id,
            enabled=body.enabled,
            provider=body.provider,
            status=body.status,
            assistant_id=body.assistant_id,
        )
    except ChatBotError:
        raise HTTPException(status_code=400, detail="invalid_chatbot") from None
