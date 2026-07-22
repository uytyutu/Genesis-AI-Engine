"""Business Product BP1.2 — Business Knowledge View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.business_knowledge import BusinessKnowledge

ENGINE_ID = "business_knowledge_view_v1"


@dataclass(frozen=True)
class BusinessKnowledgeView:
    knowledge_id: str
    profile_id: str
    category: str
    title: str
    content: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "knowledge_id": self.knowledge_id,
            "profile_id": self.profile_id,
            "category": self.category,
            "title": self.title,
            "content": self.content,
            "updated_at": self.updated_at,
        }


def build_knowledge_view(row: BusinessKnowledge) -> BusinessKnowledgeView:
    return BusinessKnowledgeView(
        knowledge_id=row.knowledge_id,
        profile_id=row.profile_id,
        category=row.category,
        title=row.title,
        content=row.content,
        updated_at=row.updated_at,
    )
