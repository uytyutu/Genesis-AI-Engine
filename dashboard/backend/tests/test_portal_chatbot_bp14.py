"""Business Product BP1.4 — Conversation Engine (stub context builder)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.channel_connection_facade import ChannelConnectionFacade
from app.portal.channel_connection_store import InMemoryChannelConnectionStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import (
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.conversation import STUB_ASSISTANT_REPLY
from app.portal.conversation_facade import ConversationFacade
from app.portal.industry_template import InMemoryIndustryTemplateStore
from app.portal.portal_chatbot_channels_registration import (
    register_portal_chatbot_channels,
)
from app.portal.portal_chatbot_channels_router import clear_channel_connection_facade
from app.portal.portal_chatbot_conversations_registration import (
    register_portal_chatbot_conversations,
)
from app.portal.portal_chatbot_conversations_router import (
    ENGINE_ID,
    clear_conversation_facade,
    portal_chatbot_conversations_router,
)
from app.portal.portal_chatbot_knowledge_registration import (
    register_portal_chatbot_knowledge,
)
from app.portal.portal_chatbot_knowledge_router import clear_business_knowledge_facade
from app.portal.portal_chatbot_product_registration import (
    register_portal_chatbot_product,
)
from app.portal.portal_chatbot_product_router import (
    clear_chatbot_business_profile_facade,
)


def _stack():
    profiles = InMemoryChatBotBusinessProfileStore()
    templates = InMemoryIndustryTemplateStore()
    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    profile_facade = ChatBotBusinessProfileFacade.from_parts(
        profiles=profiles, templates=templates
    )
    knowledge_facade = BusinessKnowledgeFacade.from_parts(
        profiles=profiles, knowledge=knowledge
    )
    channel_facade = ChannelConnectionFacade.from_parts(
        profiles=profiles, channels=channels
    )
    conversations = ConversationFacade.from_parts(
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
    )
    return (
        profiles,
        templates,
        knowledge,
        channels,
        profile_facade,
        knowledge_facade,
        channel_facade,
        conversations,
    )


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_conversations_router_v1"


def test_post_message_builds_context_without_ai():
    (
        _,
        _,
        _,
        _,
        profiles,
        knowledge_facade,
        channel_facade,
        conversations,
    ) = _stack()
    boot = profiles.bootstrap(
        account_id="acc-1", industry="dental", business_name="Smile"
    )
    knowledge_facade.create_knowledge(
        account_id="acc-1",
        category="faq",
        title="Hours",
        content="09:00–19:00",
    )
    knowledge_facade.create_knowledge(
        account_id="acc-1",
        category="pricing",
        title="Prices",
        content="From 50",
    )
    channel = channel_facade.create_channel(
        account_id="acc-1",
        channel="website",
        configuration={"widget_name": "Smile", "theme": "light", "language": "ru"},
    )
    created = conversations.create_conversation(
        account_id="acc-1", channel_connection_id=channel.connection_id
    )
    turn = conversations.post_message(
        account_id="acc-1",
        conversation_id=created.conversation_id,
        content="Какие у вас часы?",
    )
    assert turn.stub_response == STUB_ASSISTANT_REPLY
    assert "AI provider is not connected" in turn.stub_response
    assert turn.context["business"]["business_name"] == "Smile"
    assert turn.context["business"]["profile_id"] == boot.profile_id
    assert turn.context["industry_template"]["industry"] == "dental"
    assert turn.context["selected_categories"] == [
        "company",
        "services",
        "faq",
        "contacts",
    ]
    assert any(item["category"] == "faq" for item in turn.context["knowledge"])
    assert not any(
        item["category"] == "pricing" for item in turn.context["knowledge"]
    )
    assert turn.context["metadata"]["ai_provider"] == "not_connected"
    assert turn.conversation.status == "prepared"
    assert turn.assistant_message.role == "assistant"


def test_http_conversation_flow():
    clear_conversation_facade()
    clear_business_knowledge_facade()
    clear_channel_connection_facade()
    clear_chatbot_business_profile_facade()

    account = new_account(email="a@b.c", display_name="A", status="ready")
    profiles = InMemoryChatBotBusinessProfileStore()
    templates = InMemoryIndustryTemplateStore()
    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot_product(
        app, profile_store=profiles, template_store=templates
    )
    register_portal_chatbot_knowledge(
        app, profiles=profiles, knowledge_store=knowledge
    )
    register_portal_chatbot_channels(
        app, profiles=profiles, channel_store=channels
    )
    register_portal_chatbot_conversations(
        app,
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
    )
    http = TestClient(app)
    try:
        assert http.post("/portal/chatbot/conversations", json={}).status_code == 400

        boot = http.post(
            "/portal/chatbot/profile/bootstrap",
            json={"industry": "restaurant", "business_name": "Nord"},
        )
        assert boot.status_code == 200

        http.post(
            "/portal/chatbot/knowledge",
            json={
                "category": "services",
                "title": "Lunch",
                "content": "Business lunch daily",
            },
        )

        created = http.post("/portal/chatbot/conversations", json={})
        assert created.status_code == 200
        cid = created.json()["conversation_id"]

        listed = http.get("/portal/chatbot/conversations")
        assert len(listed.json()) == 1

        turn = http.post(
            f"/portal/chatbot/conversations/{cid}/messages",
            json={"content": "Есть ли бизнес-ланч?"},
        )
        assert turn.status_code == 200
        body = turn.json()
        assert body["context"]["business"]["industry"] == "restaurant"
        assert any(
            item["category"] == "services" for item in body["context"]["knowledge"]
        )
        assert body["stub_response"].startswith("Conversation prepared")

        got = http.get(f"/portal/chatbot/conversations/{cid}")
        assert got.status_code == 200
        assert len(got.json()["messages"]) == 2
    finally:
        clear_conversation_facade()
        clear_business_knowledge_facade()
        clear_channel_connection_facade()
        clear_chatbot_business_profile_facade()


def test_anonymous_401():
    clear_conversation_facade()
    profiles = InMemoryChatBotBusinessProfileStore()
    templates = InMemoryIndustryTemplateStore()
    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    app = FastAPI()
    register_portal_chatbot_conversations(
        app,
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
    )
    try:
        assert (
            TestClient(app).get("/portal/chatbot/conversations").status_code == 401
        )
    finally:
        clear_conversation_facade()


def test_no_ai_no_sdk_invariant():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "conversation.py",
        "conversation_service.py",
        "conversation_facade.py",
        "conversation_context_builder.py",
        "portal_chatbot_conversations_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "openai" not in text
        assert "anthropic" not in text
        assert "ollama" not in text
        assert "from telegram" not in text
        assert "import openai" not in text
        assert "streaming" not in text
        assert "function_calling" not in text
        assert "vector db" not in text
        assert "semantic search" not in text
    domain = (portal / "conversation.py").read_text(encoding="utf-8")
    assert "never generates AI responses" in domain
    assert "never communicates with external providers" in domain
    assert "never depends on external SDKs" in domain


def test_router_paths():
    paths = {
        getattr(route, "path", "") for route in portal_chatbot_conversations_router.routes
    }
    assert any(p.endswith("/conversations") for p in paths)
    assert any("/conversations/{conversation_id}/messages" in p for p in paths)


def test_main_wires_shared_stores():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot_conversations(" in text
    assert "_portal_chatbot_knowledge_store" in text
    assert "_portal_chatbot_channel_store" in text
    assert text.index("register_portal_chatbot_channels(") < text.index(
        "register_portal_chatbot_conversations("
    )
