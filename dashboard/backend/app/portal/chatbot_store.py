"""R5.4 — ChatBotStore (temporary in-memory adapter).

``ChatBotStore`` is the abstraction; ``InMemoryChatBotStore`` is today's
adapter. Durable store plugs in without changing the Facade.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.chatbot import ChatBotConnection

ENGINE_ID = "chatbot_store_v1"


class ChatBotStore(Protocol):
    def get(self, website_id: str) -> ChatBotConnection | None: ...

    def save(self, connection: ChatBotConnection) -> None: ...


class InMemoryChatBotStore:
    """Process-local connection map — replace with durable store later."""

    def __init__(self) -> None:
        self._rows: dict[str, ChatBotConnection] = {}

    def get(self, website_id: str) -> ChatBotConnection | None:
        return self._rows.get(website_id)

    def save(self, connection: ChatBotConnection) -> None:
        self._rows[connection.website_id] = connection
