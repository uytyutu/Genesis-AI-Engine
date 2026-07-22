"""PT4 — Business Action audit log (operator intent · never auto-execute)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "business_action_domain_v1"

ActionType = Literal[
    "send_message",
    "create_knowledge",
    "create_follow_up_task",
    "escalate_conversation",
]

ActionStatus = Literal["executed", "rejected"]

ALLOWED_ACTION_TYPES: frozenset[str] = frozenset(
    {
        "send_message",
        "create_knowledge",
        "create_follow_up_task",
        "escalate_conversation",
    }
)


class BusinessActionError(ValueError):
    """Invalid Business Action operation."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class BusinessAction:
    action_id: str
    account_id: str
    conversation_id: str | None
    action_type: ActionType
    status: ActionStatus
    payload: dict[str, Any]
    result: dict[str, Any]
    approved: bool
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "account_id": self.account_id,
            "conversation_id": self.conversation_id,
            "action_type": self.action_type,
            "status": self.status,
            "payload": dict(self.payload),
            "result": dict(self.result),
            "approved": self.approved,
            "created_at": self.created_at,
        }


def new_business_action(
    *,
    account_id: str,
    action_type: str,
    approved: bool,
    conversation_id: str | None = None,
    payload: dict[str, Any] | None = None,
    result: dict[str, Any] | None = None,
    status: str = "executed",
) -> BusinessAction:
    if not account_id.strip():
        raise BusinessActionError("account_required")
    if action_type not in ALLOWED_ACTION_TYPES:
        raise BusinessActionError("unknown_action_type")
    if not approved:
        raise BusinessActionError("approval_required")
    if status not in {"executed", "rejected"}:
        raise BusinessActionError("unknown_status")
    return BusinessAction(
        action_id=str(uuid4()),
        account_id=account_id,
        conversation_id=conversation_id,
        action_type=action_type,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        payload=dict(payload or {}),
        result=dict(result or {}),
        approved=True,
        created_at=_utc_now_iso(),
    )
