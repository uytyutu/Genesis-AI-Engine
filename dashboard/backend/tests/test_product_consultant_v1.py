"""Product Consultant — sales discovery + catalog CTAs."""

from __future__ import annotations

from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.product_consultant import (
    try_product_consultant_reply,
    consultant_state_snapshot,
)


def _turn(state: ConversationState, text: str):
    state._apply(text)
    return try_product_consultant_reply(text, [{"role": "user", "content": text}], state)


def test_want_website_starts_sales_discovery():
    state = ConversationState()
    reply = _turn(state, "Хочу сайт.")
    assert reply is not None
    low = reply.answer.lower()
    assert "вопрос" in low or "чем занимается" in low or "1/7" in reply.answer
    assert state.consultant_intent == "website"
    snap = consultant_state_snapshot(state)
    assert snap["next_step"] == "sales discovery"
    assert snap["sales_step"] == "niche"


def test_sales_discovery_recommends_business_and_order_cta():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    _turn(state, "Автосервис")
    _turn(state, "Нет сайта")
    _turn(state, "Да, нужен бот")
    _turn(state, "Да, заявки")
    _turn(state, "Нет")
    _turn(state, "Да, SEO")
    reply = _turn(state, "2-5 сотрудников")
    assert reply is not None
    assert "рекомендую" in reply.answer.lower() or "Business" in reply.answer
    assert "почему" in reply.answer.lower()
    assert reply.cta_label == "Оформить заказ"
    assert reply.cta_href and "order" in reply.cta_href
    assert state.package_choice in ("basic", "business", "premium")


def test_explicit_package_skips_discovery():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    reply = _turn(state, "Business")
    assert reply is not None
    assert state.package_choice == "business"
    assert reply.cta_href and "business" in reply.cta_href
    assert reply.cta_label == "Оформить заказ"


def test_show_packages_escape_hatch():
    state = ConversationState()
    _turn(state, "Хочу сайт.")
    reply = _turn(state, "Покажи пакеты без вопросов")
    assert reply is not None
    assert "Basic" in reply.answer and "Premium" in reply.answer
    assert reply.cta_href == "/order"


def test_autoservice_seed_niche_then_next_question():
    state = ConversationState()
    reply = _turn(state, "Мне нужен сайт автосервиса.")
    assert reply is not None
    assert state.consultant_niche == "autoservice" or "автосервис" in (
        state.sales_discovery or {}
    ).get("niche", "")
    assert "2/7" in reply.answer or "есть ли уже сайт" in reply.answer.lower()


def test_repair_is_orderable():
    state = ConversationState()
    reply = _turn(state, "Что такое Website Repair?")
    assert reply is not None
    assert "199" in reply.answer
    assert reply.cta_href == "/order?package=website_repair"
    assert reply.cta_label == "Оформить заказ"


def test_pricing_has_next_action():
    state = ConversationState()
    reply = _turn(state, "Сколько стоит?")
    assert reply is not None
    assert "350" in reply.answer or "€" in reply.answer
    assert reply.cta_href in ("/order", "/products")


def test_about_virtus_core():
    state = ConversationState()
    reply = _turn(state, "Что такое Virtus Core?")
    assert reply is not None
    assert "Virtus" in reply.answer or "платформ" in reply.answer.lower()


def test_from_messages_keeps_package_across_history():
    msgs = [
        {"role": "user", "content": "Хочу сайт"},
        {"role": "assistant", "content": "..."},
        {"role": "user", "content": "Premium"},
    ]
    state = ConversationState.from_messages(msgs)
    assert state.consultant_intent == "website"
    assert state.package_choice == "premium"


def test_ai_bot_order_lists_tiers_and_order_cta():
    state = ConversationState()
    reply = _turn(state, "Хочу заказать AI Bot.")
    assert reply is not None
    assert "499" in reply.answer
    assert "Starter" in reply.answer or "999" in reply.answer
    assert "Professional" in reply.answer or "1499" in reply.answer
    assert reply.cta_label == "Оформить заказ"
    assert reply.cta_href and ("bot" in reply.cta_href or "service=bots" in reply.cta_href)
    assert reply.cta_href != "/site"


def test_which_bot_asks_clarifying_questions():
    state = ConversationState()
    _turn(state, "Хочу AI Bot")
    reply = _turn(state, "Какой бот мне выбрать?")
    assert reply is not None
    low = reply.answer.lower()
    assert "telegram" in low or "телеграм" in low
    assert "канал" in low or "сайт" in low
    assert "whatsapp" in low or "instagram" in low


def test_seo_order_cta():
    state = ConversationState()
    reply = _turn(state, "Как заказать SEO?")
    assert reply is not None
    assert "249" in reply.answer
    assert reply.cta_href == "/order?package=seo_audit"
    assert reply.cta_label == "Оформить заказ"


def test_business_vs_premium_explained():
    state = ConversationState()
    reply = _turn(state, "Чем отличается Business от Premium?")
    assert reply is not None
    assert "Business" in reply.answer
    assert "Premium" in reply.answer
    assert reply.cta_href and "order" in reply.cta_href
