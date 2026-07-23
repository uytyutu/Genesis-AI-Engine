"""S1.4 — AI Security (prompt injection · jailbreak · tools · isolation · secrets)."""

from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.business_action import BusinessActionError
from app.portal.business_action_facade import BusinessActionFacade
from app.portal.business_action_store import InMemoryBusinessActionStore
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.channel_connection_store import InMemoryChannelConnectionStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import InMemoryChatBotBusinessProfileStore
from app.portal.conversation_assistance_view import AssistanceDraftView
from app.portal.conversation_facade import ConversationFacade
from app.portal.conversation_store import InMemoryConversationStore, InMemoryMessageStore
from app.portal.industry_template import InMemoryIndustryTemplateStore
from app.portal.portal_chatbot_conversations_registration import (
    register_portal_chatbot_conversations,
)
from app.portal.portal_chatbot_conversations_router import clear_conversation_facade
from app.portal.s1_4_ai_security import (
    CROSS_USER_MEMORY,
    ENGINE_ID,
    JAILBREAK,
    PROMPT_INJECTION,
    SAFE_CONTROL,
    SECRET_EXTRACTION,
)
from app.security import (
    META_EXFILTRATION_REFUSAL,
    is_meta_exfiltration_attempt,
    scrub_internal_terms_from_answer,
)


def test_engine_id():
    assert ENGINE_ID == "s1_4_ai_security_v1"


@pytest.mark.parametrize("phrase", PROMPT_INJECTION + JAILBREAK + SECRET_EXTRACTION + CROSS_USER_MEMORY)
def test_ai_attack_phrases_detected(phrase: str):
    assert is_meta_exfiltration_attempt(phrase)


@pytest.mark.parametrize("phrase", SAFE_CONTROL)
def test_safe_user_phrases_not_blocked(phrase: str):
    assert not is_meta_exfiltration_attempt(phrase)


def test_secret_scrub_strips_key_material_from_answers():
    dirty = "Use GENESIS_GROQ_API_KEY=sk-abcdefghijklmnopqrstuvwxyz or call Groq"
    clean = scrub_internal_terms_from_answer(dirty)
    assert clean != dirty
    assert "sk-" not in clean.lower() or clean == (
        "Извините, сейчас не удалось сформировать ответ. "
        "Попробуйте переформулировать — я здесь, чтобы помочь."
    )
    assert "GENESIS_GROQ" not in clean


def test_refusal_copy_does_not_leak_internals():
    assert "system prompt" not in META_EXFILTRATION_REFUSAL.lower()
    assert "sk-" not in META_EXFILTRATION_REFUSAL


def test_tool_permission_escalation_requires_approved_true():
    alice = new_account(email="ai-a@s14.test", display_name="A", status="ready")
    profiles_store = InMemoryChatBotBusinessProfileStore()
    ChatBotBusinessProfileFacade.from_parts(profiles=profiles_store).bootstrap(
        account_id=alice.account_id, industry="dental", business_name="A"
    )
    knowledge_store = InMemoryBusinessKnowledgeStore()
    knowledge = BusinessKnowledgeFacade.from_parts(
        profiles=profiles_store, knowledge=knowledge_store
    )
    conversations = ConversationFacade.from_parts(
        profiles=profiles_store,
        knowledge=knowledge_store,
        conversations=InMemoryConversationStore(),
        messages=InMemoryMessageStore(),
    )
    actions = BusinessActionFacade.from_parts(
        store=InMemoryBusinessActionStore(),
        conversations=conversations,
        knowledge=knowledge,
    )
    conv = conversations.create_conversation(account_id=alice.account_id)
    with pytest.raises(BusinessActionError) as exc:
        actions.execute(
            account_id=alice.account_id,
            action_type="send_message",
            approved=False,
            conversation_id=conv.conversation_id,
            payload={"content": "spam"},
        )
    assert str(exc.value) == "approval_required"


def test_function_abuse_assistance_never_auto_sent():
    view = AssistanceDraftView(
        conversation_id="c1",
        draft_text="Hi",
        provider_type="stub",
        prompt_package_id=None,
        policy_language="de",
        auto_sent=False,
    )
    assert view.as_dict()["auto_sent"] is False
    assert "system_prompt" not in view.as_dict()


def test_data_isolation_and_cross_user_conversation_memory():
    clear_conversation_facade()
    alice = new_account(email="iso-a@s14.test", display_name="A", status="ready")
    bob = new_account(email="iso-b@s14.test", display_name="B", status="ready")
    profiles = InMemoryChatBotBusinessProfileStore()
    ChatBotBusinessProfileFacade.from_parts(profiles=profiles).bootstrap(
        account_id=alice.account_id, industry="dental", business_name="Alice"
    )
    ChatBotBusinessProfileFacade.from_parts(profiles=profiles).bootstrap(
        account_id=bob.account_id, industry="dental", business_name="Bob"
    )
    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    templates = InMemoryIndustryTemplateStore()
    conversations = InMemoryConversationStore()
    messages = InMemoryMessageStore()
    holder: dict[str, object] = {"account": alice}
    app = FastAPI()

    @app.middleware("http")
    async def inject(request: Request, call_next):
        request.state.account = holder["account"]
        return await call_next(request)

    register_portal_chatbot_conversations(
        app,
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
        conversation_store=conversations,
        message_store=messages,
    )
    http = TestClient(app)
    try:
        holder["account"] = alice
        created = http.post("/portal/chatbot/conversations", json={})
        assert created.status_code == 200
        cid = created.json()["conversation_id"]
        http.post(
            f"/portal/chatbot/conversations/{cid}/messages",
            json={"content": "secret alice memory atom"},
        )
        holder["account"] = bob
        stolen = http.get(f"/portal/chatbot/conversations/{cid}")
        assert stolen.status_code in {400, 403, 404}
        listed = http.get("/portal/chatbot/conversations")
        assert cid not in {row["conversation_id"] for row in listed.json()}
    finally:
        clear_conversation_facade()
