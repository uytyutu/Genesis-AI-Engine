"""LLM availability — real API key only (no dev mock)."""

from __future__ import annotations

from app.integration.llm_chat_provider import LlmChatProvider


class LlmRuntime:
    def __init__(self) -> None:
        self._provider = LlmChatProvider()

    @property
    def active(self) -> bool:
        return self._provider.available()

    @property
    def provider(self) -> LlmChatProvider:
        return self._provider
