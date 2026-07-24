"""Product Consultant v1 — manager replies + sticky dialog goal."""

from __future__ import annotations

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.product_consultant import (
    try_product_consultant_reply,
    consultant_state_snapshot,
)


def _turn(state: ConversationState, text: str):
    state._apply(text)
    return try_product_consultant_reply(text, [{"role": "user", "content": text}], state)


def test_want_website_offers_packages_not_questionnaire():
    state = ConversationState()
    reply = _turn(state, "Хочу сайт.")
    assert reply is not None
    low = reply.answer.lower()
    assert "basic" in low and "business" in low and "premium" in low
    assert "зафиксир" not in low
    assert "какой сайт" not in low
    assert reply.cta_href == "/order"
    assert state.consultant_intent == "website"
    snap = consultant_state_snapshot(state)
    assert snap["next_step"] == "помочь выбрать пакет"


def test_sticky_intent_business_package_no_reask():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    reply = _turn(state, "Бизнес.")
    assert reply is not None
    assert state.package_choice == "business"
    assert "business" in reply.answer.lower() or "Business" in reply.answer
    assert reply.cta_href and "business" in reply.cta_href
    assert "какой сайт" not in reply.answer.lower()


def test_dental_recommends_business():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    reply = _turn(state, "Мне для стоматологии.")
    assert reply is not None
    assert "Business" in reply.answer or "business" in reply.answer.lower()
    assert reply.cta_href


def test_repair_points_to_analysis():
    state = ConversationState()
    reply = _turn(state, "Хочу отремонтировать сайт.")
    assert reply is not None
    assert "анализ" in reply.answer.lower()
    assert reply.cta_href and "analyze" in reply.cta_href


def test_pricing_has_next_action():
    state = ConversationState()
    reply = _turn(state, "Сколько стоит?")
    assert reply is not None
    assert "350" in reply.answer or "€" in reply.answer
    assert reply.cta_href == "/order"


def test_about_virtus_core():
    state = ConversationState()
    reply = _turn(state, "Что такое Virtus Core?")
    assert reply is not None
    assert "Virtus" in reply.answer or "платформ" in reply.answer.lower()
    assert "следующ" in reply.answer.lower()


def test_affirmation_advances_not_restarts():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    reply = _turn(state, "Да.")
    assert reply is not None
    assert "Basic" in reply.answer or "пакет" in reply.answer.lower()
    assert "зафиксир" not in reply.answer.lower()


def test_from_messages_keeps_package_across_history():
    msgs = [
        {"role": "user", "content": "Хочу сайт"},
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "Premium"},
    ]
    state = ConversationState.from_messages(msgs)
    assert state.consultant_intent == "website"
    assert state.package_choice == "premium"
