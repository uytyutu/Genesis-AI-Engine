"""Store buyer auth — separate from Virtus Core Client Identity.

Tokens use scope ``store_buyer`` and always carry ``order_id`` (shop scope).
Virtus ``client`` tokens must never authenticate here.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from typing import Any

from fastapi import HTTPException, Request

# Reuse password helpers from Virtus client auth (same algorithm, separate stores).
from app.integration.customer_identity.auth import hash_password, verify_password

_TOKEN_TTL_SEC = 30 * 24 * 3600
_RESET_TTL_SEC = 2 * 3600
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _secret() -> str:
    return (
        os.getenv("GENESIS_STORE_BUYER_JWT_SECRET", "").strip()
        or os.getenv("GENESIS_CLIENT_JWT_SECRET", "").strip()
        or os.getenv("GENESIS_OWNER_JWT_SECRET", "").strip()
    )


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise ValueError("invalid_email")
    return normalized


def issue_store_buyer_token(
    *,
    buyer_id: str,
    email: str,
    order_id: str,
    ttl_sec: int = _TOKEN_TTL_SEC,
) -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError("store_buyer_secret_not_configured")
    payload = {
        "sub": buyer_id,
        "email": email,
        "order_id": order_id,
        "scope": "store_buyer",
        "exp": int(time.time()) + ttl_sec,
        "iat": int(time.time()),
    }
    body = (
        base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode())
        .decode()
        .rstrip("=")
    )
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_store_buyer_token(token: str) -> dict[str, Any] | None:
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
    if payload.get("scope") != "store_buyer":
        return None
    exp = int(payload.get("exp") or 0)
    if exp and time.time() > exp:
        return None
    return payload


def require_store_buyer(request: Request, order_id: str) -> dict[str, Any]:
    auth = (request.headers.get("authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="store_buyer_auth_required")
    payload = decode_store_buyer_token(auth[7:].strip())
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="store_buyer_auth_required")
    if str(payload.get("order_id") or "") != str(order_id):
        raise HTTPException(status_code=403, detail="wrong_store")
    return payload


def make_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_reset_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


__all__ = [
    "hash_password",
    "verify_password",
    "validate_email",
    "issue_store_buyer_token",
    "decode_store_buyer_token",
    "require_store_buyer",
    "make_reset_token",
    "hash_reset_token",
    "_RESET_TTL_SEC",
]
