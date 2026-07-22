"""AI Platform AP1.1 — AIProviderManager (lifecycle + Protocol gateway)."""

from __future__ import annotations

import time
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
from app.portal.operational_context import ensure_request_id
from app.portal.operational_log import emit_ops_event
from app.portal.operational_metrics import get_operational_metrics
from app.portal.prompt_facade import PromptFacade
from app.portal.provider_resilience import (
    generate_resilient,
    is_provider_failure,
    operator_safe_failure,
)

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
        request_id = ensure_request_id(
            str(context.metadata.get("request_id") or "") or None
        )
        meta = dict(context.metadata)
        meta["request_id"] = request_id
        context = ConversationContext(
            conversation_id=context.conversation_id,
            profile_id=context.profile_id,
            business=context.business,
            industry_template=context.industry_template,
            knowledge=context.knowledge,
            selected_categories=context.selected_categories,
            messages=context.messages,
            metadata=meta,
        )
        started = time.perf_counter()
        runtime = self.active_protocol()
        package = self._prompts.build(context)
        if runtime is None:
            result = operator_safe_failure(
                provider_type="none",
                prepared={
                    "ready": False,
                    "conversation_id": context.conversation_id,
                    "prompt_package": package.as_dict(),
                    "request_id": request_id,
                    "legacy_stub": STUB_UNAVAILABLE_REPLY,
                },
            )
            duration_ms = (time.perf_counter() - started) * 1000.0
            get_operational_metrics().record_ai_latency(duration_ms)
            get_operational_metrics().record_provider_failure()
            emit_ops_event(
                operation="ai_generate",
                status="error",
                level="warning",
                conversation_id=context.conversation_id,
                provider="none",
                duration_ms=duration_ms,
                error="provider_unavailable",
            )
            return result

        def _once() -> AIGenerationResult:
            prepared = runtime.prepare(context)
            raw = runtime.generate(package)
            merged = dict(raw.prepared)
            merged["prepare"] = prepared
            merged["prompt_package_id"] = package.package_id
            merged["request_id"] = request_id
            return AIGenerationResult(
                text=raw.text,
                provider_type=raw.provider_type,
                prepared=merged,
            )

        result = generate_resilient(_once)
        duration_ms = (time.perf_counter() - started) * 1000.0
        get_operational_metrics().record_ai_latency(duration_ms)
        failed = is_provider_failure(result)
        if failed:
            get_operational_metrics().record_provider_failure()
        emit_ops_event(
            operation="ai_generate",
            status="error" if failed else "ok",
            level="warning" if failed else "info",
            conversation_id=context.conversation_id,
            provider=result.provider_type,
            duration_ms=duration_ms,
            error="provider_unavailable" if failed else None,
            prompt_package_id=package.package_id,
        )
        return result

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
