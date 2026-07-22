"""R4.3 — Authentication Middleware (identity only)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)
from app.portal.portal_authentication_middleware import (
    ENGINE_ID,
    clear_portal_authentication_middleware,
    register_portal_authentication_middleware,
)
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.request_principal import ANONYMOUS
from app.portal.session_cookie import DEFAULT_COOKIE_NAME, SessionCookieFactory
from app.portal.session_store import InMemorySessionStore


def _ready_directory(email: str = "owner@ex.de", secret: str = "opaque-secret-1"):
    account = new_account(email=email, display_name="Owner")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash=secret,
        activation_token=used,
    )
    return (
        InMemoryAuthenticationDirectory(
            accounts_by_email={ready.email: ready},
            credentials_by_account={ready.account_id: cred},
        ),
        secret,
        ready,
    )


def _app_with_probe(directory, store=None):
    clear_authentication_facade()
    clear_portal_authentication_middleware()
    app = FastAPI()
    register_portal_login(
        app,
        directory=directory,
        session_store=store or InMemorySessionStore(),
        cookie_factory=SessionCookieFactory(secure=False),
    )
    register_portal_authentication_middleware(app)

    @app.get("/portal/_whoami")
    def whoami(request: Request):
        principal = getattr(request.state, "portal_principal", None)
        account = getattr(request.state, "account", "MISSING")
        return {
            "authenticated": bool(principal and principal.is_authenticated),
            "account_id": None if account is None else getattr(account, "account_id", None),
            "status_code_hint": "middleware_never_blocks",
        }

    return app


def test_engine_id():
    assert ENGINE_ID == "portal_authentication_middleware_v1"
    assert ANONYMOUS.account is None
    assert ANONYMOUS.is_authenticated is False


def test_no_cookie_is_anonymous_200():
    directory, _, _ = _ready_directory()
    http = TestClient(_app_with_probe(directory))
    try:
        r = http.get("/portal/_whoami")
        assert r.status_code == 200
        assert r.json() == {
            "authenticated": False,
            "account_id": None,
            "status_code_hint": "middleware_never_blocks",
        }
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()


def test_invalid_cookie_is_anonymous_200():
    directory, _, _ = _ready_directory()
    http = TestClient(_app_with_probe(directory))
    try:
        http.cookies.set(DEFAULT_COOKIE_NAME, "not-a-real-session")
        r = http.get("/portal/_whoami")
        assert r.status_code == 200
        assert r.json()["authenticated"] is False
        assert r.json()["account_id"] is None
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()


def test_login_then_whoami_sees_account():
    directory, secret, ready = _ready_directory()
    http = TestClient(_app_with_probe(directory))
    try:
        login = http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": secret},
        )
        assert login.status_code == 200
        assert login.json()["authenticated"] is True
        r = http.get("/portal/_whoami")
        assert r.status_code == 200
        body = r.json()
        assert body["authenticated"] is True
        assert body["account_id"] == ready.account_id
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()


def test_middleware_does_not_authorize_or_redirect():
    import ast

    path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "portal_authentication_middleware.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "authorization" not in node.module
            assert node.module != "app.portal.authorization"
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            continue
        if isinstance(node, ast.Constant) and node.value in (401, 403):
            raise AssertionError("middleware must not use 401/403")
    src = path.read_text(encoding="utf-8")
    assert "RedirectResponse" not in src
    assert "HTTPException" not in src


def test_main_registers_middleware():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_authentication_middleware(app)" in text
