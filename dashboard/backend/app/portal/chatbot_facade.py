"""R5.4 — ChatBotFacade (reference integration ModuleFacade).

```text
Authorization (caller)
    ↓
ChatBotFacade
    ↓
ChatBot Domain + Store
    ↓
ChatBotIntegrationAdapter  (stub today · provider later)
```

Sole application entry for ChatBot integration config.
Does not authenticate · authorize · know cookies · Session · Ownership.
Does not call OpenAI or store API keys.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.chatbot import (
    ChatBotConnectionUpdate,
    ChatBotError,
    apply_chatbot_connection_update,
    empty_chatbot_connection,
)
from app.portal.chatbot_integration_adapter import ChatBotIntegrationAdapter
from app.portal.chatbot_store import ChatBotStore
from app.portal.chatbot_view import ChatBotView, build_chatbot_view

ENGINE_ID = "chatbot_facade_v1"


@dataclass(frozen=True)
class ChatBotFacade:
    """Integration ModuleFacade — provider stays behind the adapter."""

    _store: ChatBotStore
    _adapter: ChatBotIntegrationAdapter

    @classmethod
    def from_parts(
        cls,
        store: ChatBotStore,
        adapter: ChatBotIntegrationAdapter,
    ) -> ChatBotFacade:
        return cls(_store=store, _adapter=adapter)

    def get_chatbot(self, website_id: str) -> ChatBotView:
        row = self._store.get(website_id)
        if row is None:
            row = empty_chatbot_connection(website_id)
        row = self._adapter.reconcile_status(row)
        return build_chatbot_view(row)

    def update_chatbot(
        self,
        website_id: str,
        *,
        enabled: bool,
        provider: str,
        status: str,
        assistant_id: str | None,
    ) -> ChatBotView:
        current = self._store.get(website_id)
        if current is None:
            current = empty_chatbot_connection(website_id)
        update = ChatBotConnectionUpdate(
            enabled=enabled,
            provider=provider,
            status=status,
            assistant_id=assistant_id,
        )
        try:
            next_row = apply_chatbot_connection_update(current, update)
        except ChatBotError:
            raise
        next_row = self._adapter.reconcile_status(next_row)
        self._store.save(next_row)
        return build_chatbot_view(next_row)
