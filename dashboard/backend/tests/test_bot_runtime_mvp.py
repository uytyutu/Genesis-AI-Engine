"""AI Bot runtime — Telegram webhook replies from bot_config."""

from __future__ import annotations

from pathlib import Path

from app.integration import workspace_ai_bots as bots
from app.integration import workspace_channel_credentials as creds
from app.integration.sales_order_service import SalesOrderService
from app.integration.workspace_bot_runtime import (
    generate_bot_reply,
    handle_telegram_update,
)


class _Factory:
    def submit(self, intent):  # noqa: ANN001
        return {"product_id": "should-not-run"}

    class _Inner:
        def get_product(self, product_id: str):  # noqa: ANN001
            return {"id": product_id}

        def build_landing(self, **kwargs):  # noqa: ANN003
            raise AssertionError("landing factory must not run for bots")

    _factory = _Inner()


def test_faq_fallback_uses_instructions(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    bots.set_entitlements(mem, "cust-1", "bot_starter")
    created = bots.create_bot(
        mem,
        "cust-1",
        display_name="Anna",
        bot_config={
            "channels": ["telegram"],
            "ai_instructions": "We fix cars in Berlin. Mention 24h tow.",
            "faq": [{"q": "hours", "a": "Mon-Fri 9-18"}],
        },
        channels=["telegram"],
    )
    bot = created["bot"]
    import app.integration.workspace_bot_runtime as rt

    monkeypatch.setattr(rt, "build_provider_registry", lambda: {}, raising=False)

    # Patch inside generate: empty registry via providers import
    monkeypatch.setattr(
        "app.integration.genesis_brain.providers.build_provider_registry",
        lambda packages=None: {},
    )
    reply = generate_bot_reply(bot, "What are your hours?")
    assert reply["ok"] is True
    assert reply["source"] == "faq_fallback"
    assert "Mon-Fri" in reply["text"] or "9-18" in reply["text"]


def test_telegram_update_replies_with_instructions(tmp_path: Path, monkeypatch):
    mem = tmp_path / "memory"
    customer = "cust-tg-runtime"
    bots.set_entitlements(mem, customer, "bot_business")
    created = bots.create_bot(
        mem,
        customer,
        display_name="ShopBot",
        bot_config={
            "channels": ["telegram"],
            "ai_instructions": "Sell hiking boots. Always say Nordic Boots.",
            "faq": [],
        },
        channels=["telegram"],
    )
    bot_id = created["bot"]["bot_id"]

    conn_id = "tg-test-1"
    secret = {
        "connection_id": conn_id,
        "channel": "telegram",
        "bot_id": bot_id,
        "status": "online",
        "token": "123456:ABC-FAKE-TOKEN-FOR-TESTS",
        "telegram": {"username": "shop_bot"},
    }
    import json

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

    sent: list[tuple] = []

    def _send(token, chat_id, text):  # noqa: ANN001
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
        },
    )

    result = handle_telegram_update(
        mem,
        bot_id,
        {
            "update_id": 1,
            "message": {
                "message_id": 10,
                "chat": {"id": 42},
                "text": "Hi, what do you sell?",
            },
        },
        send=_send,
    )
    assert result["ok"] is True
    assert sent
    assert "Nordic Boots" in sent[0][2]


def test_start_production_bot_skips_landing(tmp_path: Path):
    sales = SalesOrderService(tmp_path, _Factory())
    created = sales.create_order(
        {
            "business_name": "Bot Co",
            "email": "bot@test.local",
            "package_id": "bot_starter",
            "customer_id": "cust-bot-prod",
            "description": "telegram employee",
            "bot_config": {"channels": ["telegram"], "ai_instructions": "Be brief."},
        }
    )
    order_id = created["order_id"]
    order = sales.get_order(order_id)
    assert order is not None
    order["status"] = "paid"
    order["paid_at"] = "2026-08-04T12:00:00+00:00"
    sales._save_order(order)  # noqa: SLF001

    result = sales.start_production(order_id)
    assert result["ok"] is True
    assert result["product_id"] is None
    refreshed = sales.get_order(order_id)
    assert refreshed is not None
    assert refreshed["product_kind"] == "bot"
    assert refreshed["status"] == "ready"
    assert refreshed.get("delivery_mode") == "workspace_bot"
    ents = bots.list_bots(tmp_path, "cust-bot-prod")
    assert len(ents) >= 1
