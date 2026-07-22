"""AI Platform AP1.1 — AIProviderManager (lifecycle + Protocol gateway)."""

from __future__ import annotations

from typing import Any

from app.portal.ai_provider import (
    AIProviderError,
    STUB_UNAVAILABLE_REPLY,
    apply_provider_update,
    new_ai_provider,
)
from app.portal.ai_provider_protocol import (
    AIGenerationResult,
    AIProviderHealth,
    AIProviderProtocol,
)
from app.portal.ai_provider_registry import AIProviderRegistry
from app.portal.ai_provider_store import AIProviderStore
from app.portal.ai_provider_view import AIProviderView, build_provider_view
from app.portal.conversation import ConversationContext
from app.portal.prompt_facade import PromptFacade

ENGINE_ID = "ai_provider_manager_v1"

_PROVIDER_TYPE_ORDER = ("openai", "anthropic", "ollama", "custom")


class AIProviderManager:
    def __init__(
        self,
        *,
        store: AIProviderStore,
        registry: AIProviderRegistry | None = None,
        prompts: PromptFacade | None = None,
    ) -> None:
        self._store = store
        self._registry = registry if registry is not None else AIProviderRegistry()
        self._prompts = prompts if prompts is not None else PromptFacade()

    def list_providers(self) -> list[AIProviderView]:
        rows = list(self._store.list_all())
        order = {name: index for index, name in enumerate(_PROVIDER_TYPE_ORDER)}
        rows.sort(
            key=lambda item: (
                order.get(item.provider_type, 99),
                item.updated_at,
            )
        )
        active = self._registry.active_id()
        return [
            build_provider_view(row, is_active=row.provider_id == active)
            for row in rows
        ]

    def create(
        self,
        *,
        provider_type: str,
        display_name: str | None = None,
        status: str = "not_configured",
        configuration: dict[str, Any] | None = None,
    ) -> AIProviderView:
        existing = self._store.list_all()
        if any(row.provider_type == provider_type for row in existing):
            raise AIProviderError("provider_type_already_exists")
        row = new_ai_provider(
            provider_type=provider_type,
            display_name=display_name,
            status=status,
            configuration=configuration,
        )
        self._store.save(row)
        if row.status == "enabled":
            self._registry.set_active(row.provider_id)
        return build_provider_view(
            row, is_active=self._registry.active_id() == row.provider_id
        )

    def update(
        self,
        *,
        provider_id: str,
        display_name: str | None = None,
        status: str | None = None,
        configuration: dict[str, Any] | None = None,
    ) -> AIProviderView:
        current = self._store.get(provider_id)
        if current is None:
            raise AIProviderError("provider_not_found")
        updated = apply_provider_update(
            current,
            display_name=display_name,
            status=status,
            configuration=configuration,
        )
        self._store.save(updated)
        if updated.status == "enabled":
            self._registry.set_active(updated.provider_id)
        elif self._registry.active_id() == updated.provider_id:
            self._registry.set_active(None)
        return build_provider_view(
            updated, is_active=self._registry.active_id() == updated.provider_id
        )

    def delete(self, *, provider_id: str) -> None:
        current = self._store.get(provider_id)
        if current is None:
            raise AIProviderError("provider_not_found")
        self._store.delete(provider_id)
        if self._registry.active_id() == provider_id:
            self._registry.set_active(None)

    def health(self, *, provider_id: str) -> AIProviderHealth:
        row = self._store.get(provider_id)
        if row is None:
            raise AIProviderError("provider_not_found")
        runtime = self._registry.bind(row)
        return runtime.health()

    def active_protocol(self) -> AIProviderProtocol | None:
        return self._registry.resolve_active(self._store.list_all())

    def generate(self, context: ConversationContext) -> AIGenerationResult:
        """Engine gateway: Prompt & Policy → Protocol.generate(PromptPackage)."""
        runtime = self.active_protocol()
        package = self._prompts.build(context)
        if runtime is None:
            return AIGenerationResult(
                text=STUB_UNAVAILABLE_REPLY,
                provider_type="none",
                prepared={
                    "ready": False,
                    "conversation_id": context.conversation_id,
                    "prompt_package": package.as_dict(),
                },
            )
        prepared = runtime.prepare(context)
        result = runtime.generate(package)
        merged = dict(result.prepared)
        merged["prepare"] = prepared
        merged["prompt_package_id"] = package.package_id
        return AIGenerationResult(
            text=result.text,
            provider_type=result.provider_type,
            prepared=merged,
        )

    def seed_default_stubs(self) -> None:
        """Ensure openai/anthropic/ollama stubs exist (idempotent)."""
        existing = {row.provider_type for row in self._store.list_all()}
        for provider_type in ("openai", "anthropic", "ollama"):
            if provider_type in existing:
                continue
            self.create(
                provider_type=provider_type,
                status="configured",
                configuration={"model_name": "stub"},
            )
