"""AI Platform AP1.1 — AIProviderProtocol (LLM abstraction contract).

Conversation Engine knows only this Protocol — never concrete SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable

from app.portal.conversation import ConversationContext

ENGINE_ID = "ai_provider_protocol_v1"


@dataclass(frozen=True)
class AIProviderInfo:
    provider_id: str
    provider_type: str
    display_name: str
    status: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "display_name": self.display_name,
            "status": self.status,
        }


@dataclass(frozen=True)
class AIProviderHealth:
    ok: bool
    status: str
    detail: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "status": self.status,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class AIGenerationResult:
    """Stub-era generation result — text only, no streaming/tools."""

    text: str
    provider_type: str
    prepared: dict[str, Any]

    def as_dict(self) -> dict[str, Any]:
        return {
            "text": self.text,
            "provider_type": self.provider_type,
            "prepared": dict(self.prepared),
        }


@runtime_checkable
class AIProviderProtocol(Protocol):
    """Platform contract for any LLM backend."""

    def prepare(self, context: ConversationContext) -> dict[str, Any]:
        """Validate/accept ConversationContext — does not build business context."""
        ...

    def generate(self, context: ConversationContext) -> AIGenerationResult:
        """Produce a reply from context — stubs never call external APIs."""
        ...

    def health(self) -> AIProviderHealth:
        ...

    def provider_info(self) -> AIProviderInfo:
        ...
