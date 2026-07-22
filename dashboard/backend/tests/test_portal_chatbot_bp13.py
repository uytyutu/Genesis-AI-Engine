"""Business Product BP1.3 — Channel Connections (stub registry)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.channel_connection import ALLOWED_CHANNELS, ALLOWED_CHANNEL_STATUSES
from app.portal.channel_connection_facade import ChannelConnectionFacade
from app.portal.chatbot_business_profile_facade import ChatBotBusinessProfileFacade
from app.portal.chatbot_business_profile_store import (
    InMemoryChatBotBusinessProfileStore,
)
from app.portal.portal_chatbot_channels_registration import (
    register_portal_chatbot_channels,
)
from app.portal.portal_chatbot_channels_router import (
    ENGINE_ID,
    clear_channel_connection_facade,
    portal_chatbot_channels_router,
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
    channels = ChannelConnectionFacade.from_parts(profiles=profiles)
    return profiles, profile_facade, channels


def test_engine_id():
    assert ENGINE_ID == "portal_chatbot_channels_router_v1"


def test_registry_types_and_statuses():
    assert ALLOWED_CHANNELS == {
        "website",
        "telegram",
        "instagram",
        "facebook",
        "whatsapp",
        "email",
        "other",
    }
    assert ALLOWED_CHANNEL_STATUSES == {
        "not_configured",
        "configured",
        "enabled",
        "disabled",
    }


def test_requires_profile_and_links_profile_id():
    _, profiles, channels = _stack()
    try:
        channels.create_channel(account_id="acc-1", channel="telegram")
        raise AssertionError("expected profile_required")
    except Exception as exc:
        assert str(exc) == "profile_required"

    boot = profiles.bootstrap(
        account_id="acc-1", industry="dental", business_name="Smile"
    )
    created = channels.create_channel(
        account_id="acc-1",
        channel="telegram",
        configuration={"bot_username": "@smile_bot", "webhook_placeholder": "pending"},
    )
    assert created.profile_id == boot.profile_id
    assert created.status == "configured"
    assert created.configuration["bot_username"] == "@smile_bot"


def test_http_crud_and_no_duplicate_channel():
    clear_channel_connection_facade()
    clear_chatbot_business_profile_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    profiles = InMemoryChatBotBusinessProfileStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_chatbot_product(app, profile_store=profiles)
    register_portal_chatbot_channels(app, profiles=profiles)
    http = TestClient(app)
    try:
        assert (
            http.post(
                "/portal/chatbot/channels", json={"channel": "website"}
            ).status_code
            == 400
        )

        boot = http.post(
            "/portal/chatbot/profile/bootstrap",
            json={"industry": "beauty", "business_name": "Glow"},
        )
        assert boot.status_code == 200
        profile_id = boot.json()["profile_id"]

        created = http.post(
            "/portal/chatbot/channels",
            json={
                "channel": "website",
                "configuration": {
                    "widget_name": "Glow Assist",
                    "theme": "light",
                    "language": "ru",
                },
            },
        )
        assert created.status_code == 200
        cid = created.json()["connection_id"]
        assert created.json()["profile_id"] == profile_id
        assert created.json()["status"] == "configured"

        dup = http.post("/portal/chatbot/channels", json={"channel": "website"})
        assert dup.status_code == 400
        assert dup.json()["detail"] == "channel_already_exists"

        listed = http.get("/portal/chatbot/channels")
        assert len(listed.json()) == 1

        updated = http.put(
            f"/portal/chatbot/channels/{cid}",
            json={"status": "enabled"},
        )
        assert updated.status_code == 200
        assert updated.json()["status"] == "enabled"

        forbidden = http.put(
            f"/portal/chatbot/channels/{cid}",
            json={"configuration": {"token": "secret"}},
        )
        assert forbidden.status_code == 400

        deleted = http.delete(f"/portal/chatbot/channels/{cid}")
        assert deleted.status_code == 204
        assert http.get("/portal/chatbot/channels").json() == []
    finally:
        clear_channel_connection_facade()
        clear_chatbot_business_profile_facade()


def test_anonymous_401():
    clear_channel_connection_facade()
    clear_chatbot_business_profile_facade()
    profiles = InMemoryChatBotBusinessProfileStore()
    app = FastAPI()
    register_portal_chatbot_product(app, profile_store=profiles)
    register_portal_chatbot_channels(app, profiles=profiles)
    try:
        assert TestClient(app).get("/portal/chatbot/channels").status_code == 401
    finally:
        clear_channel_connection_facade()
        clear_chatbot_business_profile_facade()


def test_no_sdk_no_messaging_invariant():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    for name in (
        "channel_connection.py",
        "channel_connection_service.py",
        "channel_connection_facade.py",
        "portal_chatbot_channels_router.py",
    ):
        text = (portal / name).read_text(encoding="utf-8").lower()
        assert "from telegram" not in text
        assert "telethon" not in text
        assert "openai" not in text
        assert "anthropic" not in text
        assert "send_message" not in text
        assert "receive_message" not in text
        assert "webhook_handler" not in text
    domain = (portal / "channel_connection.py").read_text(encoding="utf-8")
    assert "never send messages" in domain
    assert "never receive messages" in domain
    assert "never depend on external SDKs" in domain


def test_router_crud_paths():
    paths: dict[str, set[str]] = {}
    for route in portal_chatbot_channels_router.routes:
        path = getattr(route, "path", "")
        methods = set(getattr(route, "methods", set()) or set())
        if "/channels" in path:
            paths[path] = paths.get(path, set()) | methods
    assert any(p.endswith("/channels") for p in paths)
    assert any("/channels/{connection_id}" in p for p in paths)


def test_main_registers_channels_after_knowledge():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_chatbot_channels(" in text
    assert text.index("register_portal_chatbot_knowledge(") < text.index(
        "register_portal_chatbot_channels("
    )
