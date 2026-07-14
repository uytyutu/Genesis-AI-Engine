"""L6 — Behavior Convergence: layers describe Journey state, not communication strategy."""

from __future__ import annotations

import inspect
import re

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.curiosity import CuriosityLayer
from app.integration.genesis_brain.layers.emotional_intelligence import EmotionalBrief, Mood
from app.integration.genesis_brain.layers.goal_analysis import GoalBrief, ThreadContext
from app.integration.genesis_brain.layers.thinking_brief import ThinkingBrief
from app.integration.genesis_brain.reasoned_reply import reasoned_business_reply
from app.integration.genesis_brain import semantic_briefs

_ROLE_MARKERS = (
    "консультант",
    "собеседник",
    "наставник",
    "живой собеседник",
    "будь ",
    "как себя вести",
    "один вопрос о человеке",
    "интересный вопрос",
    "product mind: консультант",
)

_CASUAL_CLOSERS = (
    "Заведение уже работает?",
    "Начнём с сайта?",
    "Что ближе по духу",
    "или есть конкретная задача?",
    "Могу набросать план на первые 2 недели — с чего начнём?",
)


def _neutral_emotion() -> EmotionalBrief:
    return EmotionalBrief(mood=Mood.NEUTRAL, intensity="low", lead_with_empathy=False)


def test_semantic_briefs_no_role_strategy():
    source = inspect.getsource(semantic_briefs)
    low = source.lower()
    for marker in _ROLE_MARKERS:
        assert marker not in low, f"role marker in semantic_briefs: {marker}"
    assert "_journey_ctx" in source
    assert "этап Journey:" in source


def test_curiosity_empty_without_missing_facts():
    layer = CuriosityLayer()
    hint = layer.suggest(
        user_message="Хочу открыть кафе",
        emotional=_neutral_emotion(),
        turn_index=1,
        visitor_id="t",
        has_business_topic=True,
        journey_phase="understand_goal",
        missing_facts=(),
    )
    assert hint.append is None


def test_curiosity_only_on_journey_gap():
    layer = CuriosityLayer()
    hint = layer.suggest(
        user_message="Хочу открыть кафе",
        emotional=_neutral_emotion(),
        turn_index=1,
        visitor_id="t",
        has_business_topic=True,
        journey_phase="understand_goal",
        missing_facts=("country",),
    )
    assert hint.append is not None
    assert "Нужен один факт для движения" in hint.append
    assert "В какой стране" in hint.append


def test_curiosity_skips_open_dialog():
    layer = CuriosityLayer()
    hint = layer.suggest(
        user_message="Привет",
        emotional=_neutral_emotion(),
        turn_index=1,
        visitor_id="t",
        has_business_topic=False,
        journey_phase="open_dialog",
        missing_facts=("country",),
    )
    assert hint.append is None


def test_thinking_brief_mandate_no_personality_cortex():
    brief = ThinkingBrief(best_response_strategy="этап Journey: Открытый диалог")
    mandate = brief.to_llm_mandate(executive_action="answer", executive_confidence=0.8)
    low = mandate.lower()
    assert "personality:" not in low
    assert "cortex" not in low
    assert "journey context:" in low


def test_reasoned_reply_advice_no_casual_closers():
    state = ConversationState()
    state.country = "Россия"
    state.city = "Москва"
    state.budget_amount = 10000
    state.budget_currency = "RUB"
    state.goal = "open_business"
    reply = reasoned_business_reply(state, "Хочу открыть кофейню", messages=[])
    assert reply is not None
    for closer in _CASUAL_CLOSERS:
        assert closer not in reply, f"casual closer found: {closer}"
    assert reply.rstrip().endswith(".") or "Следующий шаг" in reply


def test_reasoned_reply_asks_only_for_critical_gaps():
    state = ConversationState()
    state.goal = "open_business"
    reply = reasoned_business_reply(state, "Помоги с бизнесом", messages=[])
    assert reply is not None
    assert "В какой стране" in reply
    state.country = "Германия"
    reply2 = reasoned_business_reply(state, "Помоги с бизнесом", messages=[])
    assert reply2 is not None
    assert "бюджет" in reply2.lower()


def test_small_talk_brief_journey_context_only():
    base = ThinkingBrief()
    goal = GoalBrief(
        real_goal="small_talk",
        helpful_action="answer",
        emotion="neutral",
        implicit_need="",
        reasoning_chain="",
        thread=ThreadContext(),
        surface_topic="",
    )
    brief = semantic_briefs._small_talk_brief(base, goal, "Привет")
    assert "этап Journey:" in brief.best_response_strategy
    assert "консультант" not in brief.best_response_strategy.lower()
