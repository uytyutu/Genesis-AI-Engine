"""Seal TikTok OAuth tokens at rest (stdlib only — no raw tokens in API responses)."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
from typing import Any


_PREFIX = "hz1"


def _secret_material() -> bytes:
    raw = (
        os.getenv("TIKTOK_TOKEN_SECRET", "").strip()
        or os.getenv("GENESIS_OWNER_JWT_SECRET", "").strip()
        or "virtus-horizon-dev-only-change-me"
    )
    return hashlib.sha256(raw.encode("utf-8")).digest()


def seal_secret(plaintext: str) -> str:
    """Encrypt+MAC a token string for disk storage."""
    if not plaintext:
        return ""
    key = _secret_material()
    nonce = secrets.token_bytes(16)
    data = plaintext.encode("utf-8")
    # Keystream from HMAC-SHA256(key, nonce || counter)
    out = bytearray()
    counter = 0
    while len(out) < len(data):
        block = hmac.new(
            key,
            nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        out.extend(block)
        counter += 1
    cipher = bytes(a ^ b for a, b in zip(data, out[: len(data)]))
    mac = hmac.new(key, nonce + cipher, hashlib.sha256).digest()[:16]
    blob = nonce + mac + cipher
    return f"{_PREFIX}." + base64.urlsafe_b64encode(blob).decode("ascii").rstrip("=")


def unseal_secret(sealed: str) -> str:
    if not sealed:
        return ""
    if not sealed.startswith(f"{_PREFIX}."):
        # Legacy / test plaintext refused
        raise ValueError("invalid_sealed_token")
    raw = sealed.split(".", 1)[1]
    pad = "=" * (-len(raw) % 4)
    blob = base64.urlsafe_b64decode(raw + pad)
    if len(blob) < 33:
        raise ValueError("invalid_sealed_token")
    nonce, mac, cipher = blob[:16], blob[16:32], blob[32:]
    key = _secret_material()
    expected = hmac.new(key, nonce + cipher, hashlib.sha256).digest()[:16]
    if not hmac.compare_digest(mac, expected):
        raise ValueError("token_mac_mismatch")
    out = bytearray()
    counter = 0
    while len(out) < len(cipher):
        block = hmac.new(
            key,
            nonce + counter.to_bytes(4, "big"),
            hashlib.sha256,
        ).digest()
        out.extend(block)
        counter += 1
    plain = bytes(a ^ b for a, b in zip(cipher, out[: len(cipher)]))
    return plain.decode("utf-8")


def public_token_meta(row: dict[str, Any]) -> dict[str, Any]:
    """Safe fields for UI — never includes raw or sealed secrets."""
    return {
        "has_access_token": bool(row.get("access_token_sealed")),
        "has_refresh_token": bool(row.get("refresh_token_sealed")),
        "access_token_expires_at": row.get("access_token_expires_at"),
        "refresh_token_expires_at": row.get("refresh_token_expires_at"),
        "scopes": row.get("scopes") or [],
    }
