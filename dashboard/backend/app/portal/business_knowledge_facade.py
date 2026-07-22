"""Business Product BP1.2 — BusinessKnowledgeFacade."""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.business_knowledge import BusinessKnowledgeError
from app.portal.business_knowledge_service import BusinessKnowledgeService
from app.portal.business_knowledge_store import (
    BusinessKnowledgeStore,
    InMemoryBusinessKnowledgeStore,
)
from app.portal.business_knowledge_view import BusinessKnowledgeView
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore

ENGINE_ID = "business_knowledge_facade_v1"


@dataclass(frozen=True)
class BusinessKnowledgeFacade:
    _service: BusinessKnowledgeService

    @classmethod
    def from_parts(
        cls,
        *,
        profiles: ChatBotBusinessProfileStore,
        knowledge: BusinessKnowledgeStore | None = None,
    ) -> BusinessKnowledgeFacade:
        return cls(
            _service=BusinessKnowledgeService(
                knowledge=knowledge
                if knowledge is not None
                else InMemoryBusinessKnowledgeStore(),
                profiles=profiles,
            )
        )

    def list_knowledge(
        self, *, account_id: str, category: str | None = None
    ) -> list[BusinessKnowledgeView]:
        try:
            return self._service.list_for_account(
                account_id=account_id, category=category
            )
        except BusinessKnowledgeError:
            raise

    def create_knowledge(
        self,
        *,
        account_id: str,
        category: str,
        title: str,
        content: str,
    ) -> BusinessKnowledgeView:
        try:
            return self._service.create(
                account_id=account_id,
                category=category,
                title=title,
                content=content,
            )
        except BusinessKnowledgeError:
            raise

    def update_knowledge(
        self,
        *,
        account_id: str,
        knowledge_id: str,
        category: str | None = None,
        title: str | None = None,
        content: str | None = None,
    ) -> BusinessKnowledgeView:
        try:
            return self._service.update(
                account_id=account_id,
                knowledge_id=knowledge_id,
                category=category,
                title=title,
                content=content,
            )
        except BusinessKnowledgeError:
            raise

    def delete_knowledge(self, *, account_id: str, knowledge_id: str) -> None:
        try:
            self._service.delete(account_id=account_id, knowledge_id=knowledge_id)
        except BusinessKnowledgeError:
            raise
