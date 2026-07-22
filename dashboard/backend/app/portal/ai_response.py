"""AI Platform AP1.2 — Unified AIResponse + provider error taxonomy.

Adapters map vendor failures into these types; SDK exceptions never escape.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
from uuid import uuid4

ENGINE_ID = "ai_response_v1"


@dataclass(frozen=True)
class AIResponse:
    """Unified generation payload returned by Provider Adapters."""

    response_id: str
    provider: str
    model: str
    content: str
    usage: dict[str, Any]
    finish_reason: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "response_id": self.response_id,
            "provider": self.provider,
            "model": self.model,
            "content": self.content,
            "usage": dict(self.usage),
            "finish_reason": self.finish_reason,
            "metadata": dict(self.metadata),
        }


def new_ai_response(
    *,
    provider: str,
    model: str,
    content: str,
    usage: dict[str, Any] | None = None,
    finish_reason: str = "stop",
    metadata: dict[str, Any] | None = None,
) -> AIResponse:
    return AIResponse(
        response_id=str(uuid4()),
        provider=provider,
        model=model,
        content=content,
        usage=dict(usage or {}),
        finish_reason=finish_reason,
        metadata=dict(metadata or {}),
    )


class ProviderPlatformError(Exception):
    """Base unified provider error — never an SDK type."""

    code: str = "provider_error"

    def __init__(self, message: str = "") -> None:
        super().__init__(message or self.code)
        self.message = message or self.code


class ProviderUnavailable(ProviderPlatformError):
    code = "provider_unavailable"


class AuthenticationFailed(ProviderPlatformError):
    code = "authentication_failed"


class RateLimited(ProviderPlatformError):
    code = "rate_limited"


class InvalidConfiguration(ProviderPlatformError):
    code = "invalid_configuration"


class GenerationFailed(ProviderPlatformError):
    code = "generation_failed"


def ai_response_from_error(
    *,
    provider: str,
    model: str,
    error: ProviderPlatformError,
) -> AIResponse:
    return new_ai_response(
        provider=provider,
        model=model,
        content=f"{error.code}: {error.message}",
        usage={},
        finish_reason="error",
        metadata={"error_code": error.code, "error_message": error.message},
    )
