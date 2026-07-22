"""OR3 — Ops metrics HTTP surface."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request

from app.portal.operational_metrics import get_operational_metrics

ENGINE_ID = "portal_chatbot_ops_router_v1"

portal_chatbot_ops_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-ops"],
)


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


@portal_chatbot_ops_router.get("/ops/metrics", response_model=None)
def http_ops_metrics(
    request: Request,
    _account_id: Annotated[str, Depends(_require_account)],
) -> dict[str, Any]:
    return get_operational_metrics().snapshot()
