"""Business Product BP1.4 — Conversation Engine domain (stub).

Answers only: how Vector accepts a request and prepares it for processing.

```text
Conversation Engine prepares context.
Conversation Engine never generates AI responses.
Conversation Engine never communicates with external providers.
Conversation Engine never depends on external SDKs.
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "conversation_engine_domain_v1"

ConversationStatus = Literal["open", "prepared", "closed"]
MessageRole = Literal["user", "assistant", "system"]

ALLOWED_CONVERSATION_STATUSES: frozenset[str] = frozenset(
    {"open", "prepared", "closed"}
)
ALLOWED_MESSAGE_ROLES: frozenset[str] = frozenset({"user", "assistant", "system"})

# Simple fixed-category pick (no retrieval model).
DEFAULT_KNOWLEDGE_CATEGORIES: tuple[str, ...] = (
    "company",
    "services",
    "faq",
    "contacts",
)

STUB_ASSISTANT_REPLY = (
    "Conversation prepared successfully. AI provider is not connected."
)


class ConversationError(ValueError):
    """Invalid Conversation Engine operation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Conversation:
    conversation_id: str
    profile_id: str
    channel_connection_id: str | None
    status: ConversationStatus
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Message:
    message_id: str
    conversation_id: str
    role: MessageRole
    content: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ConversationContext:
    """Prepared packet for a future AI Provider — not an LLM call."""

    conversation_id: str
    profile_id: str
    business: dict[str, Any]
    industry_template: dict[str, Any] | None
    knowledge: tuple[dict[str, Any], ...]
    selected_categories: tuple[str, ...]
    messages: tuple[dict[str, Any], ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "profile_id": self.profile_id,
            "business": dict(self.business),
            "industry_template": (
                dict(self.industry_template)
                if self.industry_template is not None
                else None
            ),
            "knowledge": [dict(item) for item in self.knowledge],
            "selected_categories": list(self.selected_categories),
            "messages": [dict(item) for item in self.messages],
            "metadata": dict(self.metadata),
        }


def new_conversation(
    *,
    profile_id: str,
    channel_connection_id: str | None = None,
) -> Conversation:
    if not profile_id.strip():
        raise ConversationError("profile_required")
    now = _utc_now_iso()
    return Conversation(
        conversation_id=str(uuid4()),
        profile_id=profile_id,
        channel_connection_id=channel_connection_id,
        status="open",
        created_at=now,
        updated_at=now,
    )


def mark_conversation_prepared(row: Conversation) -> Conversation:
    return replace(row, status="prepared", updated_at=_utc_now_iso())


def set_conversation_status(row: Conversation, *, status: str) -> Conversation:
    """Lifecycle transition for Operations Workspace — not AI / not channels."""
    if status not in ALLOWED_CONVERSATION_STATUSES:
        raise ConversationError("unknown_status")
    if status == row.status:
        return row
    return replace(row, status=status, updated_at=_utc_now_iso())  # type: ignore[arg-type]


def new_message(
    *,
    conversation_id: str,
    role: str,
    content: str,
) -> Message:
    if role not in ALLOWED_MESSAGE_ROLES:
        raise ConversationError("unknown_role")
    text = content.strip()
    if not text:
        raise ConversationError("content_required")
    if len(text) > 8000:
        raise ConversationError("content_too_long")
    return Message(
        message_id=str(uuid4()),
        conversation_id=conversation_id,
        role=role,  # type: ignore[arg-type]
        content=text,
        created_at=_utc_now_iso(),
    )
