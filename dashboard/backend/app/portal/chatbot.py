"""R5.4 — ChatBot Domain (integration connection config).

Reference **integration** Portal module. Answers: how is ChatBot
configured for this Website?

```text
ChatBotConnection
  enabled · provider · status · assistant_id
```

Does not authenticate · authorize · know Session · Ownership · HTTP.
No OpenAI calls · API keys · chat history · RAG · streaming · tools.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "chatbot_domain_v1"

_MAX_ASSISTANT_ID = 200

ChatBotProvider = Literal["none", "openai", "local"]
ChatBotStatus = Literal["disconnected", "pending", "connected", "error"]

ALLOWED_PROVIDERS: frozenset[str] = frozenset({"none", "openai", "local"})
ALLOWED_STATUSES: frozenset[str] = frozenset(
    {"disconnected", "pending", "connected", "error"}
)


class ChatBotError(ValueError):
    """Invalid ChatBot connection config."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class ChatBotConnection:
    """Website↔ChatBot integration config — not a chat runtime."""

    connection_id: str
    website_id: str
    enabled: bool
    provider: ChatBotProvider
    status: ChatBotStatus
    assistant_id: str | None
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ChatBotConnectionUpdate:
    """Intent to set integration config fields."""

    enabled: bool
    provider: str
    status: str
    assistant_id: str | None

    def as_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "provider": self.provider,
            "status": self.status,
            "assistant_id": self.assistant_id,
        }


def empty_chatbot_connection(website_id: str) -> ChatBotConnection:
    now = _utc_now_iso()
    return ChatBotConnection(
        connection_id=str(uuid4()),
        website_id=website_id,
        enabled=False,
        provider="none",
        status="disconnected",
        assistant_id=None,
        created_at=now,
        updated_at=now,
    )


def apply_chatbot_connection_update(
    current: ChatBotConnection,
    update: ChatBotConnectionUpdate,
) -> ChatBotConnection:
    """Validate config. Domain-only — no provider network calls."""
    provider = str(update.provider).strip().lower()
    status = str(update.status).strip().lower()
    if provider not in ALLOWED_PROVIDERS:
        raise ChatBotError("provider_invalid")
    if status not in ALLOWED_STATUSES:
        raise ChatBotError("status_invalid")

    assistant_id = update.assistant_id
    if assistant_id is not None:
        assistant_id = str(assistant_id).strip() or None
    if assistant_id is not None and len(assistant_id) > _MAX_ASSISTANT_ID:
        raise ChatBotError("assistant_id_too_long")

    enabled = bool(update.enabled)
    if not enabled or provider == "none":
        # Local consistency before adapter reconcile.
        status = "disconnected"
        if provider == "none":
            assistant_id = None

    return ChatBotConnection(
        connection_id=current.connection_id,
        website_id=current.website_id,
        enabled=enabled,
        provider=provider,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        assistant_id=assistant_id,
        created_at=current.created_at,
        updated_at=_utc_now_iso(),
    )
