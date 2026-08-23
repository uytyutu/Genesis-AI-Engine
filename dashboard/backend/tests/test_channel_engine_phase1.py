"""Channel Engine Phase 1 — TelegramProvider adapter without rewriting Bot API path."""

from __future__ import annotations

import json
from pathlib import Path

from app.integration import workspace_ai_bots as bots
from app.integration.channel_engine import (
    ConnectionStatus,
    InboundMessage,
    get_provider,
    list_providers,
)
from app.integration.channel_engine.registry import reset_registry_for_tests
from app.integration.channel_engine.telegram_provider import TelegramProvider
from app.integration.channel_engine.types import NormalizedOutbound, ProviderCapability
from app.integration.workspace_bot_runtime import handle_telegram_update


def _seed_telegram_bot(mem: Path, customer: str = "cust-ce-1") -> str:
    bots.set_entitlements(mem, customer, "bot_business")
    created = bots.create_bot(
        mem,
        customer,
        display_name="CE Bot",
        bot_config={
            "channels": ["telegram"],
            "ai_instructions": "Sell hiking boots. Always say Nordic Boots.",
            "faq": [],
        },
        channels=["telegram"],
    )
    bot_id = created["bot"]["bot_id"]
    conn_id = "tg-ce-1"
    secret = {
        "connection_id": conn_id,
        "channel": "telegram",
        "bot_id": bot_id,
        "status": "online",
        "token": "123456:AA-test-token",
        "telegram": {"username": "ce_bot"},
    }
    cred_dir = mem / "customer_identity" / customer / "channel_credentials"
    cred_dir.mkdir(parents=True, exist_ok=True)
    (cred_dir / f"{conn_id}.json").write_text(json.dumps(secret), encoding="utf-8")
    (cred_dir / "index.json").write_text(
        json.dumps(
            {
                "connections": [
                    {
                        "connection_id": conn_id,
                        "channel": "telegram",
                        "bot_id": bot_id,
                        "status": "online",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    return bot_id


def test_registry_exposes_telegram_provider():
    reset_registry_for_tests()
    provider = get_provider("telegram")
    assert provider is not None
    assert provider.channel_type == "telegram"
    assert ProviderCapability.SEND_TEXT in provider.supported_capabilities()
    assert "telegram" in list_providers()


def test_normalize_inbound_telegram_update():
    provider = TelegramProvider()
    inbound = provider.normalize_inbound(
        {
            "update_id": 9,
            "message": {
                "message_id": 42,
                "text": "Hallo",
                "chat": {"id": 777},
                "from": {"id": 55, "first_name": "Max", "username": "max_m"},
            },
        },
        workspace_id="ws-1",
        bot_id="bot-1",
    )
    assert isinstance(inbound, InboundMessage)
    assert inbound.channel_type == "telegram"
    assert inbound.conversation_external_id == "777"
    assert inbound.external_user_id == "55"
    assert inbound.text == "Hallo"
    assert inbound.metadata.get("session_key") == "tg:777"
    assert provider.normalize_inbound({"message": {"chat": {"id": 1}}}) is None


def test_receive_matches_legacy_handle_telegram_update(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    customer = "cust-ce-parity"
    bot_id = _seed_telegram_bot(mem, customer)
    sent: list[tuple[str, object, str]] = []

    def _fake_send(token: str, chat_id, text: str):
        sent.append((token, chat_id, text))
        return {"ok": True, "result": {"message_id": 1}}

    import app.integration.workspace_bot_runtime as rt

    monkeypatch.setattr(
        rt,
        "generate_bot_reply",
        lambda bot, text, **kw: {
            "ok": True,
            "text": "Nordic Boots — how can I help?",
            "source": "test",
            "intent": "product",
        },
    )

    update = {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "text": "Need boots",
            "chat": {"id": 9001},
            "from": {"id": 11, "first_name": "Thomas"},
        },
    }
    legacy = handle_telegram_update(mem, bot_id, update, send=_fake_send)
    sent.clear()
    reset_registry_for_tests()
    provider = get_provider("telegram")
    assert provider is not None
    via_engine = provider.receive(mem, bot_id, update, send=_fake_send)

    assert legacy.get("ok") is True
    assert via_engine.get("ok") is True
    assert via_engine.get("channel_type") == "telegram"
    assert via_engine.get("reply_source") == legacy.get("reply_source")
    assert via_engine.get("reply_text") == legacy.get("reply_text")
    assert via_engine.get("normalized", {}).get("conversation_external_id") == "9001"
    assert len(sent) == 1
    assert "Nordic Boots" in sent[0][2]


def test_send_refuses_when_not_connected(tmp_path: Path):
    mem = tmp_path / "memory"
    provider = TelegramProvider()
    status = provider.health(mem, "no-customer", bot_id="missing")
    assert status == ConnectionStatus.NOT_CONNECTED
    result = provider.send(
        mem,
        "no-customer",
        NormalizedOutbound(conversation_external_id="1", text="hi"),
        bot_id="missing",
    )
    assert result.get("ok") is False
    assert result.get("error") == "CHANNEL_UNAVAILABLE"
