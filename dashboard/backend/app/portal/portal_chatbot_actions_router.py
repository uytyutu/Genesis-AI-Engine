"""PT4 — Business Actions HTTP.

GET  /portal/chatbot/actions
POST /portal/chatbot/actions
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from app.portal.business_action import BusinessActionError
from app.portal.business_action_facade import BusinessActionFacade
from app.portal.business_action_view import BusinessActionView

ENGINE_ID = "portal_chatbot_actions_router_v1"

portal_chatbot_actions_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-actions"],
)

_facade: BusinessActionFacade | None = None


class ActionExecuteBody(BaseModel):
    action_type: str = Field(min_length=1, max_length=64)
    approved: bool = False
    conversation_id: str | None = Field(default=None, max_length=64)
    payload: dict[str, Any] | None = None


def set_business_action_facade(facade: BusinessActionFacade) -> None:
    global _facade
    _facade = facade


def clear_business_action_facade() -> None:
    global _facade
    _facade = None


def get_business_action_facade() -> BusinessActionFacade:
    if _facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_actions_not_configured"
        )
    return _facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


def _map_error(exc: BusinessActionError) -> HTTPException:
    detail = str(exc)
    if detail == "approval_required":
        return HTTPException(status_code=400, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@portal_chatbot_actions_router.get("/actions", response_model=None)
def http_list_actions(
    request: Request,
    actions: Annotated[BusinessActionFacade, Depends(get_business_action_facade)],
    conversation_id: Annotated[str | None, Query()] = None,
) -> list[BusinessActionView]:
    account_id = _require_account(request)
    return actions.list_actions(
        account_id=account_id, conversation_id=conversation_id
    )


@portal_chatbot_actions_router.post("/actions", response_model=None)
def http_execute_action(
    body: ActionExecuteBody,
    request: Request,
    actions: Annotated[BusinessActionFacade, Depends(get_business_action_facade)],
) -> BusinessActionView:
    account_id = _require_account(request)
    try:
        return actions.execute(
            account_id=account_id,
            action_type=body.action_type,
            approved=body.approved,
            conversation_id=body.conversation_id,
            payload=body.payload,
        )
    except BusinessActionError as exc:
        raise _map_error(exc) from exc
