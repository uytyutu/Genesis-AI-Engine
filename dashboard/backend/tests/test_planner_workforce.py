"""Planner → Workforce wiring — premium tier driven by intelligence layer."""

from __future__ import annotations

from app.integration.genesis_brain.brain import GenesisBrain
from app.integration.vector_intelligence.pipeline import analyze_turn


def test_code_channel_uses_tier_two():
    a = analyze_turn("Напиши python функцию для API")
    assert a.workforce_channel == "code"
    assert a.workforce_tier >= 2


def test_casual_uses_tier_one():
    a = analyze_turn("Как дела?")
    assert a.workforce_tier == 1


def test_premium_allowed_when_planner_tier_two():
    assert GenesisBrain._premium_llm_allowed(None, "короткий вопрос", workforce_tier=2) is True


def test_premium_blocked_casual_tier_one():
    assert GenesisBrain._premium_llm_allowed(None, "привет", workforce_tier=1) is False
