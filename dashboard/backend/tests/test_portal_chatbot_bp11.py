"""Business Product BP1.1 — ChatBot Business Profile & Industry Template."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.portal_chatbot_product_registration import (
    register_portal_chatbot_product,
)
from app.portal.portal_chatbot_product_router import (
    ENGINE_ID,
    clear_chatbot_business_profile_facade,
    portal_chatbot_product_router,
)


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_product_router_v1"


def test_bootstrap_dental_creates_initial_configuration():
    facade = ChatBotBusinessProfileFacade.from_parts()
    view = facade.bootstrap(
        account_id="acc-1",
        industry="dental",
        business_name="Smile Clinic",
        description="Семейная стоматология",
    )
    assert view.business_name == "Smile Clinic"
    assert view.industry == "dental"
    assert view.initial_configuration is not None
    assert "Здравствуйте" in view.initial_configuration["greeting"]
    assert view.initial_configuration["placeholders"]["appointment_faq"]
    assert len(view.initial_configuration["faq"]) >= 1


def test_bootstrap_restaurant_placeholders():
    facade = ChatBotBusinessProfileFacade.from_parts()
    view = facade.bootstrap(
        account_id="acc-2",
        industry="restaurant",
        business_name="Bistro Nord",
    )
    placeholders = view.initial_configuration["placeholders"]
    assert "menu" in placeholders
    assert "reservation_faq" in placeholders
    assert "delivery_faq" in placeholders


def test_list_templates_covers_industries():
    facade = ChatBotBusinessProfileFacade.from_parts()
    industries = {row.industry for row in facade.list_templates()}
    assert industries == {
        "dental",
        "auto_service",
        "beauty",
        "real_estate",
        "restaurant",
        "ecommerce",
        "other",
    }


def test_http_templates_bootstrap_get_put():
    clear_chatbot_business_profile_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot_product(app)
    http = TestClient(app)
    try:
        templates = http.get("/portal/chatbot/templates")
        assert templates.status_code == 200
        assert len(templates.json()) == 7

        missing = http.get("/portal/chatbot/profile")
        assert missing.status_code == 404

        boot = http.post(
            "/portal/chatbot/profile/bootstrap",
            json={
                "industry": "beauty",
                "business_name": "Glow Studio",
                "language": "ru",
                "timezone": "Europe/Berlin",
            },
        )
        assert boot.status_code == 200
        body = boot.json()
        assert body["industry"] == "beauty"
        assert body["initial_configuration"]["greeting"]

        got = http.get("/portal/chatbot/profile")
        assert got.status_code == 200
        assert got.json()["business_name"] == "Glow Studio"

        updated = http.put(
            "/portal/chatbot/profile",
            json={"description": "Маникюр и уход"},
        )
        assert updated.status_code == 200
        assert updated.json()["description"] == "Маникюр и уход"
        assert updated.json()["initial_configuration"] is not None
    finally:
        clear_chatbot_business_profile_facade()


def test_anonymous_401():
    clear_chatbot_business_profile_facade()
    app = FastAPI()
    register_portal_chatbot_product(app)
    try:
        client = TestClient(app)
        assert client.get("/portal/chatbot/templates").status_code == 401
        assert client.get("/portal/chatbot/profile").status_code == 401
        assert (
            client.post(
                "/portal/chatbot/profile/bootstrap", json={"industry": "dental"}
            ).status_code
            == 401
        )
    finally:
        clear_chatbot_business_profile_facade()


def test_no_ai_no_external_sdks():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "chatbot_business_profile.py",
        "chatbot_business_profile_service.py",
        "chatbot_business_profile_facade.py",
        "industry_template.py",
        "portal_chatbot_product_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "openai" not in text
        assert "anthropic" not in text
        assert "telegram" not in text
        assert "instagram" not in text
        assert "facebook" not in text
        assert "whatsapp" not in text
        assert "embedding" not in text
        assert " rag" not in text
        assert "streaming" not in text


def test_separate_from_website_chatbot_routes():
    paths = {getattr(route, "path", "") for route in portal_chatbot_product_router.routes}
    assert any(p.endswith("/profile") for p in paths)
    assert any(p.endswith("/templates") for p in paths)
    assert any("/profile/bootstrap" in p for p in paths)
    assert not any("/websites/" in p for p in paths)


def test_main_registers_chatbot_product():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot_product(" in text
