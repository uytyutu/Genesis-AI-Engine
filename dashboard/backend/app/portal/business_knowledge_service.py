"""Business Product BP1.2 — BusinessKnowledgeService.

Stores facts only. Never generates answers · never talks to customers.
"""

from __future__ import annotations

from app.portal.business_knowledge import (
    BusinessKnowledgeError,
    KNOWLEDGE_CATEGORY_ORDER,
    apply_knowledge_update,
    new_business_knowledge,
)
from app.portal.business_knowledge_store import BusinessKnowledgeStore
from app.portal.business_knowledge_view import (
    BusinessKnowledgeView,
    build_knowledge_view,
)
from app.portal.chatbot_business_profile_store import ChatBotBusinessProfileStore

ENGINE_ID = "business_knowledge_service_v1"


class BusinessKnowledgeService:
    def __init__(
        self,
        *,
        knowledge: BusinessKnowledgeStore,
        profiles: ChatBotBusinessProfileStore,
    ) -> None:
        self._knowledge = knowledge
        self._profiles = profiles

    def _require_profile_id(self, account_id: str) -> str:
        profile = self._profiles.get_for_account(account_id)
        if profile is None:
            raise BusinessKnowledgeError("profile_required")
        return profile.profile_id

    def list_for_account(
        self, *, account_id: str, category: str | None = None
    ) -> list[BusinessKnowledgeView]:
        profile_id = self._require_profile_id(account_id)
        rows = list(self._knowledge.list_for_profile(profile_id))
        if category is not None:
            rows = [row for row in rows if row.category == category]
        order = {name: index for index, name in enumerate(KNOWLEDGE_CATEGORY_ORDER)}
        rows.sort(
            key=lambda item: (
                order.get(item.category, 99),
                item.updated_at,
                item.title,
            )
        )
        return [build_knowledge_view(row) for row in rows]

    def create(
        self,
        *,
        account_id: str,
        category: str,
        title: str,
        content: str,
    ) -> BusinessKnowledgeView:
        profile_id = self._require_profile_id(account_id)
        row = new_business_knowledge(
            profile_id=profile_id,
            category=category,
            title=title,
            content=content,
        )
        self._knowledge.save(row)
        return build_knowledge_view(row)

    def update(
        self,
        *,
        account_id: str,
        knowledge_id: str,
        category: str | None = None,
        title: str | None = None,
        content: str | None = None,
    ) -> BusinessKnowledgeView:
        profile_id = self._require_profile_id(account_id)
        current = self._knowledge.get(knowledge_id)
        if current is None or current.profile_id != profile_id:
            raise BusinessKnowledgeError("knowledge_not_found")
        updated = apply_knowledge_update(
            current, category=category, title=title, content=content
        )
        self._knowledge.save(updated)
        return build_knowledge_view(updated)

    def delete(self, *, account_id: str, knowledge_id: str) -> None:
        profile_id = self._require_profile_id(account_id)
        current = self._knowledge.get(knowledge_id)
        if current is None or current.profile_id != profile_id:
            raise BusinessKnowledgeError("knowledge_not_found")
        self._knowledge.delete(knowledge_id)
