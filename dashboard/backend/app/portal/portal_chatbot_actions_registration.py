"""PT4 — Register Business Actions."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.business_action_facade import BusinessActionFacade
from app.portal.business_action_store import BusinessActionStore
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.conversation_facade import ConversationFacade
from app.portal.portal_chatbot_actions_router import (
    portal_chatbot_actions_router,
    set_business_action_facade,
)

ENGINE_ID = "portal_chatbot_actions_registration_v1"


def register_portal_chatbot_actions(
    app: FastAPI,
    *,
    conversations: ConversationFacade,
    knowledge: BusinessKnowledgeFacade,
    store: BusinessActionStore | None = None,
) -> BusinessActionFacade:
    facade = BusinessActionFacade.from_parts(
        conversations=conversations,
        knowledge=knowledge,
        store=store,
    )
    set_business_action_facade(facade)
    app.include_router(portal_chatbot_actions_router)
    return facade
