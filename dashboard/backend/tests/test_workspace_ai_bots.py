"""Tests for workspace AI bots + Telegram channel credentials."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from app.integration import workspace_ai_bots as bots
from app.integration import workspace_channel_credentials as creds
from app.integration import meta_oauth_client as meta


def test_create_bot_respects_starter_max_1(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-starter-1"
    bots.set_entitlements(mem, customer, "bot_starter")

    first = bots.create_bot(
        mem,
        customer,
        display_name="Anna",
        bot_config={"channels": ["telegram"]},
        channels=["telegram"],
    )
    assert first["ok"] is True
    assert first["bot"]["status"] == "pending_connect"
    assert first["entitlements"]["max_bots"] == 1
    assert first["entitlements"]["bots_used"] == 1

    second = bots.create_bot(
        mem,
        customer,
        display_name="Bob",
        bot_config={},
        channels=["website_chat"],
    )
    assert second["ok"] is False
    assert second["reason"] == "max_bots_reached"
    assert second["max_bots"] == 1
    assert second["bots_used"] == 1


def test_business_allows_3_bots(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-biz-1"
    bots.set_entitlements(mem, customer, "bot_business")
    ents = bots.get_entitlements(mem, customer)
    assert ents["max_bots"] == 3
    assert ents["package_id"] == "bot_business"

    created_ids: list[str] = []
    for i in range(3):
        result = bots.create_bot(
            mem,
            customer,
            display_name=f"Bot {i + 1}",
            bot_config={"channels": ["telegram"]},
            channels=["telegram"],
        )
        assert result["ok"] is True, result
        created_ids.append(result["bot"]["bot_id"])

    assert len(bots.list_bots(mem, customer)) == 3
    fourth = bots.create_bot(
        mem,
        customer,
        display_name="Bot 4",
        bot_config={},
        channels=[],
    )
    assert fourth["ok"] is False
    assert fourth["reason"] == "max_bots_reached"
    assert fourth["max_bots"] == 3


def test_save_telegram_token_mocked_getme(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    mem = tmp_path / "memory"
    customer = "cust-tg-1"
    bot_id = "bot-abc123"

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "ok": True,
        "result": {
            "id": 123456789,
            "is_bot": True,
            "first_name": "TestBot",
            "username": "virtus_test_bot",
        },
    }

    mock_client = MagicMock()
    mock_client.__enter__.return_value = mock_client
    mock_client.__exit__.return_value = False
    mock_client.get.return_value = mock_resp

    monkeypatch.setattr(creds.httpx, "Client", lambda **_kw: mock_client)

    token = "123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw"
    result = creds.save_telegram_token(
        mem,
        customer,
        bot_id=bot_id,
        token=token,
    )
    assert result["ok"] is True
    conn = result["connection"]
    assert conn["status"] == "online"
    assert conn["channel"] == "telegram"
    assert conn["bot_id"] == bot_id
    assert conn["telegram"]["username"] == "virtus_test_bot"
    # Token must be masked in public view
    assert token not in str(conn.get("token"))
    assert conn.get("token_present") is True

    listed = creds.list_connections(mem, customer)
    assert len(listed) == 1
    assert token not in str(listed[0])

    # Secret available only via internal getter
    secret = creds.get_connection_secret(mem, customer, conn["connection_id"])
    assert secret is not None
    assert secret["token"] == token

    # Index must not contain raw token
    index_path = (
        mem / "customer_identity" / customer / "channel_credentials" / "index.json"
    )
    index_text = index_path.read_text(encoding="utf-8")
    assert token not in index_text
    assert "AAHdqTcv" not in index_text


def test_save_telegram_token_empty_rejected(tmp_path: Path):
    result = creds.save_telegram_token(
        tmp_path / "memory",
        "cust-x",
        bot_id="bot-1",
        token="   ",
    )
    assert result["ok"] is False
    assert result["reason"] == "token_empty"


def test_provision_from_paid_order(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-paid-1"
    order = {
        "order_id": "ord-test-1",
        "package_id": "bot_business",
        "business_name": "Auto Service GmbH",
        "bot_config": {
            "bot_display_name": "Anna",
            "channels": ["telegram", "website_chat"],
            "tone": "friendly",
        },
    }
    result = bots.provision_from_paid_order(mem, customer, order)
    assert result["ok"] is True
    assert result["provisioned"] is True
    assert result["bot"]["display_name"] == "Anna"
    assert result["bot"]["status"] == "pending_connect"
    assert result["entitlements"]["package_id"] == "bot_business"
    assert result["entitlements"]["max_bots"] == 3
    assert result["entitlements"]["bots_used"] == 1


def test_meta_oauth_not_configured(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("META_APP_ID", raising=False)
    monkeypatch.delenv("META_APP_SECRET", raising=False)
    assert meta.meta_oauth_configured() is False
    url = meta.build_meta_oauth_url("state-1")
    assert isinstance(url, dict)
    assert url["ok"] is False
    assert url["reason"] == "meta_not_configured"
    exchanged = meta.exchange_meta_code("abc")
    assert exchanged["ok"] is False
    assert exchanged["reason"] == "meta_not_configured"


def test_meta_oauth_build_url(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("META_APP_ID", "app123")
    monkeypatch.setenv("META_APP_SECRET", "secret456")
    monkeypatch.delenv("META_REDIRECT_URI", raising=False)
    assert meta.meta_oauth_configured() is True
    url = meta.build_meta_oauth_url("csrf-state")
    assert isinstance(url, str)
    assert "client_id=app123" in url
    assert "pages_messaging" in url
    assert "instagram_manage_messages" in url
    assert "state=csrf-state" in url
