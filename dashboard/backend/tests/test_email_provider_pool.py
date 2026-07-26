"""Email Provider Pool — Resend → Gmail → Mailbox failover + journal."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.integration.email_provider_pool import (
    email_providers_health,
    provider_order,
    recent_send_journal,
    record_provider_result,
    send_via_pool,
)


def test_default_provider_order():
    order = provider_order()
    assert order[:3] == ["resend", "gmail", "mailbox"]


def test_pool_skips_unconfigured_and_fails_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("RESEND_API_KEY", raising=False)
    monkeypatch.delenv("GMAIL_REFRESH_TOKEN", raising=False)
    monkeypatch.delenv("MAILBOX_SMTP_HOST", raising=False)
    monkeypatch.delenv("MAILBOX_SMTP_USER", raising=False)
    monkeypatch.delenv("MAILBOX_SMTP_PASSWORD", raising=False)
    monkeypatch.delenv("SMTP_HOST", raising=False)
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("MAILGUN_API_KEY", raising=False)
    result = send_via_pool(
        to="a@b.co",
        subject="t",
        text="hello",
        memory_dir=tmp_path,
    )
    assert result["ok"] is False
    assert result["reason"] == "all_providers_failed"
    assert result["pool"] is True
    assert [a["provider"] for a in result["attempts"][:3]] == [
        "resend",
        "gmail",
        "mailbox",
    ]


def test_pool_uses_gmail_after_resend_cooldown(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("GENESIS_EMAIL_FROM", "from@example.com")
    record_provider_result(
        tmp_path,
        "resend",
        ok=False,
        reason="resend_error:429",
        http_status=429,
        detail="rate limited",
        cooldown_sec=3600,
    )

    called = {"gmail": 0}

    def fake_gmail(**kwargs):  # noqa: ANN003
        called["gmail"] += 1
        return {"ok": True, "provider": "gmail", "id": "g1"}

    import app.integration.email_provider_pool as pool

    monkeypatch.setitem(pool._SENDERS, "gmail", fake_gmail)
    monkeypatch.setitem(
        pool._PROBERS,
        "gmail",
        lambda: {
            "id": "gmail",
            "label": "Gmail",
            "configured": True,
            "role": "failover",
            "env_required": [],
        },
    )

    result = pool.send_via_pool(
        to="ceo@example.com",
        subject="failover",
        text="body",
        memory_dir=tmp_path,
    )
    assert result["ok"] is True
    assert result["provider"] == "gmail"
    assert called["gmail"] == 1
    assert any(a.get("provider") == "resend" for a in result["attempts"])
    journal = recent_send_journal(tmp_path)
    assert journal
    assert journal[0]["provider"] == "gmail"


def test_pool_falls_to_mailbox_after_gmail_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setenv("RESEND_API_KEY", "re_test")
    monkeypatch.setenv("GENESIS_EMAIL_FROM", "from@example.com")
    monkeypatch.setenv("MAILBOX_SMTP_HOST", "smtp.mailbox.org")
    monkeypatch.setenv("MAILBOX_SMTP_PORT", "587")
    monkeypatch.setenv("MAILBOX_SMTP_USER", "u@mailbox.org")
    monkeypatch.setenv("MAILBOX_SMTP_PASSWORD", "secret")
    monkeypatch.setenv("MAILBOX_SMTP_SECURE", "starttls")

    record_provider_result(
        tmp_path,
        "resend",
        ok=False,
        reason="resend_error:429",
        http_status=429,
        cooldown_sec=3600,
    )

    import app.integration.email_provider_pool as pool

    def fake_gmail(**kwargs):  # noqa: ANN003
        return {
            "ok": False,
            "provider": "gmail",
            "reason": "gmail_error:429",
            "http_status": 429,
            "detail": "rate limit",
        }

    def fake_mailbox(**kwargs):  # noqa: ANN003
        return {"ok": True, "provider": "mailbox", "id": "mb1"}

    monkeypatch.setitem(pool._SENDERS, "gmail", fake_gmail)
    monkeypatch.setitem(
        pool._PROBERS,
        "gmail",
        lambda: {
            "id": "gmail",
            "label": "Gmail",
            "configured": True,
            "role": "failover",
            "env_required": [],
        },
    )
    monkeypatch.setitem(pool._SENDERS, "mailbox", fake_mailbox)

    result = pool.send_via_pool(
        to="ceo@example.com",
        subject="mailbox failover",
        text="body",
        memory_dir=tmp_path,
    )
    assert result["ok"] is True
    assert result["provider"] == "mailbox"
    assert [a["provider"] for a in result["attempts"]] == ["resend", "gmail", "mailbox"]
    journal = recent_send_journal(tmp_path)
    assert journal[0]["provider"] == "mailbox"


def test_health_board_shows_gmail_429_detail(tmp_path: Path):
    record_provider_result(
        tmp_path,
        "gmail",
        ok=False,
        reason="gmail_error:429",
        http_status=429,
        detail="User-rate limit exceeded. Retry after 2026-07-26T18:45:02Z",
        cooldown_sec=600,
    )
    board = email_providers_health(tmp_path)
    gmail = next(p for p in board["providers"] if p["id"] == "gmail")
    assert gmail["last_http_status"] == 429
    assert "User-rate limit" in (gmail["last_detail"] or "")
    assert board["quota_today"]["gmail"]["status"] == "429"
    assert board["order"][:3] == ["resend", "gmail", "mailbox"]
