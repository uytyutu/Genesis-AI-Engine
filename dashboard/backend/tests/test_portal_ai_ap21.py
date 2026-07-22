"""AI Platform AP2.1 — Prompt & Policy Layer."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from app.portal.ai_provider import new_ai_provider
from app.portal.ai_provider_adapters import OpenAIProviderAdapter
from app.portal.ai_provider_facade import AIProviderFacade
from app.portal.conversation import ConversationContext
from app.portal.prompt_builder import build_prompt_package
from app.portal.prompt_facade import PromptFacade
from app.portal.prompt_package import PromptPackage
from app.portal.prompt_policy import resolve_policy


def _context(**overrides) -> ConversationContext:
    base = dict(
        conversation_id="c1",
        profile_id="p1",
        business={
            "business_name": "Smile",
            "industry": "dental",
            "language": "en",
        },
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
        messages=(
            {"role": "assistant", "content": "Hello.", "created_at": "t0"},
            {"role": "user", "content": "When are you open?", "created_at": "t1"},
        ),
        metadata={},
    )
    base.update(overrides)
    return ConversationContext(**base)


def test_prompt_package_has_required_contract_fields():
    package = PromptFacade().build(_context())
    assert isinstance(package, PromptPackage)
    payload = package.as_dict()
    for key in (
        "package_id",
        "system_prompt",
        "business_context",
        "conversation_history",
        "user_message",
        "generation_parameters",
    ):
        assert key in payload
    assert package.user_message == "When are you open?"
    assert package.conversation_history == (
        {"role": "assistant", "content": "Hello."},
    )
    assert "Vector" in package.system_prompt
    assert "Smile" in package.system_prompt
    assert "09:00–19:00" in package.system_prompt
    assert package.generation_parameters["temperature"] == 0.4
    assert package.generation_parameters["max_tokens"] == 800


def test_policy_applies_language_and_industry_safety():
    policy = resolve_policy(_context())
    assert policy.language == "en"
    assert any("diagnose" in rule.lower() for rule in policy.safety_rules)
    assert "Reply language: en." in policy.instruction_block()

    de = resolve_policy(
        _context(business={"business_name": "Zahn", "industry": "dental", "language": "de"})
    )
    assert de.language == "de"


def test_builder_never_mutates_context_or_knowledge():
    context = _context()
    before = context.as_dict()
    knowledge_before = [dict(item) for item in context.knowledge]
    package = build_prompt_package(context)
    assert context.as_dict() == before
    assert [dict(item) for item in context.knowledge] == knowledge_before
    assert package.business_context["business_name"] == "Smile"


def test_prompt_layer_never_imports_providers_or_sdks():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "prompt_package.py",
        "prompt_policy.py",
        "prompt_builder.py",
        "prompt_facade.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "ai_provider_adapters" not in text
        assert "import openai" not in text
        assert "from openai" not in text
        assert "import anthropic" not in text
        assert "from anthropic" not in text
        assert "httpx" not in text
        assert "channel_connection" not in text
        assert "ChannelConnection" not in text


def test_manager_attaches_prompt_package_metadata():
    facade = AIProviderFacade.from_parts(seed_stubs=True)
    openai = next(p for p in facade.list_providers() if p.provider_type == "openai")
    facade.update_provider(provider_id=openai.provider_id, status="enabled")
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = facade.generate(_context())
    assert "prompt_package_id" in result.prepared
    assert result.prepared["prompt_package_id"]


def test_adapters_consume_prompt_package_not_business_assembly():
    adapters = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "ai_provider_adapters.py"
    ).read_text(encoding="utf-8")
    assert "provider_messages()" in adapters
    assert "Business knowledge:" not in adapters
    assert "You are Vector" not in adapters
    assert "build_system_prompt" not in adapters

    record = new_ai_provider(provider_type="openai", status="enabled")
    adapter = OpenAIProviderAdapter(record)
    package = PromptFacade().build(_context())
    with patch.dict("os.environ", {"OPENAI_API_KEY": ""}, clear=False):
        result = adapter.generate(package)
    assert result.prepared["prompt_package_id"] == package.package_id


def test_prompt_facade_never_calls_generate_on_providers():
    facade_src = (
        Path(__file__).resolve().parents[1] / "app" / "portal" / "prompt_facade.py"
    ).read_text(encoding="utf-8")
    assert "generate(" not in facade_src
    assert "AIProvider" not in facade_src
