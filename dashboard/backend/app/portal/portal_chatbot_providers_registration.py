"""AI Platform AP1.1 — Register Provider Layer."""

from __future__ import annotations

from fastapi import FastAPI

from app.portal.ai_provider_facade import AIProviderFacade
from app.portal.ai_provider_store import AIProviderStore, InMemoryAIProviderStore
from app.portal.portal_chatbot_providers_router import (
    portal_chatbot_providers_router,
    set_ai_provider_facade,
)

ENGINE_ID = "portal_chatbot_providers_registration_v1"


def register_portal_chatbot_providers(
    app: FastAPI,
    *,
    store: AIProviderStore | None = None,
    seed_stubs: bool = True,
) -> AIProviderFacade:
    facade = AIProviderFacade.from_parts(
        store=store if store is not None else InMemoryAIProviderStore(),
        seed_stubs=seed_stubs,
    )
    set_ai_provider_facade(facade)
    app.include_router(portal_chatbot_providers_router)
    return facade
