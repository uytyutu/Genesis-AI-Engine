"""PT4 — BusinessActionService (explicit operator approval required)."""

from __future__ import annotations

from typing import Any

from app.portal.business_action import BusinessActionError, new_business_action
from app.portal.business_action_store import BusinessActionStore
from app.portal.business_action_view import BusinessActionView, build_action_view
from app.portal.business_knowledge import BusinessKnowledgeError
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.conversation import ConversationError
from app.portal.conversation_facade import ConversationFacade

ENGINE_ID = "business_action_service_v1"


class BusinessActionService:
    def __init__(
        self,
        *,
        store: BusinessActionStore,
        conversations: ConversationFacade,
        knowledge: BusinessKnowledgeFacade,
    ) -> None:
        self._store = store
        self._conversations = conversations
        self._knowledge = knowledge

    def list_actions(
        self, *, account_id: str, conversation_id: str | None = None
    ) -> list[BusinessActionView]:
        rows = self._store.list_for_account(
            account_id, conversation_id=conversation_id
        )
        return [build_action_view(row) for row in rows]

    def execute(
        self,
        *,
        account_id: str,
        action_type: str,
        approved: bool,
        conversation_id: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> BusinessActionView:
        if not approved:
            raise BusinessActionError("approval_required")
        data = dict(payload or {})
        result: dict[str, Any] = {}

        if action_type == "send_message":
            if not conversation_id:
                raise BusinessActionError("conversation_required")
            content = str(data.get("content") or "").strip()
            if not content:
                raise BusinessActionError("content_required")
            try:
                view = self._conversations.publish_assistant_message(
                    account_id=account_id,
                    conversation_id=conversation_id,
                    content=content,
                )
            except ConversationError as exc:
                raise BusinessActionError(str(exc)) from exc
            result = {
                "conversation_id": view.conversation_id,
                "status": view.status,
                "message_count": len(view.messages or []),
                "note": "Operator-approved assistant message published",
            }

        elif action_type == "create_knowledge":
            category = str(data.get("category") or "faq").strip()
            title = str(data.get("title") or "").strip()
            content = str(data.get("content") or "").strip()
            if not title or not content:
                raise BusinessActionError("knowledge_fields_required")
            try:
                view = self._knowledge.create_knowledge(
                    account_id=account_id,
                    category=category,
                    title=title,
                    content=content,
                )
            except BusinessKnowledgeError as exc:
                raise BusinessActionError(str(exc)) from exc
            result = {
                "knowledge_id": view.knowledge_id,
                "category": view.category,
            }

        elif action_type == "create_follow_up_task":
            title = str(data.get("title") or "Follow up").strip()
            result = {
                "task_id": "stub",
                "title": title,
                "note": "Follow-up task stub — no Task domain yet",
            }

        elif action_type == "escalate_conversation":
            if not conversation_id:
                raise BusinessActionError("conversation_required")
            try:
                view = self._conversations.set_conversation_status(
                    account_id=account_id,
                    conversation_id=conversation_id,
                    status="prepared",
                )
            except ConversationError as exc:
                raise BusinessActionError(str(exc)) from exc
            result = {
                "conversation_id": view.conversation_id,
                "status": view.status,
                "note": "Escalated → prepared for operator review",
            }

        else:
            raise BusinessActionError("unknown_action_type")

        row = new_business_action(
            account_id=account_id,
            action_type=action_type,
            approved=True,
            conversation_id=conversation_id,
            payload=data,
            result=result,
            status="executed",
        )
        self._store.save(row)
        return build_action_view(row)
