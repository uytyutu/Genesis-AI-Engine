"""PT4 — Business Action views."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.business_action import BusinessAction

ENGINE_ID = "business_action_view_v1"


@dataclass(frozen=True)
class BusinessActionView:
    action_id: str
    conversation_id: str | None
    action_type: str
    status: str
    payload: dict[str, Any]
    result: dict[str, Any]
    approved: bool
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "conversation_id": self.conversation_id,
            "action_type": self.action_type,
            "status": self.status,
            "payload": dict(self.payload),
            "result": dict(self.result),
            "approved": self.approved,
            "created_at": self.created_at,
        }


def build_action_view(row: BusinessAction) -> BusinessActionView:
    return BusinessActionView(
        action_id=row.action_id,
        conversation_id=row.conversation_id,
        action_type=row.action_type,
        status=row.status,
        payload=dict(row.payload),
        result=dict(row.result),
        approved=row.approved,
        created_at=row.created_at,
    )
