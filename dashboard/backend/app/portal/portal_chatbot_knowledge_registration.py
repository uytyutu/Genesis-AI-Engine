"""Business Product BP1.2 — Register Business Knowledge APIs."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_store import (
    BusinessKnowledgeStore,
    InMemoryBusinessKnowledgeStore,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.portal_chatbot_knowledge_router import (
    portal_chatbot_knowledge_router,
    set_business_knowledge_facade,
)

ENGINE_ID = "portal_chatbot_knowledge_registration_v1"


def register_portal_chatbot_knowledge(
    app: FastAPI,
    *,
    profiles: ChatBotBusinessProfileStore,
    knowledge_store: BusinessKnowledgeStore | None = None,
) -> BusinessKnowledgeFacade:
    facade = BusinessKnowledgeFacade.from_parts(
        profiles=profiles,
        knowledge=knowledge_store
        if knowledge_store is not None
        else InMemoryBusinessKnowledgeStore(),
    )
    set_business_knowledge_facade(facade)
    app.include_router(portal_chatbot_knowledge_router)
    return facade
