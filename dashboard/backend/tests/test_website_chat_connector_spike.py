"""Website Chat connector — commercial Live channel E2E."""

from __future__ import annotations

from pathlib import Path

from app.integration import website_chat_connector as wcc
from app.integration import workspace_ai_bots as bots


def test_commercial_gate_live():
    st = wcc.commercial_status()
    assert st["commercial_live"] is True
    assert st["status"] == "live"


def test_website_chat_spike_e2e_path(tmp_path: Path):
    mem = tmp_path / "memory"
    customer = "cust-wch-1"
    bots.set_entitlements(mem, customer, "bot_starter")
    created = bots.create_bot(
        mem,
        customer,
        display_name="Sales Assistant",
        bot_config={"faq": "Termine Mo-Fr 9-18. Hallo!"},
        channels=["telegram"],
    )
    assert created["ok"] is True
    bot_id = created["bot"]["bot_id"]

    ch = wcc.create_website_channel(
        mem,
        customer,
        bot_id=bot_id,
        site_ref="order-website-basic",
        site_label="Website Basic smoke",
    )
    assert ch["ok"] is True
    conn = ch["connection"]
    assert conn["status"] == "connected"
    assert conn["public_key"].startswith("wc_")
    assert ch["commercial"]["commercial_live"] is True

    key = conn["public_key"]
    msg = wcc.handle_website_chat_message(
        mem,
        key,
        "Hallo, ich möchte einen Termin...",
        visitor_id="browser-1",
    )
    assert msg["ok"] is True
    assert msg["customer_id"] == customer
    assert msg["bot_id"] == bot_id
    assert isinstance(msg["reply"], str) and len(msg["reply"]) > 0

    # Tenant isolation: forged owner cannot use another tenant's path via wrong resolve
    other = "cust-wch-other"
    bots.set_entitlements(mem, other, "bot_starter")
    other_bot = bots.create_bot(
        mem,
        other,
        display_name="Other",
        bot_config={"faq": "secret"},
        channels=["telegram"],
    )
    other_ch = wcc.create_website_channel(
        mem, other, bot_id=other_bot["bot"]["bot_id"], site_label="Other site"
    )
    other_key = other_ch["connection"]["public_key"]
    assert other_key != key
    # Message with key A must never return customer B
    again = wcc.handle_website_chat_message(mem, key, "Noch eine Frage")
    assert again["ok"] is True
    assert again["customer_id"] == customer
    assert again["customer_id"] != other

    disc = wcc.disconnect_website_channel(mem, customer, conn["connection_id"])
    assert disc["ok"] is True
    assert disc["connection"]["status"] == "disconnected"
    blocked = wcc.handle_website_chat_message(mem, key, "after disconnect")
    assert blocked["ok"] is False
    assert blocked["reason"] in {"invalid_or_disconnected_key", "disconnected"}

    recon = wcc.reconnect_website_channel(mem, customer, conn["connection_id"])
    assert recon["ok"] is True
    new_key = recon["connection"]["public_key"]
    ok2 = wcc.handle_website_chat_message(mem, new_key, "Wieder da")
    assert ok2["ok"] is True
    assert ok2["customer_id"] == customer


def test_bot_not_found_blocks_channel(tmp_path: Path):
    mem = tmp_path / "memory"
    result = wcc.create_website_channel(
        mem, "cust-x", bot_id="missing-bot", site_label="X"
    )
    assert result["ok"] is False
    assert result["reason"] == "bot_not_found"
