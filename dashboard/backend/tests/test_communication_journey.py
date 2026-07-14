"""L4 — Journey-first communication gate and intent layer."""

from __future__ import annotations

from app.integration.genesis_brain.communication_gate import resolve_communication_gate
from app.integration.genesis_brain.layers.intent import GenesisIntentLayer
from app.integration.genesis_brain.layers.reasoning import GenesisReasoningLayer


def test_intent_prompt_hint_uses_journey_not_role():
    intent = GenesisIntentLayer().analyze([{"role": "user", "content": "Как дела?"}])
    hint = intent.to_prompt_hint()
    assert "Этап Journey:" in hint
    assert "Роль:" not in hint
    assert intent.journey_phase == "open_dialog"


def test_business_intent_accepts_responsibility_phase():
    intent = GenesisIntentLayer().analyze(
        [{"role": "user", "content": "Хочу открыть ресторан"}],
    )
    assert intent.intent == "business"
    assert intent.journey_phase == "accept_responsibility"
    assert "принять задачу" in intent.goals[0].lower()


def test_reasoning_no_suggested_role():
    brief = GenesisReasoningLayer().analyze([{"role": "user", "content": "Как дела?"}])
    assert brief.journey_phase == "open_dialog"
    assert brief.should_recommend is False
    assert "Роль:" not in brief.to_prompt_hint()


def test_reasoning_recommends_on_work_phase():
    brief = GenesisReasoningLayer().analyze(
        [{"role": "user", "content": "Хочу сайт для кафе"}],
    )
    assert brief.journey_phase == "accept_responsibility"
    assert brief.should_recommend is True


def test_communication_gate_open_dialog_blocks_commerce():
    gate = resolve_communication_gate("Как дела?")
    assert gate.journey_phase == "open_dialog"
    assert gate.product_mind is False
    assert gate.commercial_knowledge is False


def test_communication_gate_work_phase_loads_product_mind():
    gate = resolve_communication_gate("Нужен сайт для салона")
    assert gate.journey_phase == "accept_responsibility"
    assert gate.product_mind is True


def test_greeting_goal_not_companion_phrase():
    intent = GenesisIntentLayer().analyze([{"role": "user", "content": "Привет"}])
    goals = " ".join(intent.goals).lower()
    assert "поболтать" not in goals
    assert "контакт" in goals
