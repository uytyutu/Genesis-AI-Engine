"""AI Platform AP1.1 — AIProviderStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.ai_provider import AIProvider

ENGINE_ID = "ai_provider_store_v1"


class AIProviderStore(Protocol):
    def save(self, row: AIProvider) -> None: ...

    def get(self, provider_id: str) -> AIProvider | None: ...

    def list_all(self) -> tuple[AIProvider, ...]: ...

    def delete(self, provider_id: str) -> bool: ...


class InMemoryAIProviderStore:
    def __init__(self) -> None:
        self._rows: dict[str, AIProvider] = {}

    def save(self, row: AIProvider) -> None:
        self._rows[row.provider_id] = row

    def get(self, provider_id: str) -> AIProvider | None:
        return self._rows.get(provider_id)

    def list_all(self) -> tuple[AIProvider, ...]:
        return tuple(self._rows.values())

    def delete(self, provider_id: str) -> bool:
        if provider_id not in self._rows:
            return False
        del self._rows[provider_id]
        return True
