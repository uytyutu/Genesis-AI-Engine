"""AI Platform AP1.2 — Provider Adapters (SDK isolation)."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.portal.ai_provider import new_ai_provider
from app.portal.ai_provider_adapters import (
    AnthropicProviderAdapter,
    OllamaProviderAdapter,
    OpenAIProviderAdapter,
    build_adapter_runtime,
)
from app.portal.ai_provider_facade import AIProviderFacade
from app.portal.ai_provider_registry import AIProviderRegistry
from app.portal.ai_provider_stubs import build_stub_runtime
from app.portal.ai_response import (
    AuthenticationFailed,
    InvalidConfiguration,
    ProviderUnavailable,
)
from app.portal.conversation import ConversationContext


def _context() -> ConversationContext:
    return ConversationContext(
        conversation_id="c1",
        profile_id="p1",
        business={"business_name": "Smile", "industry": "dental"},
        industry_template={
            "industry": "dental",
            "system_prompt_seed": "You help a dental clinic.",
            "default_behavior": "Be calm.",
        },
        knowledge=(
            {
                "category": "faq",
                "title": "Hours",
                "content": "09:00–19:00",
            },
        ),
        selected_categories=("faq",),
        messages=({"role": "user", "content": "When are you open?", "created_at": "t"},),
        metadata={},
    )


def test_adapters_exist_and_implement_protocol():
    record = new_ai_provider(provider_type="openai", status="configured")
    runtime = build_adapter_runtime(record)
    assert isinstance(runtime, OpenAIProviderAdapter)
    assert runtime.prepare(_context())["ready"] is True


def test_registry_bind_uses_adapters_without_registry_change():
    record = new_ai_provider(provider_type="anthropic", status="configured")
    bound = AIProviderRegistry().bind(record)
    assert isinstance(bound, AnthropicProviderAdapter)
    assert build_stub_runtime(record).__class__ is AnthropicProviderAdapter


def test_openai_adapter_maps_missing_key_to_unified_error():
    record = new_ai_provider(
        provider_type="openai",
        status="enabled",
        configuration={"model_name": "gpt-4o-mini"},
    )
    adapter = OpenAIProviderAdapter(record)
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = adapter.generate(_context())
    assert "invalid_configuration" in result.text
    payload = result.prepared["ai_response"]
    assert payload["finish_reason"] == "error"
    assert payload["provider"] == "openai"
    assert "response_id" in payload
    assert "usage" in payload


def test_openai_adapter_uses_sdk_only_inside_adapter():
    record = new_ai_provider(
        provider_type="openai",
        status="enabled",
        configuration={"model_name": "gpt-4o-mini"},
    )
    adapter = OpenAIProviderAdapter(record)

    fake_usage = MagicMock(prompt_tokens=3, completion_tokens=5, total_tokens=8)
    fake_choice = MagicMock(
        message=MagicMock(content="Clinic hours are 09:00–19:00."),
        finish_reason="stop",
    )
    fake_completion = MagicMock(choices=[fake_choice], usage=fake_usage)
    fake_client = MagicMock()
    fake_client.chat.completions.create.return_value = fake_completion
    fake_openai = MagicMock()
    fake_openai.OpenAI.return_value = fake_client

    with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test"}, clear=False):
        with patch.dict(sys.modules, {"openai": fake_openai}):
            result = adapter.generate(_context())

    assert result.text == "Clinic hours are 09:00–19:00."
    assert result.prepared["ai_response"]["provider"] == "openai"
    assert result.prepared["ai_response"]["usage"]["total_tokens"] == 8
    fake_client.chat.completions.create.assert_called_once()
    kwargs = fake_client.chat.completions.create.call_args.kwargs
    assert kwargs["model"] == "gpt-4o-mini"
    assert kwargs["messages"][0]["role"] == "system"
    assert "Smile" in kwargs["messages"][0]["content"]


def test_anthropic_adapter_maps_sdk_auth_error():
    record = new_ai_provider(
        provider_type="anthropic",
        status="enabled",
        configuration={"model_name": "claude-3-5-haiku-latest"},
    )
    adapter = AnthropicProviderAdapter(record)

    class AuthError(Exception):
        pass

    fake_anthropic = MagicMock()
    client = MagicMock()
    client.messages.create.side_effect = AuthError("invalid api key")
    fake_anthropic.Anthropic.return_value = client

    with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "ak-test"}, clear=False):
        with patch.dict(sys.modules, {"anthropic": fake_anthropic}):
            result = adapter.generate(_context())

    assert "authentication_failed" in result.text
    assert result.prepared["ai_response"]["finish_reason"] == "error"


def test_ollama_adapter_http_success(monkeypatch):
    record = new_ai_provider(
        provider_type="ollama",
        status="enabled",
        configuration={
            "model_name": "llama3.2",
            "base_url_placeholder": "http://127.0.0.1:11434",
        },
    )
    adapter = OllamaProviderAdapter(record)

    class FakeResponse:
        status_code = 200
        text = "{}"

        def json(self):
            return {
                "message": {"content": "We open at 09:00."},
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 4,
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def get(self, url):
            return FakeResponse()

        def post(self, url, json=None):
            assert url.endswith("/api/chat")
            assert json["stream"] is False
            return FakeResponse()

    monkeypatch.setattr("app.portal.ai_provider_adapters.httpx.Client", FakeClient)
    result = adapter.generate(_context())
    assert result.text == "We open at 09:00."
    assert result.prepared["ai_response"]["provider"] == "ollama"


def test_adapter_never_mutates_conversation_context():
    record = new_ai_provider(provider_type="openai", status="enabled")
    adapter = OpenAIProviderAdapter(record)
    context = _context()
    before = context.as_dict()
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        adapter.generate(context)
    assert context.as_dict() == before


def test_conversation_engine_files_unchanged_contract():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    engine = (portal / "conversation_service.py").read_text(encoding="utf-8")
    assert "from app.portal.ai_provider_adapters" not in engine
    assert "OpenAI(" not in engine
    protocol = (portal / "ai_provider_protocol.py").read_text(encoding="utf-8")
    assert (
        "def generate(self, context: ConversationContext) -> AIGenerationResult:"
        in protocol
    )
    registry = (portal / "ai_provider_registry.py").read_text(encoding="utf-8")
    assert "from app.portal.ai_provider_stubs import build_stub_runtime" in registry
    manager = (portal / "ai_provider_manager.py").read_text(encoding="utf-8")
    assert "from app.portal.ai_provider_adapters" not in manager


def test_sdk_imports_only_inside_adapters_module():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "ai_provider_manager.py",
        "ai_provider_registry.py",
        "ai_provider_protocol.py",
        "conversation_service.py",
        "conversation_facade.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "import openai" not in text
        assert "from openai" not in text
        assert "import anthropic" not in text
        assert "from anthropic" not in text
    adapters = (portal / "ai_provider_adapters.py").read_text(encoding="utf-8")
    assert "from openai import OpenAI" in adapters
    assert "import anthropic" in adapters


def test_facade_generate_returns_unified_ai_response_payload():
    facade = AIProviderFacade.from_parts(seed_stubs=True)
    openai = next(p for p in facade.list_providers() if p.provider_type == "openai")
    facade.update_provider(provider_id=openai.provider_id, status="enabled")
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = facade.generate(_context())
    assert "ai_response" in result.prepared
    assert result.prepared["ai_response"]["provider"] == "openai"


def test_platform_errors_are_not_sdk_types():
    assert issubclass(InvalidConfiguration, Exception)
    assert issubclass(AuthenticationFailed, Exception)
    assert issubclass(ProviderUnavailable, Exception)
    assert "openai" not in InvalidConfiguration.__module__
