"""Business Product BP1.4 — ConversationStore + MessageStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.conversation import Conversation, Message

ENGINE_ID = "conversation_store_v1"


class ConversationStore(Protocol):
    def save(self, row: Conversation) -> None: ...

    def get(self, conversation_id: str) -> Conversation | None: ...

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[Conversation, ...]: ...


class MessageStore(Protocol):
    def save(self, row: Message) -> None: ...

    def list_for_conversation(
        self, conversation_id: str
    ) -> tuple[Message, ...]: ...


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._rows: dict[str, Conversation] = {}

    def save(self, row: Conversation) -> None:
        self._rows[row.conversation_id] = row

    def get(self, conversation_id: str) -> Conversation | None:
        return self._rows.get(conversation_id)

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[Conversation, ...]:
        return tuple(
            row for row in self._rows.values() if row.profile_id == profile_id
        )


class InMemoryMessageStore:
    def __init__(self) -> None:
        self._rows: dict[str, Message] = {}

    def save(self, row: Message) -> None:
        self._rows[row.message_id] = row

    def list_for_conversation(
        self, conversation_id: str
    ) -> tuple[Message, ...]:
        rows = [
            row
            for row in self._rows.values()
            if row.conversation_id == conversation_id
        ]
        rows.sort(key=lambda item: item.created_at)
        return tuple(rows)
