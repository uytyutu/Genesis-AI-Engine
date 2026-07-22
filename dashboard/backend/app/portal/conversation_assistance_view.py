"""PT3 — Conversation Assistance results (operator augment, never auto-send)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class AssistanceDraftView:
    conversation_id: str
    draft_text: str
    provider_type: str
    prompt_package_id: str | None
    policy_language: str | None
    auto_sent: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "draft_text": self.draft_text,
            "provider_type": self.provider_type,
            "prompt_package_id": self.prompt_package_id,
            "policy_language": self.policy_language,
            "auto_sent": self.auto_sent,
        }


@dataclass(frozen=True)
class AssistanceSummaryView:
    conversation_id: str
    summary_text: str
    provider_type: str
    prompt_package_id: str | None
    auto_sent: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "summary_text": self.summary_text,
            "provider_type": self.provider_type,
            "prompt_package_id": self.prompt_package_id,
            "auto_sent": self.auto_sent,
        }


@dataclass(frozen=True)
class AssistanceReviewView:
    """Operator review panel — mix of heuristics + optional AI fields."""

    conversation_id: str
    priority: str
    suggested_tags: list[str]
    suggested_knowledge: list[dict[str, str]]
    insights: list[str]
    draft_available: bool
    summary_available: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "priority": self.priority,
            "suggested_tags": list(self.suggested_tags),
            "suggested_knowledge": [dict(item) for item in self.suggested_knowledge],
            "insights": list(self.insights),
            "draft_available": self.draft_available,
            "summary_available": self.summary_available,
            "auto_sent": False,
        }
