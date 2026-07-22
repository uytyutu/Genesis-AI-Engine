"""Business Product BP1.4 — Register Conversation Engine (stub)."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.business_knowledge_store import BusinessKnowledgeStore
from app.portal.channel_connection_store import ChannelConnectionStore
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import ConversationStore, MessageStore
from app.portal.industry_template import IndustryTemplateStore
from app.portal.portal_chatbot_conversations_router import (
    portal_chatbot_conversations_router,
    set_conversation_facade,
)

ENGINE_ID = "portal_chatbot_conversations_registration_v1"


def register_portal_chatbot_conversations(
    app: FastAPI,
    *,
    profiles: ChatBotBusinessProfileStore,
    knowledge: BusinessKnowledgeStore,
    channels: ChannelConnectionStore,
    templates: IndustryTemplateStore,
    conversation_store: ConversationStore | None = None,
    message_store: MessageStore | None = None,
) -> ConversationFacade:
    facade = ConversationFacade.from_parts(
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
        conversations=conversation_store,
        messages=message_store,
    )
    set_conversation_facade(facade)
    app.include_router(portal_chatbot_conversations_router)
    return facade
