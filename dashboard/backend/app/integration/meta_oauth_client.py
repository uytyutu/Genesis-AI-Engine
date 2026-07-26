"""Meta (Facebook / Instagram / WhatsApp) OAuth client for AI Business Bot channels.

Env:
  META_APP_ID
  META_APP_SECRET
  META_REDIRECT_URI (default http://127.0.0.1:8000/api/client/bots/meta/oauth/callback)

Never logs tokens or app secret.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

from app.integration.workspace_channel_credentials import save_channel_record

logger = logging.getLogger(__name__)

_DEFAULT_REDIRECT = "http://127.0.0.1:8000/api/client/bots/meta/oauth/callback"

# Best-effort scope list for Pages + Instagram messaging.
_META_SCOPES = (
    "pages_show_list",
    "pages_messaging",
    "pages_manage_metadata",
    "instagram_basic",
    "instagram_manage_messages",
)

_FACEBOOK_DIALOG = "https://www.facebook.com/v21.0/dialog/oauth"
_TOKEN_URL = "https://graph.facebook.com/v21.0/oauth/access_token"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or "").strip()


def _state_secret() -> str:
    return (
        _env("META_APP_SECRET")
        or _env("GENESIS_CLIENT_JWT_SECRET")
        or _env("GENESIS_OWNER_JWT_SECRET")
        or "virtus-meta-oauth-dev"
    )


def meta_oauth_configured() -> bool:
    return bool(_env("META_APP_ID") and _env("META_APP_SECRET"))


def _not_configured() -> dict[str, Any]:
    return {"ok": False, "reason": "meta_not_configured"}


def encode_oauth_state(
    *,
    customer_id: str,
    bot_id: str,
    channel: str,
) -> str:
    """Signed state for OAuth round-trip (no secrets)."""
    nonce = secrets.token_hex(8)
    payload = f"{customer_id}|{bot_id}|{channel}|{nonce}"
    sig = hmac.new(
        _state_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    raw = f"{payload}|{sig}".encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def decode_oauth_state(state: str) -> dict[str, Any] | None:
    raw = str(state or "").strip()
    if not raw:
        return None
    pad = "=" * (-len(raw) % 4)
    try:
        text = base64.urlsafe_b64decode(raw + pad).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return None
    parts = text.split("|")
    if len(parts) != 5:
        return None
    customer_id, bot_id, channel, nonce, sig = parts
    payload = f"{customer_id}|{bot_id}|{channel}|{nonce}"
    expect = hmac.new(
        _state_secret().encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:20]
    if not hmac.compare_digest(expect, sig):
        return None
    return {
        "customer_id": customer_id,
        "bot_id": bot_id,
        "channel": channel,
        "nonce": nonce,
    }


def build_meta_oauth_url(state: str) -> str | dict[str, Any]:
    """Build Facebook OAuth dialog URL. Returns error dict if not configured."""
    if not meta_oauth_configured():
        return _not_configured()
    app_id = _env("META_APP_ID")
    redirect = _env("META_REDIRECT_URI", _DEFAULT_REDIRECT)
    st = str(state or "").strip()
    if not st:
        return {"ok": False, "reason": "state_required"}
    params = {
        "client_id": app_id,
        "redirect_uri": redirect,
        "state": st,
        "response_type": "code",
        "scope": ",".join(_META_SCOPES),
    }
    return f"{_FACEBOOK_DIALOG}?{urlencode(params)}"


def start_meta_oauth(
    *,
    customer_id: str,
    bot_id: str,
    channel: str = "facebook_messenger",
) -> dict[str, Any]:
    """Create signed state + authorize URL for Dashboard Connect."""
    if not meta_oauth_configured():
        return _not_configured()
    cid = str(customer_id or "").strip()
    bid = str(bot_id or "").strip()
    ch = str(channel or "facebook_messenger").strip().lower() or "facebook_messenger"
    if not cid:
        return {"ok": False, "reason": "customer_id_required"}
    if not bid:
        return {"ok": False, "reason": "bot_id_required"}
    state = encode_oauth_state(customer_id=cid, bot_id=bid, channel=ch)
    url = build_meta_oauth_url(state)
    if isinstance(url, dict):
        return url
    return {"ok": True, "authorize_url": url, "state": state, "configured": True}


def exchange_meta_code(code: str) -> dict[str, Any]:
    """Exchange OAuth authorization code for a user access token."""
    if not meta_oauth_configured():
        return _not_configured()

    raw_code = str(code or "").strip()
    if not raw_code:
        return {"ok": False, "reason": "code_empty"}

    app_id = _env("META_APP_ID")
    app_secret = _env("META_APP_SECRET")
    redirect = _env("META_REDIRECT_URI", _DEFAULT_REDIRECT)

    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(
                _TOKEN_URL,
                params={
                    "client_id": app_id,
                    "client_secret": app_secret,
                    "redirect_uri": redirect,
                    "code": raw_code,
                },
            )
    except httpx.HTTPError:
        logger.info("meta_token_exchange_network_error")
        return {"ok": False, "reason": "meta_network_error"}

    if resp.status_code != 200:
        logger.info("meta_token_exchange_http_error status=%s", resp.status_code)
        return {"ok": False, "reason": "meta_http_error", "http_status": resp.status_code}

    try:
        body = resp.json()
    except ValueError:
        return {"ok": False, "reason": "meta_invalid_response"}

    if not isinstance(body, dict):
        return {"ok": False, "reason": "meta_invalid_response"}

    access_token = str(body.get("access_token") or "").strip()
    if not access_token:
        err = body.get("error") if isinstance(body.get("error"), dict) else {}
        msg = str(err.get("message") or "")[:120]
        logger.info("meta_token_exchange_no_token detail=%s", msg)
        return {"ok": False, "reason": "meta_token_missing", "detail": msg or None}

    return {
        "ok": True,
        "access_token": access_token,
        "token_type": body.get("token_type"),
        "expires_in": body.get("expires_in"),
    }


def _infer_meta_channel(token_payload: dict[str, Any]) -> str:
    """Pick storage channel label from payload hints."""
    explicit = str(token_payload.get("channel") or "").strip().lower()
    if explicit in {"meta", "whatsapp", "instagram", "facebook_messenger"}:
        return explicit
    platform = str(token_payload.get("platform") or "").strip().lower()
    if platform in {"whatsapp", "wa"}:
        return "whatsapp"
    if platform in {"instagram", "ig"}:
        return "instagram"
    if platform in {"messenger", "facebook_messenger", "facebook", "fb"}:
        return "facebook_messenger"
    return "meta"


def save_meta_tokens(
    memory_dir: Path,
    customer_id: str,
    bot_id: str,
    token_payload: dict[str, Any],
) -> dict[str, Any]:
    """Persist Meta tokens via workspace_channel_credentials pattern."""
    if not meta_oauth_configured():
        return _not_configured()

    if not isinstance(token_payload, dict):
        return {"ok": False, "reason": "token_payload_required"}

    access_token = str(token_payload.get("access_token") or "").strip()
    if not access_token:
        return {"ok": False, "reason": "token_empty"}

    bid = str(bot_id or "").strip()
    if not bid:
        return {"ok": False, "reason": "bot_id_required"}

    cid = str(customer_id or "").strip()
    if not cid:
        return {"ok": False, "reason": "customer_id_required"}

    channel = _infer_meta_channel(token_payload)
    conn_id = str(token_payload.get("connection_id") or "").strip() or (
        f"meta-{uuid.uuid4().hex[:12]}"
    )
    now = _utc_now_iso()
    record: dict[str, Any] = {
        "connection_id": conn_id,
        "channel": channel,
        "meta_channel": channel,
        "bot_id": bid,
        "status": str(token_payload.get("status") or "online"),
        "access_token": access_token,
        "token_type": token_payload.get("token_type"),
        "expires_in": token_payload.get("expires_in"),
        "page_id": token_payload.get("page_id"),
        "page_name": token_payload.get("page_name"),
        "page_access_token": token_payload.get("page_access_token"),
        "updated_at": now,
        "created_at": now,
    }
    if not record.get("page_access_token"):
        record.pop("page_access_token", None)

    result = save_channel_record(memory_dir, cid, record)
    if result.get("ok"):
        logger.info(
            "meta_tokens_saved customer=%s bot=%s connection=%s channel=%s",
            cid,
            bid,
            conn_id,
            channel,
        )
    return result


def complete_meta_oauth_callback(
    memory_dir: Path,
    *,
    code: str,
    state: str,
) -> dict[str, Any]:
    """Validate state, exchange code, store tokens under Workspace."""
    parsed = decode_oauth_state(state)
    if not parsed:
        return {"ok": False, "reason": "invalid_state"}
    exchanged = exchange_meta_code(code)
    if not exchanged.get("ok"):
        return exchanged
    payload = {
        "access_token": exchanged["access_token"],
        "token_type": exchanged.get("token_type"),
        "expires_in": exchanged.get("expires_in"),
        "channel": parsed["channel"],
    }
    saved = save_meta_tokens(
        memory_dir,
        parsed["customer_id"],
        parsed["bot_id"],
        payload,
    )
    if not saved.get("ok"):
        return saved
    return {
        "ok": True,
        "customer_id": parsed["customer_id"],
        "bot_id": parsed["bot_id"],
        "channel": parsed["channel"],
        "connection": saved.get("connection"),
    }
