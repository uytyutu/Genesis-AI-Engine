"""Business Product BP1.2 — Business Knowledge (company facts)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.business_knowledge import ALLOWED_KNOWLEDGE_CATEGORIES
from app.portal.business_knowledge_facade import BusinessKnowledgeFacade
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import (
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.portal_chatbot_knowledge_registration import (
    register_portal_chatbot_knowledge,
)
from app.portal.portal_chatbot_knowledge_router import (
    ENGINE_ID,
    clear_business_knowledge_facade,
    portal_chatbot_knowledge_router,
)
from app.portal.portal_chatbot_product_registration import (
    register_portal_chatbot_product,
)
from app.portal.portal_chatbot_product_router import (
    clear_chatbot_business_profile_facade,
)


def _stack():
    profiles = InMemoryChatBotBusinessProfileStore()
    profile_facade = ChatBotBusinessProfileFacade.from_parts(profiles=profiles)
    knowledge = BusinessKnowledgeFacade.from_parts(profiles=profiles)
    return profiles, profile_facade, knowledge


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_knowledge_router_v1"


def test_categories_fixed():
    assert ALLOWED_KNOWLEDGE_CATEGORIES == {
        "company",
        "services",
        "products",
        "pricing",
        "working_hours",
        "faq",
        "policies",
        "contacts",
    }


def test_knowledge_requires_profile_and_links_profile_id():
    _, profiles, knowledge = _stack()
    try:
        knowledge.create_knowledge(
            account_id="acc-1",
            category="company",
            title="About",
            content="We exist",
        )
        raise AssertionError("expected profile_required")
    except Exception as exc:
        assert str(exc) == "profile_required"

    boot = profiles.bootstrap(
        account_id="acc-1",
        industry="dental",
        business_name="Smile",
    )
    created = knowledge.create_knowledge(
        account_id="acc-1",
        category="services",
        title="Cleaning",
        content="Профессиональная чистка",
    )
    assert created.profile_id == boot.profile_id
    assert created.category == "services"
    listed = knowledge.list_knowledge(account_id="acc-1")
    assert len(listed) == 1


def test_http_crud():
    clear_business_knowledge_facade()
    clear_chatbot_business_profile_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    profiles = InMemoryChatBotBusinessProfileStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot_product(app, profile_store=profiles)
    register_portal_chatbot_knowledge(app, profiles=profiles)
    http = TestClient(app)
    try:
        assert (
            http.post(
                "/portal/chatbot/knowledge",
                json={
                    "category": "company",
                    "title": "About",
                    "content": "Clinic",
                },
            ).status_code
            == 400
        )

        boot = http.post(
            "/portal/chatbot/profile/bootstrap",
            json={"industry": "restaurant", "business_name": "Nord"},
        )
        assert boot.status_code == 200
        profile_id = boot.json()["profile_id"]

        created = http.post(
            "/portal/chatbot/knowledge",
            json={
                "category": "working_hours",
                "title": "Hours",
                "content": "12:00–23:00",
            },
        )
        assert created.status_code == 200
        kid = created.json()["knowledge_id"]
        assert created.json()["profile_id"] == profile_id

        listed = http.get("/portal/chatbot/knowledge")
        assert listed.status_code == 200
        assert len(listed.json()) == 1

        filtered = http.get("/portal/chatbot/knowledge?category=working_hours")
        assert len(filtered.json()) == 1

        updated = http.put(
            f"/portal/chatbot/knowledge/{kid}",
            json={"content": "Ежедневно 12:00–23:00"},
        )
        assert updated.status_code == 200
        assert "Ежедневно" in updated.json()["content"]

        deleted = http.delete(f"/portal/chatbot/knowledge/{kid}")
        assert deleted.status_code == 204
        assert http.get("/portal/chatbot/knowledge").json() == []
    finally:
        clear_business_knowledge_facade()
        clear_chatbot_business_profile_facade()


def test_anonymous_401():
    clear_business_knowledge_facade()
    clear_chatbot_business_profile_facade()
    profiles = InMemoryChatBotBusinessProfileStore()
    app = FastAPI()
    register_portal_chatbot_product(app, profile_store=profiles)
    register_portal_chatbot_knowledge(app, profiles=profiles)
    try:
        assert TestClient(app).get("/portal/chatbot/knowledge").status_code == 401
    finally:
        clear_business_knowledge_facade()
        clear_chatbot_business_profile_facade()


def test_no_ai_no_sdk_invariant():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "business_knowledge.py",
        "business_knowledge_service.py",
        "business_knowledge_facade.py",
        "portal_chatbot_knowledge_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "openai" not in text
        assert "anthropic" not in text
        assert "embedding" not in text
        assert "vector db" not in text
        assert "telegram" not in text
        assert "instagram" not in text
        assert "facebook" not in text
        assert "semantic search" not in text
    domain = (portal / "business_knowledge.py").read_text(encoding="utf-8")
    assert "Business Knowledge stores facts." in domain
    assert "never generates answers" in domain
    assert "never communicates with customers" in domain


def test_router_crud_paths():
    paths: dict[str, set[str]] = {}
    for route in portal_chatbot_knowledge_router.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())
        if "/knowledge" in path:
            paths[path] = paths.get(path, set()) | methods
    assert any(p.endswith("/knowledge") for p in paths)
    assert any("/knowledge/{knowledge_id}" in p for p in paths)


def test_main_shares_profile_store():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot_knowledge(" in text
    assert "_portal_chatbot_profile_store" in text
    assert text.index("register_portal_chatbot_product(") < text.index(
        "register_portal_chatbot_knowledge("
    )
