"""Business Product BP1.4 — Conversation Engine HTTP (stub).

POST /portal/chatbot/conversations
GET  /portal/chatbot/conversations
GET  /portal/chatbot/conversations/{conversation_id}
POST /portal/chatbot/conversations/{conversation_id}/messages
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from app.portal.conversation import ConversationError
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_assistance_view import (
    AssistanceDraftView,
    AssistanceReviewView,
    AssistanceSummaryView,
)
from app.portal.conversation_view import ConversationTurnView, ConversationView

ENGINE_ID = "portal_chatbot_conversations_router_v1"

portal_chatbot_conversations_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-conversations"],
)

_conversation_facade: ConversationFacade | None = None


class ConversationCreateBody(BaseModel):
    channel_connection_id: str | None = Field(default=None, max_length=64)


class MessageCreateBody(BaseModel):
    content: str = Field(min_length=1, max_length=8000)
    categories: list[str] | None = None


class ConversationStatusBody(BaseModel):
    status: str = Field(min_length=1, max_length=32)


def set_conversation_facade(facade: ConversationFacade) -> None:
    global _conversation_facade
    _conversation_facade = facade


def clear_conversation_facade() -> None:
    global _conversation_facade
    _conversation_facade = None


def get_conversation_facade() -> ConversationFacade:
    if _conversation_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_conversations_not_configured"
        )
    return _conversation_facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


def _map_error(exc: ConversationError) -> HTTPException:
    detail = str(exc)
    if detail in {"conversation_not_found", "channel_not_found"}:
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@portal_chatbot_conversations_router.post("/conversations", response_model=None)
def http_create_conversation(
    body: ConversationCreateBody,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> ConversationView:
    account_id = _require_account(request)
    try:
        return facade.create_conversation(
            account_id=account_id,
            channel_connection_id=body.channel_connection_id,
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.get("/conversations", response_model=None)
def http_list_conversations(
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> list[ConversationView]:
    account_id = _require_account(request)
    try:
        return facade.list_conversations(account_id=account_id)
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.get(
    "/conversations/{conversation_id}", response_model=None
)
def http_get_conversation(
    conversation_id: str,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> ConversationView:
    account_id = _require_account(request)
    try:
        return facade.get_conversation(
            account_id=account_id, conversation_id=conversation_id
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.put(
    "/conversations/{conversation_id}/status",
    response_model=None,
)
def http_set_conversation_status(
    conversation_id: str,
    body: ConversationStatusBody,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> ConversationView:
    """Lifecycle only (open/prepared/closed) — no AI · no channel IO."""
    account_id = _require_account(request)
    try:
        return facade.set_conversation_status(
            account_id=account_id,
            conversation_id=conversation_id,
            status=body.status,
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.post(
    "/conversations/{conversation_id}/assistance/draft",
    response_model=None,
)
def http_assistance_draft(
    conversation_id: str,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> AssistanceDraftView:
    """Draft reply for operator — never auto-sends to customer."""
    account_id = _require_account(request)
    try:
        return facade.draft_reply(
            account_id=account_id, conversation_id=conversation_id
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.post(
    "/conversations/{conversation_id}/assistance/summary",
    response_model=None,
)
def http_assistance_summary(
    conversation_id: str,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> AssistanceSummaryView:
    """Conversation summary for operator — never auto-sends."""
    account_id = _require_account(request)
    try:
        return facade.summarize(
            account_id=account_id, conversation_id=conversation_id
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.get(
    "/conversations/{conversation_id}/assistance/review",
    response_model=None,
)
def http_assistance_review(
    conversation_id: str,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> AssistanceReviewView:
    """Priority · tags · knowledge suggestions — display only."""
    account_id = _require_account(request)
    try:
        return facade.review_panel(
            account_id=account_id, conversation_id=conversation_id
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_conversations_router.post(
    "/conversations/{conversation_id}/messages", response_model=None
)
def http_post_message(
    conversation_id: str,
    body: MessageCreateBody,
    request: Request,
    facade: Annotated[ConversationFacade, Depends(get_conversation_facade)],
) -> ConversationTurnView:
    account_id = _require_account(request)
    try:
        return facade.post_message(
            account_id=account_id,
            conversation_id=conversation_id,
            content=body.content,
            categories=body.categories,
        )
    except ConversationError as exc:
        raise _map_error(exc) from exc
