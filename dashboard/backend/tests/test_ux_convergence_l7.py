"""L7 — UX Convergence: Journey passage, not conversation scripts."""

from __future__ import annotations

import inspect

from app.integration.concierge_service import ConciergeService
from app.integration.genesis_brain import conversation_flow
from app.integration.genesis_brain.layers.conversation_state import ConversationState
from app.integration.genesis_brain.conversation_flow import infer_journey_phase, journey_ux_reply

_PACKAGES = [
    {"id": "basic", "name": "Landing Basic", "price_eur": 350, "deliverables": []},
    {"id": "business", "name": "Landing Business", "price_eur": 650, "deliverables": []},
    {"id": "premium", "name": "Landing Premium", "price_eur": 1200, "deliverables": []},
]

_CONSULTANT_MARKERS = (
    "консультант",
    "чем могу помочь",
    "задам всего несколько вопросов",
    "ответьте на текущий вопрос",
    "поболтаем",
    "живой собеседник",
    "как ощущения",
)

_CHATBOT_QUESTIONS = (
    "Что ближе по духу",
    "Начнём с сайта?",
    "с чего начнём?",
    "Кофейня уже работает",
    "Заведение уже работает",
)


def test_conversation_flow_no_consultant_persona():
    source = inspect.getsource(conversation_flow)
    low = source.lower()
    for marker in _CONSULTANT_MARKERS:
        assert marker not in low, f"consultant marker: {marker}"
    assert "journey_ux_reply" in source
    assert "reasoned_business_reply" in source


def test_infer_journey_phase_accept_responsibility():
    state = ConversationState()
    phase = infer_journey_phase(state, "Нужен сайт для кафе")
    assert phase == "accept_responsibility"


def test_journey_ux_no_chatbot_questions_on_advice():
    state = ConversationState()
    state.country = "Россия"
    state.city = "Москва"
    state.budget_amount = 10000
    state.budget_currency = "RUB"
    state.goal = "open_business"
    reply = journey_ux_reply(state, "Хочу открыть кофейню", messages=[])
    assert reply is not None
    for q in _CHATBOT_QUESTIONS:
        assert q not in reply, f"chatbot question: {q}"


def test_concierge_cafe_immediate_quote_not_questionnaire():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен сайт для кафе")
    ans = out["answer"].lower()
    assert "конечно" not in ans or "принял" in ans
    assert out["context"]["journey_phase"] == "quoted"
    assert "650" in out["answer"] or "350" in out["answer"]
    assert out.get("cta_href") is None
    assert "заведение" not in ans or "какое у вас" not in ans


def test_concierge_greeting_no_consultant_pitch():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Привет")
    low = out["answer"].lower()
    assert "чем могу помочь" not in low
    assert "консультант" not in low


def test_concierge_order_journey_to_cta():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен сайт для кафе")
    ctx = out["context"]
    out = svc.ask("Да, оформить", context=ctx)
    assert out["cta_href"] is not None
    assert out["cta_href"].startswith("/order")
    assert out["context"]["journey_phase"] == "launch"


def test_concierge_applies_language_constitution():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Привет, нужен сайт. Gracias!")
    assert "gracias" not in out["answer"].lower()


def test_concierge_no_consulting_phase_key():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен сайт")
    ctx = out.get("context") or {}
    assert ctx.get("phase") != "consulting"
    assert "journey_phase" in ctx
