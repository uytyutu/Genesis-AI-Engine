"""LLM Router — Rule #0 capability routing and reproducible proof pin."""

from __future__ import annotations

from app.integration.llm_router.capabilities import task_to_capability
from app.integration.llm_router.planner import RoutePlanner
from app.integration.llm_router.policies import FREE_TIER_EMPLOYEES
from app.integration.llm_router.proof import proof_provider_pin


class _FakeProvider:
    def __init__(self, pid: str, ok: bool = True) -> None:
        self.provider_id = pid
        self._ok = ok

    def available(self) -> bool:
        return self._ok


def test_task_maps_to_capability():
    assert task_to_capability("code") == "coding"
    assert task_to_capability("document_analysis") == "analysis"
    assert task_to_capability("complex") == "reasoning"
    assert task_to_capability("Привет") == "conversation"


def test_conversation_capability_free_first(monkeypatch):
    monkeypatch.setenv("GENESIS_GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GENESIS_GEMINI_API_KEY", "gem-test")
    registry = {
        "groq": _FakeProvider("groq"),
        "gemini": _FakeProvider("gemini"),
    }
    planner = RoutePlanner()
    plan = planner.plan("conversation", registry=registry, premium_allowed=False)
    assert plan.capability == "conversation"
    assert plan.primary == "groq"


def test_proof_pin_reorders_without_code_change(monkeypatch):
    monkeypatch.setenv("GENESIS_GROQ_API_KEY", "gsk-test")
    monkeypatch.setenv("GENESIS_GEMINI_API_KEY", "gem-test")
    monkeypatch.setenv("GENESIS_LLM_PROOF_PROVIDER", "gemini")
    registry = {
        "groq": _FakeProvider("groq"),
        "gemini": _FakeProvider("gemini"),
    }
    planner = RoutePlanner()
    plan = planner.plan("conversation", registry=registry, premium_allowed=False)
    assert plan.primary == "gemini"
    assert plan.proof_pin == "architecture_proof:gemini"


def test_coding_capability_distinct_from_conversation():
    from app.integration.llm_router.capabilities import capability_chain

    conv = capability_chain("conversation", premium_allowed=False)
    code = capability_chain("coding", premium_allowed=False)
    assert conv[0] == "groq"
    assert "groq" in code


def test_free_tier_set():
    assert "groq" in FREE_TIER_EMPLOYEES
    assert "openai" not in FREE_TIER_EMPLOYEES
