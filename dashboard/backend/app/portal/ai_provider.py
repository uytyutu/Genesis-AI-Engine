"""AI Platform AP1.1 — AIProvider domain (provider registry records).

```text
Provider Layer abstracts LLM implementations.
Provider Layer never prepares business context.
Provider Layer never manages conversations.
Provider Layer never communicates directly with channels.
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "ai_provider_domain_v1"

ProviderType = Literal["openai", "anthropic", "ollama", "custom"]
ProviderStatus = Literal[
    "not_configured",
    "configured",
    "enabled",
    "disabled",
]

ALLOWED_PROVIDER_TYPES: frozenset[str] = frozenset(
    {"openai", "anthropic", "ollama", "custom"}
)
ALLOWED_PROVIDER_STATUSES: frozenset[str] = frozenset(
    {
        "not_configured",
        "configured",
        "enabled",
        "disabled",
    }
)

ALLOWED_CONFIG_KEYS: dict[str, frozenset[str]] = {
    "openai": frozenset({"model_name", "organization_placeholder"}),
    "anthropic": frozenset({"model_name"}),
    "ollama": frozenset({"model_name", "base_url_placeholder"}),
    "custom": frozenset({"label", "notes"}),
}

_FORBIDDEN_CONFIG_FRAGMENTS: tuple[str, ...] = (
    "token",
    "secret",
    "password",
    "api_key",
    "apikey",
    "oauth",
    "access_key",
    "private_key",
)

STUB_GENERATION_REPLY = (
    "Provider configured. Generation is not implemented."
)
STUB_UNAVAILABLE_REPLY = "Provider unavailable."


class AIProviderError(ValueError):
    """Invalid AI Provider operation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _sanitize_configuration(
    provider_type: str, configuration: dict[str, Any] | None
) -> dict[str, str]:
    raw = configuration or {}
    allowed = ALLOWED_CONFIG_KEYS.get(provider_type, frozenset())
    clean: dict[str, str] = {}
    for key, value in raw.items():
        key_l = str(key).strip().lower()
        if key_l not in allowed:
            raise AIProviderError(f"unknown_config_key:{key}")
        if any(frag in key_l for frag in _FORBIDDEN_CONFIG_FRAGMENTS):
            raise AIProviderError("secret_config_forbidden")
        text = str(value).strip()
        if len(text) > 500:
            raise AIProviderError("config_value_too_long")
        clean[key_l] = text
    return clean


def _default_display_name(provider_type: str) -> str:
    return {
        "openai": "OpenAI",
        "anthropic": "Anthropic",
        "ollama": "Ollama",
        "custom": "Custom Provider",
    }.get(provider_type, provider_type)


@dataclass(frozen=True)
class AIProvider:
    """Registered provider descriptor — not an LLM runtime call."""

    provider_id: str
    provider_type: ProviderType
    display_name: str
    status: ProviderStatus
    configuration: dict[str, str]
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["configuration"] = dict(self.configuration)
        return payload


def new_ai_provider(
    *,
    provider_type: str,
    display_name: str | None = None,
    status: str = "not_configured",
    configuration: dict[str, Any] | None = None,
) -> AIProvider:
    if provider_type not in ALLOWED_PROVIDER_TYPES:
        raise AIProviderError("unknown_provider_type")
    if status not in ALLOWED_PROVIDER_STATUSES:
        raise AIProviderError("unknown_status")
    config = _sanitize_configuration(provider_type, configuration)
    if status == "not_configured" and config:
        status = "configured"
    name = (display_name or "").strip() or _default_display_name(provider_type)
    now = _utc_now_iso()
    return AIProvider(
        provider_id=str(uuid4()),
        provider_type=provider_type,  # type: ignore[arg-type]
        display_name=name,
        status=status,  # type: ignore[arg-type]
        configuration=config,
        created_at=now,
        updated_at=now,
    )


def apply_provider_update(
    current: AIProvider,
    *,
    display_name: str | None = None,
    status: str | None = None,
    configuration: dict[str, Any] | None = None,
) -> AIProvider:
    next_status = current.status
    if status is not None:
        if status not in ALLOWED_PROVIDER_STATUSES:
            raise AIProviderError("unknown_status")
        next_status = status  # type: ignore[assignment]
    next_config = current.configuration
    if configuration is not None:
        next_config = _sanitize_configuration(current.provider_type, configuration)
        if next_status == "not_configured" and next_config:
            next_status = "configured"  # type: ignore[assignment]
    next_name = current.display_name
    if display_name is not None:
        next_name = display_name.strip() or current.display_name
    return replace(
        current,
        display_name=next_name,
        status=next_status,
        configuration=next_config,
        updated_at=_utc_now_iso(),
    )
