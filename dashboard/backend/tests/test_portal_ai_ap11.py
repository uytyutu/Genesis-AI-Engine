"""AI Platform AP1.1 — Provider Layer (stub LLM abstraction)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.ai_provider import STUB_UNAVAILABLE_REPLY
from app.portal.ai_provider_facade import AIProviderFacade
from app.portal.ai_provider_protocol import AIProviderProtocol
from app.portal.business_knowledge_store import InMemoryBusinessKnowledgeStore
from app.portal.channel_connection_store import InMemoryChannelConnectionStore
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import (
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.conversation import ConversationContext
from app.portal.conversation_facade import ConversationFacade
from app.portal.industry_template import InMemoryIndustryTemplateStore
from app.portal.portal_chatbot_conversations_registration import (
    register_portal_chatbot_conversations,
)
from app.portal.portal_chatbot_conversations_router import clear_conversation_facade
from app.portal.portal_chatbot_product_registration import (
    register_portal_chatbot_product,
)
from app.portal.portal_chatbot_product_router import (
    clear_chatbot_business_profile_facade,
)
from app.portal.portal_chatbot_providers_registration import (
    register_portal_chatbot_providers,
)
from app.portal.portal_chatbot_providers_router import (
    ENGINE_ID,
    clear_ai_provider_facade,
    portal_chatbot_providers_router,
)


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_providers_router_v1"


def test_protocol_implemented_by_stubs():
    facade = AIProviderFacade.from_parts(seed_stubs=True)
    listed = facade.list_providers()
    assert {row.provider_type for row in listed} >= {
        "openai",
        "anthropic",
        "ollama",
    }
    from app.portal.ai_provider_adapters import (
        AnthropicProviderAdapter,
        OllamaProviderAdapter,
        OpenAIProviderAdapter,
    )

    for row in listed:
        runtime = facade.manager._registry.bind(
            facade.manager._store.get(row.provider_id)
        )
        assert isinstance(
            runtime,
            (OpenAIProviderAdapter, AnthropicProviderAdapter, OllamaProviderAdapter),
        )
        assert isinstance(runtime, AIProviderProtocol)


def test_generate_via_protocol_without_external_calls():
    facade = AIProviderFacade.from_parts(seed_stubs=True)
    openai = next(
        row for row in facade.list_providers() if row.provider_type == "openai"
    )
    facade.update_provider(provider_id=openai.provider_id, status="enabled")
    context = ConversationContext(
        conversation_id="c1",
        profile_id="p1",
        business={"business_name": "Demo"},
        industry_template={"industry": "dental"},
        knowledge=({"category": "faq", "title": "Q", "content": "A"},),
        selected_categories=("faq",),
        messages=({"role": "user", "content": "hi", "created_at": "t"},),
        metadata={},
    )
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = facade.generate(context)
    assert "invalid_configuration" in result.text or "Provider unavailable" in result.text
    assert result.provider_type == "openai"
    assert result.prepared["ready"] is True
    assert result.prepared["conversation_id"] == "c1"


def test_conversation_uses_provider_layer():
    profiles = InMemoryChatBotBusinessProfileStore()
    templates = InMemoryIndustryTemplateStore()
    knowledge = InMemoryBusinessKnowledgeStore()
    channels = InMemoryChannelConnectionStore()
    providers = AIProviderFacade.from_parts(seed_stubs=True)
    openai = next(
        row for row in providers.list_providers() if row.provider_type == "openai"
    )
    providers.update_provider(provider_id=openai.provider_id, status="enabled")

    profile_facade = ChatBotBusinessProfileFacade.from_parts(
        profiles=profiles, templates=templates
    )
    conversations = ConversationFacade.from_parts(
        profiles=profiles,
        knowledge=knowledge,
        channels=channels,
        templates=templates,
        providers=providers.manager,
    )
    profile_facade.bootstrap(
        account_id="acc-1", industry="dental", business_name="Smile"
    )
    created = conversations.create_conversation(account_id="acc-1")
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        turn = conversations.post_message(
            account_id="acc-1",
            conversation_id=created.conversation_id,
            content="Hello",
        )
    assert "invalid_configuration" in turn.stub_response
    assert turn.context["metadata"]["ai_provider"] == "openai"
    assert "ai_response" in turn.context["metadata"]["provider_prepared"]


def test_http_providers_crud_and_health():
    clear_ai_provider_facade()
    clear_chatbot_business_profile_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot_providers(app, seed_stubs=True)
    http = TestClient(app)
    try:
        listed = http.get("/portal/chatbot/providers")
        assert listed.status_code == 200
        assert len(listed.json()) == 3

        openai = next(
            row for row in listed.json() if row["provider_type"] == "openai"
        )
        health = http.post(f"/portal/chatbot/providers/{openai['provider_id']}/health")
        assert health.status_code == 200
        # configured (not enabled yet) — adapter reports configured
        assert health.json()["status"] in {"configured", "enabled"}

        enabled = http.put(
            f"/portal/chatbot/providers/{openai['provider_id']}",
            json={"status": "enabled"},
        )
        assert enabled.status_code == 200
        assert enabled.json()["status"] == "enabled"
        assert enabled.json()["is_active"] is True

        with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
            health2 = http.post(
                f"/portal/chatbot/providers/{openai['provider_id']}/health"
            )
        assert health2.status_code == 200
        assert health2.json()["ok"] is False

        forbidden = http.put(
            f"/portal/chatbot/providers/{openai['provider_id']}",
            json={"configuration": {"api_key": "secret"}},
        )
        assert forbidden.status_code == 400
    finally:
        clear_ai_provider_facade()
        clear_chatbot_business_profile_facade()


def test_anonymous_401():
    clear_ai_provider_facade()
    app = FastAPI()
    register_portal_chatbot_providers(app, seed_stubs=False)
    try:
        assert TestClient(app).get("/portal/chatbot/providers").status_code == 401
    finally:
        clear_ai_provider_facade()


def test_no_sdk_no_http_invariant():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "ai_provider.py",
        "ai_provider_protocol.py",
        "ai_provider_stubs.py",
        "ai_provider_manager.py",
        "ai_provider_facade.py",
        "portal_chatbot_providers_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "import openai" not in text
        assert "from openai" not in text
        assert "import anthropic" not in text
        assert "from anthropic" not in text
        assert "httpx" not in text
        assert "requests." not in text
        assert "urllib.request" not in text
        assert "function_calling" not in text
        assert "vector db" not in text
    domain = (portal / "ai_provider.py").read_text(encoding="utf-8")
    assert "never prepares business context" in domain
    assert "never manages conversations" in domain
    assert "never communicates directly with channels" in domain


def test_router_paths():
    paths = {
        getattr(route, "path", "") for route in portal_chatbot_providers_router.routes
    }
    assert any(p.endswith("/providers") for p in paths)
    assert any("/providers/{provider_id}/health" in p for p in paths)


def test_main_registers_providers_before_conversations():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot_providers(" in text
    assert text.index("register_portal_chatbot_providers(") < text.index(
        "register_portal_chatbot_conversations("
    )
    assert "providers=_portal_ai_provider_facade.manager" in text


def test_unavailable_without_enabled_provider():
    facade = AIProviderFacade.from_parts(seed_stubs=True)
    context = ConversationContext(
        conversation_id="c1",
        profile_id="p1",
        business={},
        industry_template=None,
        knowledge=(),
        selected_categories=(),
        messages=(),
    )
    result = facade.generate(context)
    assert result.text == STUB_UNAVAILABLE_REPLY
