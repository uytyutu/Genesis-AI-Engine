"""Business Product BP1.2 — BusinessKnowledge domain.

Answers only: what should the digital employee know about the company?

```text
Business Knowledge stores facts.
Business Knowledge never generates answers.
Business Knowledge never communicates with customers.
```
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "business_knowledge_domain_v1"

KnowledgeCategory = Literal[
    "company",
    "services",
    "products",
    "pricing",
    "working_hours",
    "faq",
    "policies",
    "contacts",
]

ALLOWED_KNOWLEDGE_CATEGORIES: frozenset[str] = frozenset(
    {
        "company",
        "services",
        "products",
        "pricing",
        "working_hours",
        "faq",
        "policies",
        "contacts",
    }
)

KNOWLEDGE_CATEGORY_ORDER: tuple[str, ...] = (
    "company",
    "services",
    "products",
    "pricing",
    "working_hours",
    "faq",
    "policies",
    "contacts",
)


class BusinessKnowledgeError(ValueError):
    """Invalid Business Knowledge operation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class BusinessKnowledge:
    """One structured fact about the business — not an answer generator."""

    knowledge_id: str
    profile_id: str
    category: KnowledgeCategory
    title: str
    content: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_business_knowledge(
    *,
    profile_id: str,
    category: str,
    title: str,
    content: str,
) -> BusinessKnowledge:
    if category not in ALLOWED_KNOWLEDGE_CATEGORIES:
        raise BusinessKnowledgeError("unknown_category")
    clean_title = title.strip()
    clean_content = content.strip()
    if not clean_title:
        raise BusinessKnowledgeError("title_required")
    if not clean_content:
        raise BusinessKnowledgeError("content_required")
    if not profile_id.strip():
        raise BusinessKnowledgeError("profile_required")
    now = _utc_now_iso()
    return BusinessKnowledge(
        knowledge_id=str(uuid4()),
        profile_id=profile_id,
        category=category,  # type: ignore[arg-type]
        title=clean_title,
        content=clean_content,
        created_at=now,
        updated_at=now,
    )


def apply_knowledge_update(
    current: BusinessKnowledge,
    *,
    category: str | None = None,
    title: str | None = None,
    content: str | None = None,
) -> BusinessKnowledge:
    next_category = current.category
    if category is not None:
        if category not in ALLOWED_KNOWLEDGE_CATEGORIES:
            raise BusinessKnowledgeError("unknown_category")
        next_category = category  # type: ignore[assignment]
    next_title = current.title
    if title is not None:
        next_title = title.strip()
        if not next_title:
            raise BusinessKnowledgeError("title_required")
    next_content = current.content
    if content is not None:
        next_content = content.strip()
        if not next_content:
            raise BusinessKnowledgeError("content_required")
    return replace(
        current,
        category=next_category,
        title=next_title,
        content=next_content,
        updated_at=_utc_now_iso(),
    )
