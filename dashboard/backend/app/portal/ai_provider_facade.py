"""AI Platform AP1.1 — AIProviderFacade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.ai_provider import AIProviderError
from app.portal.ai_provider_manager import AIProviderManager
from app.portal.ai_provider_protocol import AIGenerationResult, AIProviderHealth
from app.portal.ai_provider_registry import AIProviderRegistry
from app.portal.ai_provider_store import AIProviderStore, InMemoryAIProviderStore
from app.portal.ai_provider_view import AIProviderView
from app.portal.conversation import ConversationContext

ENGINE_ID = "ai_provider_facade_v1"


@dataclass(frozen=True)
class AIProviderFacade:
    _manager: AIProviderManager

    @classmethod
    def from_parts(
        cls,
        *,
        store: AIProviderStore | None = None,
        registry: AIProviderRegistry | None = None,
        seed_stubs: bool = True,
    ) -> AIProviderFacade:
        manager = AIProviderManager(
            store=store if store is not None else InMemoryAIProviderStore(),
            registry=registry,
        )
        if seed_stubs:
            manager.seed_default_stubs()
        return cls(_manager=manager)

    @property
    def manager(self) -> AIProviderManager:
        return self._manager

    def list_providers(self) -> list[AIProviderView]:
        return self._manager.list_providers()

    def create_provider(
        self,
        *,
        provider_type: str,
        display_name: str | None = None,
        status: str = "not_configured",
        configuration: dict[str, Any] | None = None,
    ) -> AIProviderView:
        try:
            return self._manager.create(
                provider_type=provider_type,
                display_name=display_name,
                status=status,
                configuration=configuration,
            )
        except AIProviderError:
            raise

    def update_provider(
        self,
        *,
        provider_id: str,
        display_name: str | None = None,
        status: str | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> AIProviderView:
        try:
            return self._manager.update(
                provider_id=provider_id,
                display_name=display_name,
                status=status,
                configuration=configuration,
            )
        except AIProviderError:
            raise

    def delete_provider(self, *, provider_id: str) -> None:
        try:
            self._manager.delete(provider_id=provider_id)
        except AIProviderError:
            raise

    def health(self, *, provider_id: str) -> AIProviderHealth:
        try:
            return self._manager.health(provider_id=provider_id)
        except AIProviderError:
            raise

    def generate(self, context: ConversationContext) -> AIGenerationResult:
        return self._manager.generate(context)
