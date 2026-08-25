"""L0 Locale SSOT — uiLocale wiring for Vector companion (no catalog translation)."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.factory.factory_service import FactoryService
from app.integration.customer_identity.b3_review_fixture import (
    B3_REVIEW_COMPANY,
    seed_b3_review_client,
)
from app.integration.factory_intent_service import FactoryIntentService
from app.integration.locale_service import effective_chat_locale
from app.integration.sales_order_service import SalesOrderService
from app.integration.vector.companion_read import CompanionReadService


@pytest.fixture()
def mem(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.delenv("STRIPE_SECRET_KEY", raising=False)
    monkeypatch.setenv("GENESIS_PAYMENT_SANDBOX", "1")
    monkeypatch.setenv("GENESIS_ALLOW_DEMO_PAYMENT", "1")
    monkeypatch.setenv("GENESIS_SMTP_MOCK", "1")
    monkeypatch.setenv("GENESIS_CLIENT_JWT_SECRET", "b3-review-gate-jwt-secret-32chars!!")
    root = tmp_path / "memory"
    root.mkdir()
    return root


def _svc(mem: Path) -> CompanionReadService:
    factory = FactoryService(memory_dir=mem, sandbox_dir=mem / "sandbox")
    sales = SalesOrderService(mem, FactoryIntentService(memory_dir=mem, factory=factory))
    return CompanionReadService(mem, sales=sales, llm_enabled=False)


def test_effective_chat_locale_defaults_to_ui():
    assert effective_chat_locale("ru", "") == "ru"
    assert effective_chat_locale("de", "ok") == "de"


def test_effective_chat_locale_message_overrides_ui():
    assert effective_chat_locale("ru", "Was ist verbunden?") == "de"
    assert effective_chat_locale("de", "Что подключено?") == "ru"


def test_welcome_uses_ui_locale_not_hardcoded_de(mem: Path):
    fx = seed_b3_review_client(mem)
    out = _svc(mem).turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="__welcome__",
        ui_locale="ru",
    )
    assert out["reply_locale"] == "ru"
    assert out["ui_locale"] == "ru"
    reply = out["reply"]
    assert "Guten Tag" not in reply
    assert "Здравствуйте" in reply or "Vector" in reply


def test_welcome_de_when_ui_de(mem: Path):
    fx = seed_b3_review_client(mem)
    out = _svc(mem).turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="__welcome__",
        ui_locale="de",
    )
    assert out["reply_locale"] == "de"
    assert "Guten Tag" in out["reply"] or "Bei " in out["reply"] or "aktiv" in out["reply"].lower()


def test_message_language_override_keeps_terminology(mem: Path):
    fx = seed_b3_review_client(mem)
    out = _svc(mem).turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Was ist bei mir gerade verbunden?",
        ui_locale="ru",
    )
    assert out["reply_locale"] == "de"
    reply = out["reply"]
    assert "Website" in reply or "Analytics" in reply
    assert B3_REVIEW_COMPANY not in reply or "Website" in reply or "aktiv" in reply.lower()


def test_ru_ui_russian_question_stays_ru(mem: Path):
    fx = seed_b3_review_client(mem)
    out = _svc(mem).turn(
        auth_customer_id=fx.customer_id,
        auth_email=fx.email,
        me={"company_display_name": fx.business_name, "email": fx.email},
        message="Что у меня сейчас подключено?",
        ui_locale="ru",
    )
    assert out["reply_locale"] == "ru"
    assert "Активно" in out["reply"] or "аккаунт" in out["reply"].lower()
