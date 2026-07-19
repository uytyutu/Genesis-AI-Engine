"""Factory engines research — Classic Path A untouched; Claude hard-fails without key."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.engines.base import ClaudeEngineAuthError, EngineError, EngineRequest
from app.factory.engines.classic_engine import generate as classic_generate
from app.factory.engines.claude_engine import generate as claude_generate
from app.factory.engines.router import generate_with_engine, resolve_research_engine
from app.factory.engines.animated_research_pricing import list_animated_research_prices
from app.factory.factory_service import FactoryService


def test_resolve_research_engine_default_classic(monkeypatch):
    monkeypatch.delenv("FACTORY_RESEARCH_ENGINE", raising=False)
    assert resolve_research_engine() == "classic"
    assert resolve_research_engine("claude") == "claude"
    with pytest.raises(EngineError) as ei:
        resolve_research_engine("magic")
    assert ei.value.code == "unknown_engine"


def test_classic_engine_returns_html():
    result = classic_generate(
        EngineRequest(
            description="Zahnarztpraxis Mueller in Koeln. Prophylaxe und Implantate.",
            business_name="Praxis Mueller",
            market_code="DE",
            language="de",
            city="Koeln",
            phone="+49 221 555",
        )
    )
    assert result.engine_id == "classic"
    assert "<html" in result.html.lower()
    assert "Mueller" in result.html or "Praxis" in result.html


def test_claude_engine_hard_fails_without_key(monkeypatch):
    monkeypatch.delenv("GENESIS_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ClaudeEngineAuthError) as ei:
        claude_generate(
            EngineRequest(
                description="Dental clinic Austin",
                business_name="Austin Dental",
                market_code="US",
                language="en",
            )
        )
    assert ei.value.code == "claude_no_key"
    assert isinstance(ei.value, EngineError)


def test_router_claude_does_not_fallback_to_classic(monkeypatch):
    monkeypatch.delenv("GENESIS_ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    with pytest.raises(ClaudeEngineAuthError) as ei:
        generate_with_engine(
            "claude",
            EngineRequest(description="SaaS landing", business_name="Acme", market_code="US"),
        )
    assert ei.value.code == "claude_no_key"


def test_path_a_factory_still_classic_only(tmp_path: Path):
    """Path A FactoryService must not require Claude and still writes legal pages."""
    factory = FactoryService(memory_dir=tmp_path, sandbox_dir=tmp_path / "sandbox")
    product = factory.build_landing(
        "Zahnarztpraxis Test in Koeln.",
        market_code="DE",
        client_legal={
            "owner_name": "Dr. Test",
            "street": "Hauptstr. 1",
            "zip": "50667",
            "city": "Koeln",
            "email": "a@b.de",
            "phone": "+49 221 1",
        },
        contacts={"business_name": "Praxis Test", "market_code": "DE"},
    )
    product_dir = tmp_path / "sandbox" / product["product_id"]
    assert (product_dir / "index.html").is_file()
    assert (product_dir / "impressum.html").is_file()
    html = (product_dir / "index.html").read_text(encoding="utf-8")
    assert "<html" in html.lower()


def test_kimi_is_connectable_workforce_employee():
    from app.integration.workforce_setup import CONNECTABLE, SETUP_EMPLOYEES
    from app.integration.genesis_brain.providers import build_provider_registry

    assert "kimi" in CONNECTABLE
    assert any(e["id"] == "kimi" for e in SETUP_EMPLOYEES)
    assert "kimi" in build_provider_registry([])
