"""L8 — Template Convergence: no chatbot imitation pools."""

from __future__ import annotations

import inspect

from app.integration.genesis_brain import response_variation
from app.integration.genesis_brain import human_replies as human_replies_mod
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.layers.conversation_style import ConversationStyleEngine
from app.integration.genesis_brain.layers.self_critique import GenesisSelfCritiqueLayer
from app.integration.genesis_brain.layers.intent import IntentBrief
from app.integration.genesis_brain.response_variation import ResponseVariationEngine
from app.integration.public_truth_catalog import unavailable_online_message

_CHATBOT_MARKERS = (
    "чем могу помочь",
    "с чего начнём",
    "чем займёмся",
    "расскажите подробнее",
    "готовы попробовать",
    "просто поболтаем",
    "слушаю вас — расскажите",
    "интересный вопрос о себе",
)


def _intent(kind: str, text: str = "test") -> IntentBrief:
    return IntentBrief(
        raw_message=text,
        normalized=text,
        intent=kind,
        journey_phase="open_dialog",
        turn_index=1,
    )


def test_response_variation_pools_empty():
    assert response_variation._POOLS == {}
    assert ResponseVariationEngine().pick("greeting", "v1", "Привет") == ""


def test_self_critique_no_pool_fallback():
    layer = GenesisSelfCritiqueLayer()
    intent = _intent("small_talk", "йо")
    assert layer.polish("", intent=intent, visitor_id="v1") == ""


def test_human_reply_no_casual_pool():
    source = inspect.getsource(human_replies_mod)
    assert "_casual" not in source
    from app.integration.genesis_brain.human_replies import human_reply

    state = ConversationState()
    assert human_reply(
        "casual_conversation",
        "Привет",
        state=state,
        visitor_id="t",
        turn_index=1,
    ) is None


def test_conversation_style_single_greeting_voice():
    engine = ConversationStyleEngine()
    g1 = engine.pick_greeting(engine.build_context({}, "a"))
    g2 = engine.pick_greeting(engine.build_context({"visit_count": 5}, "a"))
    for marker in _CHATBOT_MARKERS:
        assert marker not in g1.lower()
        assert marker not in g2.lower()


def test_public_truth_no_consultation_wording():
    msg = unavailable_online_message("Чат-бот").lower()
    assert "консультац" not in msg
    assert "расскажите, для какого" not in msg


def test_self_critique_strips_chatbot_phrases():
    layer = GenesisSelfCritiqueLayer()
    intent = _intent("general")
    out = layer.polish(
        "Отлично, на связи. Чем могу помочь сегодня?",
        intent=intent,
        cloud_llm_used=True,
    )
    assert "чем могу помочь" not in out.lower()
