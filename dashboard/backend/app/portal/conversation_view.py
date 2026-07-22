"""Business Product BP1.4 — Conversation views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.conversation import Conversation, ConversationContext, Message

ENGINE_ID = "conversation_view_v1"


@dataclass(frozen=True)
class MessageView:
    message_id: str
    conversation_id: str
    role: str
    content: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "message_id": self.message_id,
            "conversation_id": self.conversation_id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class ConversationView:
    conversation_id: str
    profile_id: str
    channel_connection_id: str | None
    status: str
    created_at: str
    updated_at: str
    messages: list[MessageView] | None = None

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "conversation_id": self.conversation_id,
            "profile_id": self.profile_id,
            "channel_connection_id": self.channel_connection_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.messages is not None:
            payload["messages"] = [item.as_dict() for item in self.messages]
        return payload


@dataclass(frozen=True)
class ConversationTurnView:
    """Result of posting a user message — context prepared + stub reply."""

    conversation: ConversationView
    user_message: MessageView
    assistant_message: MessageView
    context: dict[str, Any]
    stub_response: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation": self.conversation.as_dict(),
            "user_message": self.user_message.as_dict(),
            "assistant_message": self.assistant_message.as_dict(),
            "context": dict(self.context),
            "stub_response": self.stub_response,
        }


def build_message_view(row: Message) -> MessageView:
    return MessageView(
        message_id=row.message_id,
        conversation_id=row.conversation_id,
        role=row.role,
        content=row.content,
        created_at=row.created_at,
    )


def build_conversation_view(
    row: Conversation, *, messages: tuple[Message, ...] | None = None
) -> ConversationView:
    return ConversationView(
        conversation_id=row.conversation_id,
        profile_id=row.profile_id,
        channel_connection_id=row.channel_connection_id,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        messages=(
            [build_message_view(item) for item in messages]
            if messages is not None
            else None
        ),
    )


def context_as_dict(context: ConversationContext) -> dict[str, Any]:
    return context.as_dict()
