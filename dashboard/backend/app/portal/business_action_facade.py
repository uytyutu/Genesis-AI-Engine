"""PT4 — BusinessActionFacade."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.business_action import BusinessActionError
from app.portal.business_action_service import BusinessActionService
from app.portal.business_action_store import (
    BusinessActionStore,
    InMemoryBusinessActionStore,
)
from app.portal.business_action_view import BusinessActionView
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.conversation_facade import ConversationFacade

ENGINE_ID = "business_action_facade_v1"


@dataclass(frozen=True)
class BusinessActionFacade:
    _service: BusinessActionService

    @classmethod
    def from_parts(
        cls,
        *,
        conversations: ConversationFacade,
        knowledge: BusinessKnowledgeFacade,
        store: BusinessActionStore | None = None,
    ) -> BusinessActionFacade:
        return cls(
            _service=BusinessActionService(
                store=store if store is not None else InMemoryBusinessActionStore(),
                conversations=conversations,
                knowledge=knowledge,
            )
        )

    def list_actions(
        self, *, account_id: str, conversation_id: str | None = None
    ) -> list[BusinessActionView]:
        return self._service.list_actions(
            account_id=account_id, conversation_id=conversation_id
        )

    def execute(
        self,
        *,
        account_id: str,
        action_type: str,
        approved: bool,
        conversation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BusinessActionView:
        try:
            return self._service.execute(
                account_id=account_id,
                action_type=action_type,
                approved=approved,
                conversation_id=conversation_id,
                payload=payload,
            )
        except BusinessActionError:
            raise
