"""WhatsApp Cloud API helpers — official webhooks only (no unofficial automation).

Phase 3 foundation: verify handshake + signature checks.
Does NOT claim CONNECTED or run AI Employee replies until Live E2E + App Review.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from typing import Any


def meta_app_secret() -> str:
    return (os.getenv("META_APP_SECRET") or "").strip()


def whatsapp_verify_token() -> str:
    return (
        os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
        or os.getenv("META_WEBHOOK_VERIFY_TOKEN")
        or ""
    ).strip()


def meta_app_configured() -> bool:
    return bool((os.getenv("META_APP_ID") or "").strip() and meta_app_secret())


def whatsapp_foundation_status() -> dict[str, Any]:
    """Honest public/operator status — never CONNECTED without Live E2E."""
    configured = meta_app_configured()
    verify_ready = bool(whatsapp_verify_token())
    if not configured:
        status = "SETUP_REQUIRED"
        note = "META_APP_ID / META_APP_SECRET missing — WhatsApp Cloud API not configured."
    elif not verify_ready:
        status = "SETUP_REQUIRED"
        note = "Webhook verify token missing (WHATSAPP_WEBHOOK_VERIFY_TOKEN)."
    else:
        status = "APP_REVIEW_REQUIRED"
        note = (
            "Platform keys present. WhatsApp remains Coming Soon until Meta App Review, "
            "WABA/phone assets, and controlled inbound/outbound E2E PASS."
        )
    return {
        "channel": "whatsapp",
        "status": status,
        "connected": False,
        "live": False,
        "commercial": "coming_soon",
        "api": "whatsapp_cloud_api",
        "meta_app_configured": configured,
        "webhook_verify_configured": verify_ready,
        "note": note,
        "honesty_rule": "READY_FOR_META_APP_REVIEW_IS_NOT_CONNECTED",
    }


def verify_webhook_subscribe(
    *,
    mode: str | None,
    token: str | None,
    challenge: str | None,
) -> str | None:
    """Return challenge string if Meta GET verification succeeds, else None."""
    expected = whatsapp_verify_token()
    if not expected:
        return None
    if str(mode or "") != "subscribe":
        return None
    if not hmac.compare_digest(str(token or ""), expected):
        return None
    ch = str(challenge or "")
    return ch if ch else None


def verify_meta_signature(*, app_secret: str, raw_body: bytes, header_value: str | None) -> bool:
    """Validate X-Hub-Signature-256 (sha256=<hex>) using Meta App Secret."""
    secret = (app_secret or "").strip()
    header = str(header_value or "").strip()
    if not secret or not header:
        return False
    if not header.startswith("sha256="):
        return False
    provided = header[len("sha256=") :]
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(digest, provided)


def normalize_whatsapp_webhook(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract minimal inbound text events from Cloud API webhook JSON (no AI side-effects)."""
    out: list[dict[str, Any]] = []
    if not isinstance(payload, dict):
        return out
    if str(payload.get("object") or "") not in ("whatsapp_business_account", "whatsapp"):
        # Still accept nested entry shapes used by Cloud API
        pass
    entries = payload.get("entry")
    if not isinstance(entries, list):
        return out
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        changes = entry.get("changes")
        if not isinstance(changes, list):
            continue
        for change in changes:
            if not isinstance(change, dict):
                continue
            value = change.get("value") if isinstance(change.get("value"), dict) else {}
            messages = value.get("messages")
            if not isinstance(messages, list):
                continue
            contacts = value.get("contacts") if isinstance(value.get("contacts"), list) else []
            contact0 = contacts[0] if contacts and isinstance(contacts[0], dict) else {}
            profile = contact0.get("profile") if isinstance(contact0.get("profile"), dict) else {}
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                text_obj = msg.get("text") if isinstance(msg.get("text"), dict) else {}
                body = str(text_obj.get("body") or "").strip()
                if not body:
                    continue
                out.append(
                    {
                        "channel_type": "whatsapp",
                        "external_message_id": str(msg.get("id") or ""),
                        "external_user_id": str(msg.get("from") or ""),
                        "conversation_external_id": str(msg.get("from") or ""),
                        "text": body,
                        "sender_name": str(profile.get("name") or "").strip(),
                        "phone_number_id": str(
                            (value.get("metadata") or {}).get("phone_number_id")
                            if isinstance(value.get("metadata"), dict)
                            else ""
                        ),
                        "waba_id": str(entry.get("id") or ""),
                    }
                )
    return out
