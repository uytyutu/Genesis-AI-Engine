"""Business Product BP1.1 — Register ChatBot Business Profile APIs."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import (
    ChatBotBusinessProfileStore,
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.industry_template import (
    InMemoryIndustryTemplateStore,
    IndustryTemplateStore,
)
from app.portal.portal_chatbot_product_router import (
    portal_chatbot_product_router,
    set_chatbot_business_profile_facade,
)

ENGINE_ID = "portal_chatbot_product_registration_v1"


def register_portal_chatbot_product(
    app: FastAPI,
    *,
    profile_store: ChatBotBusinessProfileStore | None = None,
    template_store: IndustryTemplateStore | None = None,
) -> ChatBotBusinessProfileFacade:
    facade = ChatBotBusinessProfileFacade.from_parts(
        profiles=profile_store
        if profile_store is not None
        else InMemoryChatBotBusinessProfileStore(),
        templates=template_store
        if template_store is not None
        else InMemoryIndustryTemplateStore(),
    )
    set_chatbot_business_profile_facade(facade)
    app.include_router(portal_chatbot_product_router)
    return facade
