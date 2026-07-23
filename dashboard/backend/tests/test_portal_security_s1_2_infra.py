"""Security Gate S1.2 — infrastructure hardening (permanent regression tests).

Principle: every vulnerability becomes a permanent automated test.
"""

from __future__ import annotations

from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.session_cookie import SessionCookieFactory
from app.security_hardening import (
    DEFAULT_SECURITY_HEADERS,
    ENGINE_ID,
    apply_security_headers,
    check_rate_limit,
    csrf_posture,
    portal_path_should_rate_limit,
    portal_rate_limit_per_min,
)


def test_engine_id():
    assert ENGINE_ID == "security_hardening_s1_2_v1"


def test_security_headers_applied_on_response():
    app = FastAPI()

    @app.middleware("http")
    async def headers_mw(request: Request, call_next):
        response = await call_next(request)
        return apply_security_headers(response)

    @app.get("/health")
    def health():
        return {"ok": True}

    http = TestClient(app)
    res = http.get("/health")
    assert res.status_code == 200
    for key, value in DEFAULT_SECURITY_HEADERS.items():
        assert res.headers.get(key) == value


def test_portal_rate_limit_bucket_returns_429(monkeypatch):
    monkeypatch.setenv("GENESIS_PORTAL_RATE_LIMIT_PER_MIN", "5")
    assert portal_rate_limit_per_min() == 5
    assert portal_path_should_rate_limit("/portal/login")
    assert not portal_path_should_rate_limit("/api/public/chat")

    app = FastAPI()
    app.state._portal_rate_buckets = defaultdict(list)
    limit = 5

    @app.middleware("http")
    async def portal_rl(request: Request, call_next):
        from app.security_hardening import rate_limit_key, rate_limited_response

        if portal_path_should_rate_limit(request.url.path):
            ok = check_rate_limit(
                app.state._portal_rate_buckets,
                key=rate_limit_key(request),
                limit=limit,
                window_sec=60.0,
            )
            if not ok:
                return rate_limited_response()
        return await call_next(request)

    @app.get("/portal/ping")
    def ping():
        return {"ok": True}

    http = TestClient(app)
    codes = [http.get("/portal/ping").status_code for _ in range(limit + 2)]
    assert codes.count(200) == limit
    assert 429 in codes


def test_csrf_posture_requires_httponly_samesite_lax():
    posture = csrf_posture()
    assert posture["session_cookie_httponly"] is True
    assert posture["session_cookie_samesite_default"] == "lax"
    assert posture["cross_site_post_cookie"] == "blocked_by_samesite_lax"

    spec = SessionCookieFactory(secure=False).build("sess-test")
    assert spec.httponly is True
    assert spec.samesite == "lax"


def test_cors_never_wildcard_with_credentials():
    from app.security_hardening import cors_allow_origins, cors_credentials_safe

    origins = cors_allow_origins(extra_csv="https://app.example, * ,https://b.example")
    assert "*" not in origins
    assert "http://localhost:3000" in origins
    assert "https://app.example" in origins
    assert cors_credentials_safe(origins, allow_credentials=True)
    assert not cors_credentials_safe(["*"], allow_credentials=True)


def test_hsts_only_in_production():
    from fastapi.responses import JSONResponse

    from app.security_hardening import apply_security_headers

    dev = apply_security_headers(JSONResponse({"ok": True}), production=False)
    assert "Strict-Transport-Security" not in dev.headers

    prod = apply_security_headers(JSONResponse({"ok": True}), production=True)
    assert prod.headers.get("Strict-Transport-Security", "").startswith("max-age=")


def test_session_cookie_secure_defaults_in_production(monkeypatch):
    monkeypatch.delenv("PORTAL_COOKIE_SECURE", raising=False)
    monkeypatch.setenv("GENESIS_ENV", "production")
    # Re-read via factory after env set
    from app.portal.session_cookie import SessionCookieFactory

    prod = SessionCookieFactory().build("s1")
    assert prod.secure is True
    assert prod.httponly is True

    monkeypatch.setenv("GENESIS_ENV", "development")
    local = SessionCookieFactory().build("s2")
    assert local.secure is False

    monkeypatch.setenv("PORTAL_COOKIE_SECURE", "0")
    monkeypatch.setenv("GENESIS_ENV", "production")
    forced = SessionCookieFactory().build("s3")
    assert forced.secure is False
