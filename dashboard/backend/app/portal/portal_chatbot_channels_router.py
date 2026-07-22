"""Business Product BP1.3 — Channel Connections HTTP (stub registry).

GET    /portal/chatbot/channels
POST   /portal/chatbot/channels
PUT    /portal/chatbot/channels/{connection_id}
DELETE /portal/chatbot/channels/{connection_id}
"""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, Field

from app.portal.channel_connection import ChannelConnectionError
from app.portal.channel_connection_facade import ChannelConnectionFacade
from app.portal.channel_connection_view import ChannelConnectionView

ENGINE_ID = "portal_chatbot_channels_router_v1"

portal_chatbot_channels_router = APIRouter(
    prefix="/portal/chatbot",
    tags=["portal-chatbot-channels"],
)

_channels_facade: ChannelConnectionFacade | None = None


class ChannelCreateBody(BaseModel):
    channel: str = Field(min_length=1, max_length=64)
    display_name: str | None = Field(default=None, max_length=200)
    status: str = Field(default="not_configured", max_length=32)
    configuration: dict[str, Any] | None = None


class ChannelUpdateBody(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    status: str | None = Field(default=None, max_length=32)
    configuration: dict[str, Any] | None = None


def set_channel_connection_facade(facade: ChannelConnectionFacade) -> None:
    global _channels_facade
    _channels_facade = facade


def clear_channel_connection_facade() -> None:
    global _channels_facade
    _channels_facade = None


def get_channel_connection_facade() -> ChannelConnectionFacade:
    if _channels_facade is None:
        raise HTTPException(
            status_code=503, detail="portal_chatbot_channels_not_configured"
        )
    return _channels_facade


def _require_account(request: Request) -> str:
    account = getattr(request.state, "account", None)
    if account is None:
        raise HTTPException(status_code=401, detail="unauthorized")
    return account.account_id


def _map_error(exc: ChannelConnectionError) -> HTTPException:
    detail = str(exc)
    if detail == "connection_not_found":
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@portal_chatbot_channels_router.get("/channels", response_model=None)
def http_list_channels(
    request: Request,
    channels: Annotated[
        ChannelConnectionFacade, Depends(get_channel_connection_facade)
    ],
    channel: Annotated[str | None, Query()] = None,
) -> list[ChannelConnectionView]:
    account_id = _require_account(request)
    try:
        return channels.list_channels(account_id=account_id, channel=channel)
    except ChannelConnectionError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_channels_router.post("/channels", response_model=None)
def http_create_channel(
    body: ChannelCreateBody,
    request: Request,
    channels: Annotated[
        ChannelConnectionFacade, Depends(get_channel_connection_facade)
    ],
) -> ChannelConnectionView:
    account_id = _require_account(request)
    try:
        return channels.create_channel(
            account_id=account_id,
            channel=body.channel,
            display_name=body.display_name,
            status=body.status,
            configuration=body.configuration,
        )
    except ChannelConnectionError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_channels_router.put(
    "/channels/{connection_id}", response_model=None
)
def http_update_channel(
    connection_id: str,
    body: ChannelUpdateBody,
    request: Request,
    channels: Annotated[
        ChannelConnectionFacade, Depends(get_channel_connection_facade)
    ],
) -> ChannelConnectionView:
    account_id = _require_account(request)
    try:
        return channels.update_channel(
            account_id=account_id,
            connection_id=connection_id,
            display_name=body.display_name,
            status=body.status,
            configuration=body.configuration,
        )
    except ChannelConnectionError as exc:
        raise _map_error(exc) from exc


@portal_chatbot_channels_router.delete(
    "/channels/{connection_id}", response_model=None
)
def http_delete_channel(
    connection_id: str,
    request: Request,
    channels: Annotated[
        ChannelConnectionFacade, Depends(get_channel_connection_facade)
    ],
) -> Response:
    account_id = _require_account(request)
    try:
        channels.delete_channel(
            account_id=account_id, connection_id=connection_id
        )
    except ChannelConnectionError as exc:
        raise _map_error(exc) from exc
    return Response(status_code=204)
