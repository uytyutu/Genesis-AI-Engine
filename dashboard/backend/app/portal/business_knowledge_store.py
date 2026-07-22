"""Business Product BP1.2 — BusinessKnowledgeStore."""

from __future__ import annotations

from typing import Protocol

from app.portal.business_knowledge import BusinessKnowledge

ENGINE_ID = "business_knowledge_store_v1"


class BusinessKnowledgeStore(Protocol):
    def save(self, row: BusinessKnowledge) -> None: ...

    def get(self, knowledge_id: str) -> BusinessKnowledge | None: ...

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[BusinessKnowledge, ...]: ...

    def delete(self, knowledge_id: str) -> bool: ...


class InMemoryBusinessKnowledgeStore:
    def __init__(self) -> None:
        self._rows: dict[str, BusinessKnowledge] = {}

    def save(self, row: BusinessKnowledge) -> None:
        self._rows[row.knowledge_id] = row

    def get(self, knowledge_id: str) -> BusinessKnowledge | None:
        return self._rows.get(knowledge_id)

    def list_for_profile(
        self, profile_id: str
    ) -> tuple[BusinessKnowledge, ...]:
        return tuple(
            row for row in self._rows.values() if row.profile_id == profile_id
        )

    def delete(self, knowledge_id: str) -> bool:
        if knowledge_id not in self._rows:
            return False
        del self._rows[knowledge_id]
        return True
