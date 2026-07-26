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
    assert "Website Chat" in body["channels_available"]
    assert "WhatsApp" in body["channels_coming_soon"]
    by_id = {p["package_id"]: p for p in body["packages"]}
    assert by_id["bot_starter"]["features"]["max_bots"] == 1
    assert by_id["bot_business"]["features"]["max_bots"] == 3
    assert by_id["bot_professional"]["features"]["max_bots"] is None
    assert "До 1 источника" in by_id["bot_starter"]["features"]["knowledge_sources"]
    assert by_id["bot_starter"]["features"]["ai_analysis"] is False
    assert by_id["bot_business"]["features"]["ai_analysis"] is True
