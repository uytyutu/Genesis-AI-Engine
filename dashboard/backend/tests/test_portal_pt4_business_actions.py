"""PT4 — Business Actions (explicit operator approval · never auto-execute)."""

from __future__ import annotations

import pytest

from app.portal.account import new_account
from app.portal.business_action import BusinessActionError
from app.portal.business_action_facade import BusinessActionFacade
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import InMemoryChatBotBusinessProfileStore
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import InMemoryConversationStore, InMemoryMessageStore


def _stack():
    account = new_account(email="pt4@ex.de", display_name="Ops")
    profiles_store = InMemoryChatBotBusinessProfileStore()
    profiles = ChatBotBusinessProfileFacade.from_parts(profiles=profiles_store)
    profiles.bootstrap(
        account_id=account.account_id,
        industry="dental",
        business_name="Smile",
    )
    knowledge_store = InMemoryBusinessKnowledgeStore()
    knowledge = BusinessKnowledgeFacade.from_parts(
        profiles=profiles_store,
        knowledge=knowledge_store,
    )
    conversations = ConversationFacade.from_parts(
        profiles=profiles_store,
        knowledge=knowledge_store,
        conversations=InMemoryConversationStore(),
        messages=InMemoryMessageStore(),
    )
    actions = BusinessActionFacade.from_parts(
        conversations=conversations,
        knowledge=knowledge,
    )
    return account, conversations, knowledge, actions


def test_execute_requires_explicit_approval():
    account, conversations, _knowledge, actions = _stack()
    created = conversations.create_conversation(account_id=account.account_id)
    with pytest.raises(BusinessActionError, match="approval_required"):
        actions.execute(
            account_id=account.account_id,
            action_type="send_message",
            approved=False,
            conversation_id=created.conversation_id,
            payload={"content": "Hello"},
        )
    assert len(actions.list_actions(account_id=account.account_id)) == 0


def test_approve_send_publishes_assistant_message_without_customer_turn():
    account, conversations, _knowledge, actions = _stack()
    created = conversations.create_conversation(account_id=account.account_id)
    view = actions.execute(
        account_id=account.account_id,
        action_type="send_message",
        approved=True,
        conversation_id=created.conversation_id,
        payload={"content": "We can see you on Tuesday at 10:00."},
    )
    assert view.approved is True
    assert view.status == "executed"
    assert view.action_type == "send_message"
    detail = conversations.get_conversation(
        account_id=account.account_id,
        conversation_id=created.conversation_id,
    )
    assert len(detail.messages or []) == 1
    assert detail.messages[0].role == "assistant"
    assert "Tuesday" in detail.messages[0].content


def test_create_knowledge_requires_approval_then_persists():
    account, _conversations, knowledge, actions = _stack()
    with pytest.raises(BusinessActionError, match="approval_required"):
        actions.execute(
            account_id=account.account_id,
            action_type="create_knowledge",
            approved=False,
            payload={
                "category": "faq",
                "title": "Hours",
                "content": "Mon–Fri 9–17",
            },
        )
    view = actions.execute(
        account_id=account.account_id,
        action_type="create_knowledge",
        approved=True,
        payload={
            "category": "faq",
            "title": "Hours",
            "content": "Mon–Fri 9–17",
        },
    )
    assert view.result.get("knowledge_id")
    listed = knowledge.list_knowledge(account_id=account.account_id)
    assert any(row.title == "Hours" for row in listed)


def test_escalate_and_follow_up_appear_in_action_history():
    account, conversations, _knowledge, actions = _stack()
    created = conversations.create_conversation(account_id=account.account_id)
    actions.execute(
        account_id=account.account_id,
        action_type="escalate_conversation",
        approved=True,
        conversation_id=created.conversation_id,
    )
    actions.execute(
        account_id=account.account_id,
        action_type="create_follow_up_task",
        approved=True,
        conversation_id=created.conversation_id,
        payload={"title": "Call back"},
    )
    history = actions.list_actions(
        account_id=account.account_id,
        conversation_id=created.conversation_id,
    )
    types = {row.action_type for row in history}
    assert types == {"escalate_conversation", "create_follow_up_task"}
    detail = conversations.get_conversation(
        account_id=account.account_id,
        conversation_id=created.conversation_id,
    )
    assert detail.status == "prepared"
