"""R5.4 — ChatBot View (HTTP/API shape).

Presentation only. No Auth · no domain rules · no provider SDKs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.chatbot import ChatBotConnection

ENGINE_ID = "chatbot_view_v1"


@dataclass(frozen=True)
class ChatBotView:
    website_id: str
    enabled: bool
    provider: str
    status: str
    assistant_id: str | None
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "website_id": self.website_id,
            "enabled": self.enabled,
            "provider": self.provider,
            "status": self.status,
            "assistant_id": self.assistant_id,
            "updated_at": self.updated_at,
        }


def build_chatbot_view(connection: ChatBotConnection) -> ChatBotView:
    return ChatBotView(
        website_id=connection.website_id,
        enabled=connection.enabled,
        provider=connection.provider,
        status=connection.status,
        assistant_id=connection.assistant_id,
        updated_at=connection.updated_at,
    )
