"""R5.4 — ChatBot Integration (integration reference module)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.chatbot import (
    ChatBotConnectionUpdate,
    apply_chatbot_connection_update,
    empty_chatbot_connection,
)
from app.portal.chatbot_facade import ChatBotFacade
from app.portal.chatbot_integration_adapter import StubChatBotIntegrationAdapter
from app.portal.chatbot_store import InMemoryChatBotStore
from app.portal.client import new_client, website_for_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_chatbot_registration import register_portal_chatbot
from app.portal.portal_chatbot_router import (
    ENGINE_ID,
    clear_chatbot_facade,
    portal_chatbot_router,
)


def _site_and_owner():
    client = new_client(display_name="EL3", primary_email="owner@example.com")
    site = website_for_client(client, product_id="p1", market_code="DE")
    account = new_account(
        email="owner@example.com", display_name="Owner", status="ready"
    )
    ownerships = InMemoryOwnershipDirectory(
        ownerships=[grant_website_ownership(account, site)]
    )
    return site.website_id, account, ownerships


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_router_v1"


def test_domain_and_stub_adapter_reconcile():
    current = empty_chatbot_connection("w1")
    assert current.enabled is False
    assert current.status == "disconnected"

    updated = apply_chatbot_connection_update(
        current,
        ChatBotConnectionUpdate(
            enabled=True,
            provider="openai",
            status="connected",
            assistant_id=None,
        ),
    )
    assert updated.enabled is True
    assert updated.provider == "openai"

    stub = StubChatBotIntegrationAdapter()
    reconciled = stub.reconcile_status(updated)
    assert reconciled.status == "pending"

    with_id = apply_chatbot_connection_update(
        updated,
        ChatBotConnectionUpdate(
            enabled=True,
            provider="openai",
            status="pending",
            assistant_id="asst_demo",
        ),
    )
    assert stub.reconcile_status(with_id).status == "connected"


def test_facade_roundtrip_uses_adapter():
    store = InMemoryChatBotStore()
    facade = ChatBotFacade.from_parts(store, StubChatBotIntegrationAdapter())
    empty = facade.get_chatbot("w-empty")
    assert empty.enabled is False
    assert empty.provider == "none"
    assert empty.status == "disconnected"
    assert empty.assistant_id is None

    saved = facade.update_chatbot(
        "w-empty",
        enabled=True,
        provider="local",
        status="disconnected",
        assistant_id="local-1",
    )
    assert saved.enabled is True
    assert saved.provider == "local"
    assert saved.status == "connected"
    assert saved.assistant_id == "local-1"
    assert facade.get_chatbot("w-empty").as_dict() == saved.as_dict()


def test_anonymous_get_401():
    clear_chatbot_facade()
    website_id, _, ownerships = _site_and_owner()
    app = FastAPI()
    register_portal_chatbot(app, ownerships=ownerships)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/chatbot").status_code
            == 401
        )
    finally:
        clear_chatbot_facade()


def test_no_ownership_403():
    clear_chatbot_facade()
    website_id, account, _ = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot(app, ownerships=InMemoryOwnershipDirectory())
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/chatbot").status_code
            == 403
        )
    finally:
        clear_chatbot_facade()


def test_get_put_happy_path():
    clear_chatbot_facade()
    website_id, account, ownerships = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot(app, ownerships=ownerships)
    http = TestClient(app)
    try:
        g = http.get(f"/portal/websites/{website_id}/chatbot")
        assert g.status_code == 200
        assert g.json()["enabled"] is False
        assert g.json()["provider"] == "none"
        assert g.json()["status"] == "disconnected"
        assert g.json()["assistant_id"] is None

        p = http.put(
            f"/portal/websites/{website_id}/chatbot",
            json={
                "enabled": True,
                "provider": "openai",
                "status": "pending",
                "assistant_id": "asst_el3",
            },
        )
        assert p.status_code == 200
        body = p.json()
        assert body["enabled"] is True
        assert body["provider"] == "openai"
        assert body["assistant_id"] == "asst_el3"
        assert body["status"] == "connected"

        again = http.get(f"/portal/websites/{website_id}/chatbot")
        assert again.status_code == 200
        assert again.json() == body
    finally:
        clear_chatbot_facade()


def test_put_invalid_provider_400():
    clear_chatbot_facade()
    website_id, account, ownerships = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot(app, ownerships=ownerships)
    try:
        # Pydantic rejects unknown provider before domain — 422
        r = TestClient(app).put(
            f"/portal/websites/{website_id}/chatbot",
            json={
                "enabled": True,
                "provider": "anthropic",
                "status": "disconnected",
                "assistant_id": None,
            },
        )
        assert r.status_code == 422
    finally:
        clear_chatbot_facade()


def test_router_get_put_only():
    methods: set[str] = set()
    matched = False
    for route in portal_chatbot_router.routes:
        path = getattr(route, "path", "")
        if not path.endswith("/websites/{website_id}/chatbot"):
            continue
        matched = True
        methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"GET", "PUT"}


def test_main_registers_chatbot():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot(app)" in text
    assert "include_router(portal_chatbot_router)" not in text


def test_integration_boundary_no_provider_leak():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    required = [
        "chatbot.py",
        "chatbot_store.py",
        "chatbot_view.py",
        "chatbot_facade.py",
        "chatbot_integration_adapter.py",
        "portal_chatbot_router.py",
        "portal_chatbot_registration.py",
    ]
    for name in required:
        assert (portal / name).is_file(), name

    for name in (
        "chatbot.py",
        "chatbot_facade.py",
        "chatbot_view.py",
        "portal_chatbot_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8")
        assert "openai" not in text.lower() or "provider" in text.lower()
        assert "import openai" not in text
        assert "api_key" not in text.lower()
        assert "from app.portal.authentication import" not in text
        assert "from app.portal.authorization import" not in text

    adapter = (portal / "chatbot_integration_adapter.py").read_text(encoding="utf-8")
    assert "ChatBotIntegrationAdapter" in adapter
    assert "StubChatBotIntegrationAdapter" in adapter
    assert "import openai" not in adapter
    assert "requests" not in adapter

    facade = (portal / "chatbot_facade.py").read_text(encoding="utf-8")
    assert "ChatBotIntegrationAdapter" in facade
    assert "reconcile_status" in facade

    router = (portal / "portal_chatbot_router.py").read_text(encoding="utf-8")
    assert "AuthorizationFacade" in router
    assert "ChatBotFacade" in router
