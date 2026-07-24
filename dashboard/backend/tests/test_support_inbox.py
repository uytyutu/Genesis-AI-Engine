"""Support inbox fingerprint + inbound ingest (no network)."""

from __future__ import annotations

from pathlib import Path

from app.integration.support_inbox_service import SupportInboxService, normalize_fingerprint


def test_normalize_fingerprint_identical():
    a = normalize_fingerprint("Hello", "When is delivery?")
    b = normalize_fingerprint("hello", "  when   is delivery?  ")
    assert a == b


def test_normalize_fingerprint_strips_quoted():
    body = "Question here\n> quoted old mail\n> more"
    a = normalize_fingerprint("Subj", body)
    b = normalize_fingerprint("Subj", "Question here")
    assert a == b


def test_ingest_and_auto_reply(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "")
    monkeypatch.setenv("GENESIS_EMAIL_FROM", "")
    svc = SupportInboxService(tmp_path)

    r1 = svc.ingest_inbound(
        from_email="client@example.com",
        subject="ETA?",
        text="How long until my site is ready?",
        auto_reply=True,
    )
    assert r1["ok"]
    thread = r1["thread"]
    assert thread["status"] == "needs_reply"
    fp = r1["message"]["fingerprint"]

    tpl = svc.create_template(
        name="ETA",
        subject="Re: ETA?",
        body="Usually about 15 minutes after payment.",
        source_fingerprint=fp,
    )
    svc.create_auto_rule(fingerprint=fp, template_id=tpl["id"], enabled=True, label="ETA")

    # Without Resend configured, auto-reply attempts but send skipped
    r2 = svc.ingest_inbound(
        from_email="client@example.com",
        subject="ETA?",
        text="How long until my site is ready?",
        auto_reply=True,
    )
    assert r2["auto_reply"] is not None
    assert r2["auto_reply"]["send"]["reason"] == "not_configured"
    # status waiting only when send ok — stays needs_reply if send failed
    assert r2["thread"]["status"] in ("needs_reply", "waiting")

    # Force ok send path for status
    monkeypatch.setattr(
        SupportInboxService,
        "_send_email",
        lambda self, **kwargs: {"ok": True, "provider": "mock"},
    )
    r3 = svc.ingest_inbound(
        from_email="other@example.com",
        subject="ETA?",
        text="How long until my site is ready?",
        auto_reply=True,
    )
    assert r3["thread"]["status"] == "waiting"
    assert r3["auto_reply"]["ok"] is True


def test_parse_resend_payload():
    parsed = SupportInboxService.parse_resend_inbound_payload(
        {
            "type": "email.received",
            "data": {
                "from": "Ada <ada@example.com>",
                "to": [{"address": "hello@genesis-ai-engine.com"}],
                "subject": "Hi",
                "text": "Body",
                "email_id": "abc",
            },
        }
    )
    assert parsed["from_email"] == "ada@example.com"
    assert parsed["to_email"] == "hello@genesis-ai-engine.com"
    assert parsed["subject"] == "Hi"
    assert parsed["external_id"] == "abc"


def test_parse_resend_payload_list_to():
    parsed = SupportInboxService.parse_resend_inbound_payload(
        {
            "type": "email.received",
            "data": {
                "from": "ada@example.com",
                "to": ["hello@genesis-ai-engine.com"],
                "subject": "Hi",
                "email_id": "abc",
            },
        }
    )
    assert parsed["from_email"] == "ada@example.com"
    assert parsed["to_email"] == "hello@genesis-ai-engine.com"
    assert parsed["text"] == ""
    assert parsed["external_id"] == "abc"


def test_svix_webhook_verify():
    from app.api.webhooks.resend_inbound import _verify_svix
    import base64
    import hashlib
    import hmac
    import time

    key = b"test-secret-key-32-bytes-long!!"
    secret = "whsec_" + base64.b64encode(key).decode("ascii")
    body = b'{"type":"email.received","data":{"from":"a@b.com","subject":"x","email_id":"1"}}'
    msg_id = "msg_test"
    ts = str(int(time.time()))
    digest = base64.b64encode(
        hmac.new(key, f"{msg_id}.{ts}.".encode() + body, hashlib.sha256).digest()
    ).decode("ascii")
    assert _verify_svix(
        secret,
        body,
        {
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": f"v1,{digest}",
        },
    )
    assert not _verify_svix(
        secret,
        body,
        {
            "svix-id": msg_id,
            "svix-timestamp": ts,
            "svix-signature": "v1,deadbeef",
        },
    )


def test_manual_reply_saves_template_rule(tmp_path: Path, monkeypatch):
    svc = SupportInboxService(tmp_path)
    monkeypatch.setattr(
        SupportInboxService,
        "_send_email",
        lambda self, **kwargs: {"ok": True, "provider": "mock"},
    )
    r1 = svc.ingest_inbound(
        from_email="c@x.com",
        subject="Price?",
        text="What does Basic cost?",
        auto_reply=False,
    )
    tid = r1["thread"]["id"]
    out = svc.reply(
        tid,
        text="Basic starts from the package price on /order.",
        save_as_template=True,
        template_name="Price Basic",
        create_auto_rule=True,
    )
    assert out["ok"]
    assert out["template_id"]
    assert out["rule_id"]
    assert len(svc.list_templates()) == 1
    assert len(svc.list_auto_rules()) == 1


def test_delete_thread(tmp_path: Path, monkeypatch):
    svc = SupportInboxService(tmp_path)
    r1 = svc.ingest_inbound(
        from_email="c@x.com",
        subject="Delete me",
        text="Gone soon",
        auto_reply=False,
    )
    tid = r1["thread"]["id"]
    assert svc.get_thread(tid) is not None
    assert svc.delete_thread(tid) is True
    assert svc.get_thread(tid) is None
    assert svc.delete_thread(tid) is False
    assert svc.list_threads() == []
