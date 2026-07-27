"""P0 — owner API must not accept proxied LAN/anonymous access."""

from __future__ import annotations

from unittest.mock import MagicMock

from app.integration.owner_auth import owner_access_allowed


def _request(*, host: str = "127.0.0.1", headers: dict[str, str] | None = None):
    req = MagicMock()
    req.client = MagicMock()
    req.client.host = host
    hdrs = headers or {}
    req.headers.get = lambda key, default="": hdrs.get(key.lower(), hdrs.get(key, default))
    return req


def test_loopback_direct_allowed(monkeypatch):
    monkeypatch.delenv("GENESIS_OWNER_JWT_SECRET", raising=False)
    monkeypatch.setenv("GENESIS_ENV", "development")
    assert owner_access_allowed(_request(host="127.0.0.1")) is True


def test_forwarded_without_bearer_denied(monkeypatch):
    monkeypatch.delenv("GENESIS_OWNER_JWT_SECRET", raising=False)
    monkeypatch.setenv("GENESIS_ENV", "development")
    req = _request(
        host="127.0.0.1",
        headers={"x-forwarded-for": "192.168.1.50"},
    )
    assert owner_access_allowed(req) is False


def test_x_real_ip_without_bearer_denied(monkeypatch):
    monkeypatch.delenv("GENESIS_OWNER_JWT_SECRET", raising=False)
    monkeypatch.setenv("GENESIS_ENV", "development")
    req = _request(
        host="127.0.0.1",
        headers={"x-real-ip": "192.168.1.50"},
    )
    assert owner_access_allowed(req) is False
