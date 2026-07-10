"""Client session tokens — HMAC bearer (same pattern as owner_auth)."""

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

_TOKEN_TTL_SEC = 30 * 24 * 3600
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _secret() -> str:
    return (
        os.getenv("GENESIS_CLIENT_JWT_SECRET", "").strip()
        or os.getenv("GENESIS_OWNER_JWT_SECRET", "").strip()
    )


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, salt, digest = stored.split("$", 2)
    except ValueError:
        return False
    if algo != "pbkdf2_sha256":
        return False
    check = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    ).hex()
    return hmac.compare_digest(check, digest)


def validate_email(email: str) -> str:
    normalized = email.strip().lower()
    if not _EMAIL_RE.match(normalized):
        raise HTTPException(status_code=400, detail="invalid_email")
    return normalized


def issue_client_token(*, customer_id: str, email: str, ttl_sec: int = _TOKEN_TTL_SEC) -> str:
    secret = _secret()
    if not secret:
        raise RuntimeError("GENESIS_CLIENT_JWT_SECRET not configured")
    payload = {
        "sub": customer_id,
        "email": email,
        "scope": "client",
        "exp": int(time.time()) + ttl_sec,
        "iat": int(time.time()),
    }
    body = base64.urlsafe_b64encode(
        json.dumps(payload, separators=(",", ":")).encode()
    ).decode().rstrip("=")
    sig = hmac.new(secret.encode(), body.encode(), hashlib.sha256).hexdigest()
    return f"{body}.{sig}"


def decode_client_token(token: str) -> dict[str, Any] | None:
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
    if payload.get("scope") != "client":
        return None
    exp = int(payload.get("exp") or 0)
    if exp and time.time() > exp:
        return None
    return payload


def verify_client_bearer(request: Request) -> dict[str, Any] | None:
    auth = (request.headers.get("authorization") or "").strip()
    if not auth.lower().startswith("bearer "):
        return None
    token = auth[7:].strip()
    return decode_client_token(token)


def require_client(request: Request) -> dict[str, Any]:
    payload = verify_client_bearer(request)
    if not payload or not payload.get("sub"):
        raise HTTPException(status_code=401, detail="client_auth_required")
    return payload
