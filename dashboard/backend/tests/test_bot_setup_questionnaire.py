"""Client bot setup questionnaire — preview + publish without CEO approve."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.bot_setup_questionnaire import build_setup_preview, parse_answers
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.portal_chatbot_product_registration import register_portal_chatbot_product
from app.portal.portal_chatbot_product_router import clear_chatbot_business_profile_facade


def test_preview_builds_greeting_and_prompt():
    out = build_setup_preview(
        {
            "business_name": "Auto Müller",
            "what_company_does": "Автосервис в Берлине",
            "services": "ТО, ремонт, диагностика",
            "answer_topics": "запись, цены ориентир, часы",
            "avoid_topics": "юридические споры",
            "working_hours": "Пн–Сб 08:00–18:00",
            "language": "ru",
            "tone": "friendly",
            "industry": "auto_service",
            "book_appointments": True,
            "take_leads": True,
            "give_prices": True,
        }
    )
    assert out["ok"] is True
    assert "Auto Müller" in out["greeting"]
    assert "цифровой" in out["system_prompt"].lower() or "цифровой" in out["greeting"].lower()
    assert out["configuration"]["placeholders"]["setup_status"] == "draft"


def test_publish_self_serve_no_ceo_gate():
    clear_chatbot_business_profile_facade()
    account = new_account(email="client@test.local", display_name="C", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    facade = register_portal_chatbot_product(app)
    http = TestClient(app)
    body = {
        "business_name": "Auto Müller",
        "what_company_does": "Ремонт авто",
        "services": "Диагностика",
        "working_hours": "Пн–Пт 9–18",
        "language": "de",
        "industry": "auto_service",
    }
    preview = http.post("/portal/chatbot/setup/preview", json=body)
    assert preview.status_code == 200
    assert preview.json()["greeting"]

    published = http.post("/portal/chatbot/setup/publish", json=body)
    assert published.status_code == 200
    data = published.json()
    assert data["ok"] is True
    assert data["status"] == "published"
    assert data["ceo_approve_required"] is False
    assert data["configuration"]["placeholders"]["setup_status"] == "published"

    view = facade.get_profile(account_id=account.account_id)
    assert view is not None
    assert view.business_name == "Auto Müller"
    assert view.initial_configuration is not None
    assert view.initial_configuration["placeholders"]["setup_status"] == "published"


def test_parse_requires_name():
    try:
        parse_answers({"business_name": "  "})
        assert False, "expected error"
    except Exception as exc:
        assert "business_name" in str(exc)
