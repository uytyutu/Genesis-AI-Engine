"""Tests for public visitor concierge."""

from app.integration.concierge_service import ConciergeService
from app.integration.genesis_ai_service import GenesisAIService
from app.integration.llm_chat_provider import LlmChatProvider

_PACKAGES = [
    {"id": "basic", "name": "Landing Basic", "price_eur": 350, "deliverables": []},
    {"id": "business", "name": "Landing Business", "price_eur": 650, "deliverables": []},
    {"id": "premium", "name": "Landing Premium", "price_eur": 1200, "deliverables": []},
]


def test_concierge_cafe_starts_consultation_not_order():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен сайт для кафе")
    assert "кафе" in out["answer"].lower() or "конечно" in out["answer"].lower()
    assert "кофейня" in out["answer"].lower() or "заведение" in out["answer"].lower()
    assert out.get("cta_href") is None
    assert out["context"]["intent"] == "service"
    assert out["context"]["flow"] == "cafe"
    assert out["context"]["phase"] == "consulting"


def test_concierge_full_consultation_then_order_cta():
    svc = ConciergeService(_PACKAGES)
    ctx = None

    out = svc.ask("Мне нужен сайт", context=ctx)
    ctx = out["context"]
    assert out.get("cta_href") is None

    out = svc.ask("Кофейня на районе", context=ctx)
    ctx = out["context"]

    out = svc.ask("3–5 страниц", context=ctx)
    ctx = out["context"]

    out = svc.ask("Нет, оплата не нужна", context=ctx)
    ctx = out["context"]

    out = svc.ask("Да, логотип есть", context=ctx)
    ctx = out["context"]
    assert out["context"]["phase"] == "quoted"
    assert "650" in out["answer"] or "350" in out["answer"]
    assert out.get("cta_href") is None

    out = svc.ask("Да, оформить", context=ctx)
    assert out["cta_href"] == "/order?package=business" or out["cta_href"].startswith("/order")
    assert out["cta_label"]


def test_concierge_studio_intent_no_service_push():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Хочу пользоваться Genesis Studio и создавать проекты сам")
    assert "studio" in out["answer"].lower()
    assert "разработк" in out["answer"].lower() or "нельзя" in out["answer"].lower()
    assert "49" not in out["answer"]
    assert out.get("cta_href") is None


def test_concierge_subscription_explains_two_products():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Сколько стоит подписка Genesis Studio?")
    assert "studio" in out["answer"].lower() or "подписк" in out["answer"].lower()
    assert "350" in out["answer"] or "лендинг" in out["answer"].lower()
    assert "49" not in out["answer"]


def test_concierge_what_is_genesis():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Что такое Genesis?")
    assert "virtus" in out["answer"].lower()
    assert "разработк" in out["answer"].lower() or "studio" in out["answer"].lower()
    assert "350" in out["answer"] or "лендинг" in out["answer"].lower()


def test_concierge_pricing_lists_packages_no_immediate_order():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Сколько стоит?")
    assert "350" in out["answer"]
    assert out.get("cta_href") is None


def test_concierge_empty_prompt():
    svc = ConciergeService()
    out = svc.ask("   ")
    assert len(out["answer"]) > 20


def test_concierge_autoservice_consultation():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен сайт для автосервиса")
    assert "автосервис" in out["answer"].lower()
    assert out.get("cta_href") is None
    assert out["context"]["answers"]["business"] == "автосервис"


def test_genesis_ai_unavailable_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setenv("GENESIS_DEV_MOCK_LLM", "0")
    monkeypatch.setenv("GENESIS_ACCEPTANCE_GATE", "1")
    svc = GenesisAIService(_PACKAGES)
    assert not svc.llm_configured()
    assert svc.intelligence_active()
    out = svc.chat("Мне нужен сайт для кафе")
    assert out["mode"] == "genesis"
    assert out["source"] == "genesis-ai"
    assert "кафе" in out["answer"].lower() or "650" in out["answer"] or "сайт" in out["answer"].lower()


def test_bot_only_product():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен чат-бот для Telegram")
    assert "нельзя" in out["answer"].lower() or "пока" in out["answer"].lower()
    assert "250" not in out["answer"]


def test_store_quick_quote():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Мне нужен интернет-магазин")
    assert "нельзя" in out["answer"].lower() or "пока" in out["answer"].lower()
    assert "800" not in out["answer"]
    assert out["context"]["flow"] == "store"


def test_studio_subscription_pricing():
    svc = ConciergeService(_PACKAGES)
    out = svc.ask("Хочу автоматизировать бизнес через Genesis Studio")
    assert "разработк" in out["answer"].lower() or "нельзя" in out["answer"].lower()
    assert "49" not in out["answer"]


def test_genesis_ai_greeting_without_llm(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    monkeypatch.setenv("GENESIS_DEV_MOCK_LLM", "0")
    monkeypatch.setenv("GENESIS_ACCEPTANCE_GATE", "1")
    svc = GenesisAIService(_PACKAGES)
    out = svc.chat("Привет")
    assert out["mode"] == "genesis"
    assert len(out["answer"]) > 15
