"""OR1–OR4 — Operational Readiness (correlation · logs · metrics · resilience)."""

from __future__ import annotations

import json
import logging

from app.portal.ai_provider_protocol import AIGenerationResult
from app.portal.business_action import BusinessActionError
from app.portal.business_action_facade import BusinessActionFacade
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import InMemoryChatBotBusinessProfileStore
from app.portal.conversation import ConversationContext
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import InMemoryConversationStore, InMemoryMessageStore
from app.portal.operational_context import clear_request_id, ensure_request_id, get_request_id
from app.portal.operational_log import emit_ops_event
from app.portal.operational_metrics import get_operational_metrics
from app.portal.provider_resilience import (
    OPERATOR_PROVIDER_UNAVAILABLE,
    generate_resilient,
    is_provider_failure,
)


def setup_function() -> None:
    clear_request_id()
    get_operational_metrics().reset()


def test_request_id_correlation_and_structured_log(caplog):
    ensure_request_id("req-or-1")
    assert get_request_id() == "req-or-1"
    with caplog.at_level(logging.INFO, logger="virtus.portal.ops"):
        payload = emit_ops_event(
            operation="ai_generate",
            conversation_id="conv-1",
            provider="stub",
            duration_ms=12.5,
            status="ok",
        )
    assert payload["request_id"] == "req-or-1"
    assert payload["conversation_id"] == "conv-1"
    assert "request_id" in payload
    assert any("req-or-1" in r.message for r in caplog.records)
    # Message is JSON
    parsed = json.loads(caplog.records[-1].message)
    assert parsed["operation"] == "ai_generate"
    assert set(parsed.keys()) >= {
        "timestamp",
        "level",
        "request_id",
        "conversation_id",
        "provider",
        "operation",
        "duration_ms",
        "status",
    }


def test_metrics_and_action_rejection():
    account_store = InMemoryChatBotBusinessProfileStore()
    account = __import__("app.portal.account", fromlist=["new_account"]).new_account(
        email="or@ex.de", display_name="OR"
    )
    ChatBotBusinessProfileFacade.from_parts(profiles=account_store).bootstrap(
        account_id=account.account_id,
        industry="dental",
        business_name="Smile",
    )
    knowledge_store = InMemoryBusinessKnowledgeStore()
    knowledge = BusinessKnowledgeFacade.from_parts(
        profiles=account_store, knowledge=knowledge_store
    )
    conversations = ConversationFacade.from_parts(
        profiles=account_store,
        knowledge=knowledge_store,
        conversations=InMemoryConversationStore(),
        messages=InMemoryMessageStore(),
    )
    actions = BusinessActionFacade.from_parts(
        conversations=conversations, knowledge=knowledge
    )
    created = conversations.create_conversation(account_id=account.account_id)
    snap = get_operational_metrics().snapshot()
    assert snap["conversation_count"] == 1

    try:
        actions.execute(
            account_id=account.account_id,
            action_type="send_message",
            approved=False,
            conversation_id=created.conversation_id,
            payload={"content": "x"},
        )
    except BusinessActionError as exc:
        assert str(exc) == "approval_required"
    assert get_operational_metrics().snapshot()["business_actions_rejected"] == 1

    actions.execute(
        account_id=account.account_id,
        action_type="create_follow_up_task",
        approved=True,
        conversation_id=created.conversation_id,
        payload={"title": "Call"},
    )
    assert get_operational_metrics().snapshot()["business_actions_executed"] == 1


def test_provider_resilience_operator_safe_message():
    attempts = {"n": 0}

    def failing() -> AIGenerationResult:
        attempts["n"] += 1
        return AIGenerationResult(
            text="boom",
            provider_type="openai",
            prepared={"error_code": "rate_limited", "ai_response": {"finish_reason": "error"}},
        )

    result = generate_resilient(failing, max_attempts=2)
    assert attempts["n"] == 2
    assert result.text == OPERATOR_PROVIDER_UNAVAILABLE
    assert is_provider_failure(result)
    assert "stack" not in result.text.lower()
