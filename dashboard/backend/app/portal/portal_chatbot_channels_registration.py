"""Business Product BP1.3 — Register Channel Connections (stub)."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.channel_connection_facade import ChannelConnectionFacade
from app.portal.channel_connection_store import (
    ChannelConnectionStore,
    InMemoryChannelConnectionStore,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.portal_chatbot_channels_router import (
    portal_chatbot_channels_router,
    set_channel_connection_facade,
)

ENGINE_ID = "portal_chatbot_channels_registration_v1"


def register_portal_chatbot_channels(
    app: FastAPI,
    *,
    profiles: ChatBotBusinessProfileStore,
    channel_store: ChannelConnectionStore | None = None,
) -> ChannelConnectionFacade:
    facade = ChannelConnectionFacade.from_parts(
        profiles=profiles,
        channels=channel_store
        if channel_store is not None
        else InMemoryChannelConnectionStore(),
    )
    set_channel_connection_facade(facade)
    app.include_router(portal_chatbot_channels_router)
    return facade
