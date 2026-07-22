"""R5.4 — ChatBot Integration Adapter (Integration Boundary).

```text
ChatBotFacade
    ↓
ChatBot Domain
    ↓
ChatBotIntegrationAdapter   ← provider stays behind this line
    ↓
Provider (future)
```

Today: ``StubChatBotIntegrationAdapter`` — no network, no API keys.
Future: OpenAI / local adapters implement the same Protocol.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Protocol

from app.portal.chatbot import ChatBotConnection, ChatBotStatus

ENGINE_ID = "chatbot_integration_adapter_v1"


class ChatBotIntegrationAdapter(Protocol):
    """Sole place that may eventually talk to an external ChatBot provider."""

    def reconcile_status(self, connection: ChatBotConnection) -> ChatBotConnection:
        """Return connection with provider-aware status. Must not leak provider SDKs upward."""
        ...


class StubChatBotIntegrationAdapter:
    """No OpenAI / HTTP. Derives status from local config only."""

    def reconcile_status(self, connection: ChatBotConnection) -> ChatBotConnection:
        status: ChatBotStatus
        if not connection.enabled or connection.provider == "none":
            status = "disconnected"
        elif not connection.assistant_id:
            status = "pending"
        else:
            status = "connected"
        if status == connection.status:
            return connection
        return replace(connection, status=status)
