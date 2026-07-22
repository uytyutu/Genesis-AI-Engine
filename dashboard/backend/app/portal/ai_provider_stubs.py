"""AI Platform AP1.1 — Stub providers (kept for compatibility).

AP1.2 routes runtime binding to Provider Adapters via build_stub_runtime.
"""

from __future__ import annotations

from typing import Any

from app.portal.ai_provider import (
    AIProvider,
    STUB_GENERATION_REPLY,
    STUB_UNAVAILABLE_REPLY,
)
from app.portal.ai_provider_adapters import build_adapter_runtime
from app.portal.ai_provider_protocol import (
    AIGenerationResult,
    AIProviderHealth,
    AIProviderInfo,
    AIProviderProtocol,
)
from app.portal.conversation import ConversationContext
from app.portal.prompt_package import PromptPackage

ENGINE_ID = "ai_provider_stubs_v1"


class _BaseStubProvider:
    """Legacy stub shape — unused at runtime after AP1.2 adapters."""

    def __init__(self, record: AIProvider) -> None:
        self._record = record

    def provider_info(self) -> AIProviderInfo:
        return AIProviderInfo(
            provider_id=self._record.provider_id,
            provider_type=self._record.provider_type,
            display_name=self._record.display_name,
            status=self._record.status,
        )

    def health(self) -> AIProviderHealth:
        enabled = self._record.status == "enabled"
        configured = self._record.status in {"configured", "enabled"}
        if enabled:
            return AIProviderHealth(
                ok=True,
                status="enabled",
                detail="Stub provider ready. No external API calls.",
            )
        if configured:
            return AIProviderHealth(
                ok=True,
                status="configured",
                detail="Stub provider configured but not enabled.",
            )
        return AIProviderHealth(
            ok=False,
            status=self._record.status,
            detail=STUB_UNAVAILABLE_REPLY,
        )

    def prepare(self, context: ConversationContext) -> dict[str, Any]:
        return {
            "provider_type": self._record.provider_type,
            "conversation_id": context.conversation_id,
            "profile_id": context.profile_id,
            "message_count": len(context.messages),
            "knowledge_count": len(context.knowledge),
            "selected_categories": list(context.selected_categories),
            "ready": True,
        }

    def generate(self, prompt: PromptPackage) -> AIGenerationResult:
        prepared = {
            "provider_type": self._record.provider_type,
            "conversation_id": prompt.conversation_id,
            "profile_id": prompt.profile_id,
            "prompt_package_id": prompt.package_id,
            "ready": True,
        }
        if self._record.status != "enabled":
            return AIGenerationResult(
                text=STUB_UNAVAILABLE_REPLY,
                provider_type=self._record.provider_type,
                prepared=prepared,
            )
        return AIGenerationResult(
            text=STUB_GENERATION_REPLY,
            provider_type=self._record.provider_type,
            prepared=prepared,
        )


class OpenAIProviderStub(_BaseStubProvider):
    """OpenAI-shaped stub — superseded by OpenAIProviderAdapter."""


class AnthropicProviderStub(_BaseStubProvider):
    """Anthropic-shaped stub — superseded by AnthropicProviderAdapter."""


class OllamaProviderStub(_BaseStubProvider):
    """Ollama-shaped stub — superseded by OllamaProviderAdapter."""


class CustomProviderStub(_BaseStubProvider):
    """Custom-shaped stub for future adapters."""


def build_stub_runtime(record: AIProvider) -> AIProviderProtocol:
    """Registry entrypoint (unchanged import path) → AP1.2 adapters."""
    return build_adapter_runtime(record)
