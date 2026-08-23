"""Channel Engine Phase 3 — WhatsApp Cloud API foundation (honest statuses)."""

from __future__ import annotations

import hashlib
import hmac

from app.integration.channel_engine import ConnectionStatus, get_provider, list_providers
from app.integration.channel_engine.registry import reset_registry_for_tests
from app.integration.channel_engine.types import NormalizedOutbound, ProviderCapability
from app.integration.channel_engine import whatsapp_cloud as wa
from app.integration.channel_engine.whatsapp_provider import WhatsAppProvider
from app.integration.meta_oauth_client import start_meta_oauth


def test_registry_includes_whatsapp_provider():
    reset_registry_for_tests()
    provider = get_provider("whatsapp")
    assert provider is not None
    assert provider.channel_type == "whatsapp"
    assert "whatsapp" in list_providers()
    assert "telegram" in list_providers()
    assert ProviderCapability.SEND_TEXT in provider.supported_capabilities()


def test_whatsapp_health_never_connected_without_keys(monkeypatch):
    monkeypatch.delenv("META_APP_ID", raising=False)
    monkeypatch.delenv("META_APP_SECRET", raising=False)
    monkeypatch.delenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", raising=False)
    provider = WhatsAppProvider()
    assert provider.health(__import__("pathlib").Path("."), "ws") == ConnectionStatus.SETUP_REQUIRED
    status = provider.foundation_status()
    assert status["connected"] is False
    assert status["live"] is False
    assert status["status"] == "SETUP_REQUIRED"


def test_whatsapp_app_review_required_when_keys_present(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "verify-me")
    provider = WhatsAppProvider()
    assert provider.health(__import__("pathlib").Path("."), "ws") == ConnectionStatus.APP_REVIEW_REQUIRED
    status = provider.foundation_status()
    assert status["connected"] is False
    assert status["commercial"] == "coming_soon"


def test_whatsapp_send_refuses_as_app_review_required(tmp_path, monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "verify-me")
    provider = WhatsAppProvider()
    result = provider.send(
        tmp_path,
        "ws",
        NormalizedOutbound(conversation_external_id="49170", text="hello"),
    )
    assert result.get("ok") is False
    assert result.get("error") == "APP_REVIEW_REQUIRED"
    assert result.get("live") is False


def test_normalize_whatsapp_webhook_text():
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA",
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "PNID"},
                            "contacts": [{"profile": {"name": "Anna"}, "wa_id": "49170"}],
                            "messages": [
                                {
                                    "from": "491701234",
                                    "id": "wamid.1",
                                    "timestamp": "1",
                                    "type": "text",
                                    "text": {"body": "Hallo WhatsApp"},
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    events = wa.normalize_whatsapp_webhook(payload)
    assert len(events) == 1
    assert events[0]["text"] == "Hallo WhatsApp"
    assert events[0]["external_user_id"] == "491701234"
    provider = WhatsAppProvider()
    inbound = provider.normalize_inbound(payload, workspace_id="ws", bot_id="b1")
    assert inbound is not None
    assert inbound.channel_type == "whatsapp"
    assert inbound.text == "Hallo WhatsApp"


def test_verify_webhook_subscribe(monkeypatch):
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "tok-xyz")
    assert (
        wa.verify_webhook_subscribe(mode="subscribe", token="tok-xyz", challenge="12345")
        == "12345"
    )
    assert wa.verify_webhook_subscribe(mode="subscribe", token="wrong", challenge="12345") is None


def test_verify_meta_signature():
    secret = "app-secret"
    body = b'{"object":"whatsapp_business_account"}'
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    assert wa.verify_meta_signature(
        app_secret=secret, raw_body=body, header_value=f"sha256={digest}"
    )
    assert not wa.verify_meta_signature(
        app_secret=secret, raw_body=body, header_value="sha256=deadbeef"
    )


def test_receive_foundation_ack_only_no_ai(tmp_path, monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", "verify-me")
    provider = WhatsAppProvider()
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WABA",
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "1",
                                    "id": "m1",
                                    "text": {"body": "hi"},
                                    "type": "text",
                                }
                            ]
                        }
                    }
                ],
            }
        ],
    }
    result = provider.receive(tmp_path, "bot", payload)
    assert result.get("ok") is True
    assert result.get("live") is False
    assert result.get("delivery") == "foundation_ack_only"
    assert result.get("events") == 1


def test_meta_oauth_start_blocks_whatsapp_fake_connect(monkeypatch):
    monkeypatch.setenv("META_APP_ID", "app-id")
    monkeypatch.setenv("META_APP_SECRET", "secret")
    monkeypatch.setenv("META_REDIRECT_URI", "https://example.com/cb")
    result = start_meta_oauth(customer_id="c1", bot_id="b1", channel="whatsapp")
    assert result.get("ok") is False
    assert result.get("reason") == "APP_REVIEW_REQUIRED"
    assert result.get("connected") is False
    assert "authorize_url" not in result
