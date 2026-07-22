"""Business Product BP1.2 — Business Knowledge HTTP.

GET    /portal/chatbot/knowledge
POST   /portal/chatbot/knowledge
PUT    /portal/chatbot/knowledge/{knowledge_id}
DELETE /portal/chatbot/knowledge/{knowledge_id}
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.portal.business_knowledge import BusinessKnowledgeError
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_view import BusinessKnowledgeView

ENGINE_ID = "portal_chatbot_knowledge_router_v1"

portal_chatbot_knowledge_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-knowledge"],
)

_knowledge_facade: BusinessKnowledgeFacade | None = None


class KnowledgeWriteBody(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=8000)


class KnowledgeUpdateBody(BaseModel):
    category: str | None = Field(default=None, max_length=64)
    title: str | None = Field(default=None, max_length=200)
    content: str | None = Field(default=None, max_length=8000)


def set_business_knowledge_facade(facade: BusinessKnowledgeFacade) -> None:
    global _knowledge_facade
    _knowledge_facade = facade


def clear_business_knowledge_facade() -> None:
    global _knowledge_facade
    _knowledge_facade = None


def get_business_knowledge_facade() -> BusinessKnowledgeFacade:
    if _knowledge_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_knowledge_not_configured"
        )
    return _knowledge_facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


def _map_error(exc: BusinessKnowledgeError) -> HTTPException:
    detail = str(exc)
    if detail == "knowledge_not_found":
        return HTTPException(status_code=404, detail=detail)
    if detail == "profile_required":
        return HTTPException(status_code=400, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@portal_chatbot_knowledge_router.get("/knowledge", response_model=None)
def http_list_knowledge(
    request: Request,
    knowledge: Annotated[
        BusinessKnowledgeFacade, Depends(get_business_knowledge_facade)
    ],
    category: Annotated[str | None, Query()] = None,
) -> list[BusinessKnowledgeView]:
    account_id = _require_account(request)
    try:
        return knowledge.list_knowledge(account_id=account_id, category=category)
    except BusinessKnowledgeError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_knowledge_router.post("/knowledge", response_model=None)
def http_create_knowledge(
    body: KnowledgeWriteBody,
    request: Request,
    knowledge: Annotated[
        BusinessKnowledgeFacade, Depends(get_business_knowledge_facade)
    ],
) -> BusinessKnowledgeView:
    account_id = _require_account(request)
    try:
        return knowledge.create_knowledge(
            account_id=account_id,
            category=body.category,
            title=body.title,
            content=body.content,
        )
    except BusinessKnowledgeError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_knowledge_router.put(
    "/knowledge/{knowledge_id}", response_model=None
)
def http_update_knowledge(
    knowledge_id: str,
    body: KnowledgeUpdateBody,
    request: Request,
    knowledge: Annotated[
        BusinessKnowledgeFacade, Depends(get_business_knowledge_facade)
    ],
) -> BusinessKnowledgeView:
    account_id = _require_account(request)
    try:
        return knowledge.update_knowledge(
            account_id=account_id,
            knowledge_id=knowledge_id,
            category=body.category,
            title=body.title,
            content=body.content,
        )
    except BusinessKnowledgeError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_knowledge_router.delete(
    "/knowledge/{knowledge_id}", response_model=None
)
def http_delete_knowledge(
    knowledge_id: str,
    request: Request,
    knowledge: Annotated[
        BusinessKnowledgeFacade, Depends(get_business_knowledge_facade)
    ],
) -> Response:
    account_id = _require_account(request)
    try:
        knowledge.delete_knowledge(
            account_id=account_id, knowledge_id=knowledge_id
        )
    except BusinessKnowledgeError as exc:
        raise _map_error(exc) from exc
    return Response(status_code=204)
