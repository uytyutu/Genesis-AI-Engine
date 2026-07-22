"""R5.4 — Register ChatBot Integration module (integration reference).

Mounts GET/PUT /portal/websites/{id}/chatbot with AuthorizationFacade gate.
Wires StubChatBotIntegrationAdapter (no provider network).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.authorization_facade import AuthorizationFacade
from app.portal.chatbot_facade import ChatBotFacade
from app.portal.chatbot_integration_adapter import (
    ChatBotIntegrationAdapter,
    StubChatBotIntegrationAdapter,
)
from app.portal.chatbot_store import ChatBotStore, InMemoryChatBotStore
from app.portal.ownership_directory import (
    OwnershipDirectory,
    empty_ownership_directory,
)
from app.portal.portal_chatbot_router import (
    portal_chatbot_router,
    set_authorization_facade,
    set_chatbot_facade,
)

ENGINE_ID = "portal_chatbot_registration_v1"


def register_portal_chatbot(
    app: FastAPI,
    *,
    ownerships: OwnershipDirectory | None = None,
    store: ChatBotStore | None = None,
    adapter: ChatBotIntegrationAdapter | None = None,
) -> bool:
    """Wire ChatBot + Authorization + Integration Adapter and mount router."""
    ownership_dir = (
        ownerships if ownerships is not None else empty_ownership_directory()
    )
    chatbot_store = store if store is not None else InMemoryChatBotStore()
    integration = (
        adapter if adapter is not None else StubChatBotIntegrationAdapter()
    )
    set_chatbot_facade(
        ChatBotFacade.from_parts(chatbot_store, integration)
    )
    set_authorization_facade(AuthorizationFacade(ownership_dir))
    app.include_router(portal_chatbot_router)
    return True
