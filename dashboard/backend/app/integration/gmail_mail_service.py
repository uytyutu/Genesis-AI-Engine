"""Gmail API — one-time OAuth + send via refresh token (no re-login)."""

from __future__ import annotations

import base64
import logging
import os
import secrets
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any
from urllib.parse import urlencode

import httpx

logger = logging.getLogger("genesis.gmail")

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_SEND_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
_SCOPES = ("https://www.googleapis.com/auth/gmail.send",)

# Short-lived CSRF state for local OAuth (CEO localhost only).
_oauth_states: dict[str, float] = {}
_STATE_TTL_SEC = 600


def _client_id() -> str:
    return os.getenv("GMAIL_CLIENT_ID", "").strip()


def _client_secret() -> str:
    return os.getenv("GMAIL_CLIENT_SECRET", "").strip()


def _refresh_token() -> str:
    return os.getenv("GMAIL_REFRESH_TOKEN", "").strip()


def _sender() -> str:
    return (
        os.getenv("GMAIL_SENDER", "").strip()
        or os.getenv("GENESIS_EMAIL_FROM", "").strip()
    )


def oauth_client_ready() -> bool:
    return bool(_client_id() and _client_secret())


def send_ready() -> bool:
    return bool(_refresh_token() and _client_id() and _client_secret() and _sender())


def default_redirect_uri(public_api_base: str) -> str:
    override = os.getenv("GMAIL_REDIRECT_URI", "").strip()
    if override:
        return override
    base = public_api_base.rstrip("/")
    return f"{base}/api/owner/gmail/oauth/callback"


def status(*, public_api_base: str = "") -> dict[str, Any]:
    redirect = default_redirect_uri(public_api_base) if public_api_base else ""
    return {
        "oauth_client_ready": oauth_client_ready(),
        "send_ready": send_ready(),
        "has_refresh_token": bool(_refresh_token()),
        "sender": _sender() or None,
        "redirect_uri": redirect or None,
        "scopes": list(_SCOPES),
        "note": (
            "Open /api/owner/gmail → Connect Gmail (localhost only). "
            "Register redirect_uri in Google Cloud Console → OAuth client."
        ),
    }


def create_oauth_state() -> str:
    now = time.time()
    expired = [k for k, ts in _oauth_states.items() if now - ts > _STATE_TTL_SEC]
    for k in expired:
        _oauth_states.pop(k, None)
    state = secrets.token_urlsafe(24)
    _oauth_states[state] = now
    return state


def consume_oauth_state(state: str) -> bool:
    ts = _oauth_states.pop(state or "", None)
    if ts is None:
        return False
    return (time.time() - ts) <= _STATE_TTL_SEC


def authorization_url(*, redirect_uri: str, state: str) -> str:
    if not oauth_client_ready():
        raise ValueError("gmail_oauth_not_configured")
    params = {
        "client_id": _client_id(),
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code(*, code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange authorization code for tokens. Returns refresh_token when Google issues one."""
    if not oauth_client_ready():
        return {"ok": False, "reason": "gmail_oauth_not_configured"}
    if not (code or "").strip():
        return {"ok": False, "reason": "missing_code"}
    with httpx.Client(timeout=30.0) as client:
        res = client.post(
            _TOKEN_URL,
            data={
                "code": code.strip(),
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code >= 400:
        logger.warning("gmail oauth token exchange failed status=%s", res.status_code)
        return {
            "ok": False,
            "reason": f"token_error:{res.status_code}",
            "detail": (res.text or "")[:240],
        }
    data = res.json() if res.content else {}
    refresh = str(data.get("refresh_token") or "").strip()
    access = str(data.get("access_token") or "").strip()
    if not access:
        return {"ok": False, "reason": "no_access_token"}
    return {
        "ok": True,
        "refresh_token": refresh or None,
        "access_token_present": True,
        "expires_in": data.get("expires_in"),
        "scope": data.get("scope"),
        "token_type": data.get("token_type"),
        "hint": (
            None
            if refresh
            else "Google did not return refresh_token. Revoke app access at "
            "https://myaccount.google.com/permissions then Connect again with prompt=consent."
        ),
    }


def access_token_from_refresh() -> dict[str, Any]:
    if not send_ready() and not (_refresh_token() and oauth_client_ready()):
        return {"ok": False, "reason": "gmail_not_configured"}
    if not _refresh_token():
        return {"ok": False, "reason": "missing_refresh_token"}
    with httpx.Client(timeout=30.0) as client:
        res = client.post(
            _TOKEN_URL,
            data={
                "client_id": _client_id(),
                "client_secret": _client_secret(),
                "refresh_token": _refresh_token(),
                "grant_type": "refresh_token",
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
    if res.status_code >= 400:
        logger.warning("gmail refresh failed status=%s", res.status_code)
        return {
            "ok": False,
            "reason": f"refresh_error:{res.status_code}",
            "detail": (res.text or "")[:240],
        }
    data = res.json() if res.content else {}
    token = str(data.get("access_token") or "").strip()
    if not token:
        return {"ok": False, "reason": "no_access_token"}
    return {"ok": True, "access_token": token}


def _build_raw_message(
    *,
    to: str,
    subject: str,
    text: str,
    html: str = "",
    from_addr: str,
    list_unsubscribe: str = "",
) -> str:
    if html.strip():
        msg: MIMEMultipart | MIMEText = MIMEMultipart("alternative")
        msg.attach(MIMEText(text, "plain", "utf-8"))
        msg.attach(MIMEText(html, "html", "utf-8"))
    else:
        msg = MIMEText(text, "plain", "utf-8")
    msg["To"] = to
    msg["From"] = from_addr
    msg["Subject"] = subject
    if list_unsubscribe.strip():
        msg["List-Unsubscribe"] = list_unsubscribe.strip()
    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii").rstrip("=")
    return raw


def send_email(
    *,
    to: str,
    subject: str,
    text: str,
    html: str = "",
    from_addr: str | None = None,  # noqa: ARG001 — Resend From ignored; GMAIL_SENDER wins
    list_unsubscribe: str = "",
) -> dict[str, Any]:
    if not to:
        return {"ok": False, "skipped": True, "reason": "no_email"}
    sender = _sender()
    if not sender:
        return {"ok": False, "skipped": True, "reason": "gmail_sender_missing"}
    if not (_refresh_token() and oauth_client_ready()):
        return {"ok": False, "skipped": True, "reason": "gmail_not_configured"}
    # Gmail API From must be the authorized mailbox (GMAIL_SENDER), not Resend From.

    tok = access_token_from_refresh()
    if not tok.get("ok"):
        return {
            "ok": False,
            "skipped": False,
            "reason": tok.get("reason") or "gmail_token_failed",
            "detail": tok.get("detail"),
        }

    raw = _build_raw_message(
        to=to,
        subject=subject,
        text=text,
        html=html,
        from_addr=sender,
        list_unsubscribe=list_unsubscribe,
    )
    try:
        with httpx.Client(timeout=30.0) as client:
            res = client.post(
                _SEND_URL,
                json={"raw": raw},
                headers={"Authorization": f"Bearer {tok['access_token']}"},
            )
    except httpx.HTTPError as exc:
        return {"ok": False, "reason": "network_error", "detail": str(exc)[:160]}

    if res.status_code >= 400:
        return {
            "ok": False,
            "skipped": False,
            "reason": f"gmail_error:{res.status_code}",
            "detail": (res.text or "")[:240],
        }
    data = res.json() if res.content else {}
    return {
        "ok": True,
        "provider": "gmail",
        "from": sender,
        "id": data.get("id"),
    }
