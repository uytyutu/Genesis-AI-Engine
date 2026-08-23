"""Cooldown + lead sending health — no secrets."""

from __future__ import annotations

from pathlib import Path

from app.integration.lead_sending_health import build_lead_sending_health
from app.integration.outreach_provider_cooldown import (
    clear_resend_cooldown,
    cooldown_status,
    mark_resend_rate_limited,
    resend_available,
)
from app.integration.pricing_engine import list_bot_packages


def test_manual_failover_test_cooldown_auto_clears(tmp_path: Path):
    mark_resend_rate_limited(
        tmp_path, seconds=3600, reason="manual_failover_test"
    )
    assert resend_available(tmp_path) is True
    st = cooldown_status(tmp_path)
    assert st["resend_available"] is True
    assert st["last_reason"] is None


def test_real_429_cooldown_blocks_until_clear(tmp_path: Path):
    mark_resend_rate_limited(tmp_path, seconds=3600, reason="resend_error:429")
    assert resend_available(tmp_path) is False
    clear_resend_cooldown(tmp_path, cleared_reason="test")
    assert resend_available(tmp_path) is True


def test_lead_sending_health_explains_gmail_and_resend(tmp_path: Path):
    mark_resend_rate_limited(tmp_path, seconds=3600, reason="resend_error:429")
    cool = cooldown_status(tmp_path)
    health = build_lead_sending_health(
        memory_dir=tmp_path,
        auto_send=True,
        runner_running=True,
        ready_now=12,
        places_ready=True,
        gmail_send_ready=False,
        resend_key_present=True,
        cooldown=cool,
        domain_at_cap=False,
    )
    assert health["ok"] is True
    assert health["lamps"]["gmail"]["status"] == "red"
    assert health["lamps"]["resend"]["status"] == "red"
    assert health["lamps"]["hunt"]["status"] == "green"
    joined = " ".join(
        [health.get("current_blocker_ru") or "", health.get("next_action_ru") or ""]
        + list(health.get("next_actions") or [])
    )
    assert "Gmail" in joined or "SMTP" in joined or "провайдер" in joined.lower() or "provider" in joined.lower() or "429" in joined


def test_bot_packages_have_tier_differences():
    body = list_bot_packages("DE")
    assert body["product_id"] == "prod_ai_business_bot"
    assert "Telegram" in body["channels_available"]
    assert "Website Chat" in body["channels_available"]
    assert "Website Chat" not in body["channels_coming_soon"]
    assert "WhatsApp" in body["channels_coming_soon"]
    by_id = {p["package_id"]: p for p in body["packages"]}
    assert by_id["bot_starter"]["features"]["max_bots"] == 1
    assert by_id["bot_business"]["features"]["max_bots"] == 3
    assert by_id["bot_professional"]["features"]["max_bots"] is None
    assert "Website Chat" in by_id["bot_starter"]["features"]["extra_channels"]
    assert by_id["bot_starter"]["features"]["knowledge_enforced"] is False
    assert by_id["bot_starter"]["features"]["languages_enforced"] is False
    assert "not enforced" in by_id["bot_starter"]["features"]["knowledge_sources"]
    assert by_id["bot_starter"]["features"]["ai_analysis"] is False
    assert by_id["bot_business"]["features"]["ai_analysis"] is True
    assert by_id["bot_starter"]["max_bots"] == 1
    assert body["ssot"]["ssot_version"] == "ai_employee_ladder_v1"
    assert body["ssot"]["channels_live"] == ["Telegram", "Website Chat"]
    assert "Website Chat" not in body["ssot"]["channels_coming_soon"]
    assert "WhatsApp" in body["ssot"]["channels_coming_soon"]
    assert body["ssot"]["tiers"][0]["knowledge_enforced"] is False
    assert body["ssot"]["tiers"][0]["buy_promise_en"].startswith("One AI employee")
    assert body["ssot"]["tiers"][1]["max_bots"] == 3
    assert body["ssot"]["tiers"][2]["max_bots"] is None
    assert body["ssot"]["tiers"][1]["analytics"] == "claim"
    assert body["ssot"]["tiers"][0]["automation"] == "coming_soon"
