"""Foundation F6 — owner auth skeleton (localhost + optional HMAC bearer).

Full JWT library not required for Mission 1. When ``GENESIS_OWNER_JWT_SECRET`` is set,
a valid ``Authorization: Bearer <token>`` allows owner API from non-localhost (staging).

Production: owner API remains blocked unless explicitly configured for remote CEO access.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from typing import Any

from fastapi import Request

from app.config import is_production
from app.security import local_owner_access_allowed

_TOKEN_TTL_SEC = 12 * 3600


def _secret() -> str:
    return os.getenv("GENESIS_OWNER_JWT_SECRET", "").strip()


def _client_host(request: Request) -> str:
    client = request.client
    return (client.host if client else "") or ""


def issue_owner_token(*, subject: str = "owner", ttl_sec: int = _TOKEN_TTL_SEC) -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError("GENESIS_OWNER_JWT_SECRET not configured")
    payload = {
        "sub": subject,
        "exp": int(time.time()) + ttl_sec,
        "iat": int(time.time()),
    }
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def _decode_token(token: str) -> dict[str, Any] | None:
    secret = _secret()
    if not secret or "." not in token:
        return None
    body, sig = token.rsplit(".", 1)
    expected = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, sig):
        return None
    pad = "=" * (-len(body) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(body + pad))
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(payload, dict):
        return None
    exp = int(payload.get("exp") or 0)
    if exp and time.time() > exp:
        return None
    return payload


def verify_owner_bearer(request: Request) -> bool:
    if not _secret():
        return False
    auth = (request.headers.get("authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        return False
    token = auth[7:].strip()
    return _decode_token(token) is not None


def owner_access_allowed(request: Request) -> bool:
    """Owner endpoints: localhost (dev) or valid bearer when secret configured."""
    if local_owner_access_allowed(request):
        return True
    if is_production() and os.getenv("GENESIS_OWNER_REMOTE", "").strip().lower() not in (
        "1",
        "true",
        "yes",
    ):
        return False
    return verify_owner_bearer(request)


def remote_owner_enabled() -> bool:
    return bool(_secret()) and (
        not is_production()
        or os.getenv("GENESIS_OWNER_REMOTE", "").strip().lower() in ("1", "true", "yes")
    )
