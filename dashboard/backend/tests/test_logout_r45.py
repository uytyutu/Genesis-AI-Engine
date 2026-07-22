"""R4.5 — Logout (invalidate session + clear cookie)."""

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
    clear_portal_authentication_middleware,
    register_portal_authentication_middleware,
)
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.session_cookie import DEFAULT_COOKIE_NAME, SessionCookieFactory
from app.portal.session_store import InMemorySessionStore


def _app():
    clear_authentication_facade()
    clear_portal_authentication_middleware()
    account = new_account(email="owner@ex.de", display_name="Owner")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash="secret-1",
        activation_token=used,
    )
    directory = InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: cred},
    )
    store = InMemorySessionStore()
    app = FastAPI()
    register_portal_login(
        app,
        directory=directory,
        session_store=store,
        cookie_factory=SessionCookieFactory(secure=False),
    )
    register_portal_authentication_middleware(app)

    @app.get("/portal/_whoami")
    def whoami(request: Request):
        account = getattr(request.state, "account", None)
        return {
            "authenticated": account is not None,
            "account_id": None if account is None else account.account_id,
        }

    return TestClient(app), store, ready.account_id


def test_logout_after_login_clears_session():
    http, store, _account_id = _app()
    try:
        login = http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": "secret-1"},
        )
        assert login.status_code == 200
        assert login.json()["authenticated"] is True
        sid = login.cookies.get(DEFAULT_COOKIE_NAME)
        assert sid
        assert store.get(sid) is not None
        assert http.get("/portal/_whoami").json()["authenticated"] is True

        out = http.post("/portal/logout")
        assert out.status_code == 204
        assert store.get(sid) is None
        assert http.get("/portal/_whoami").json()["authenticated"] is False
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()


def test_logout_idempotent():
    http, _, _ = _app()
    try:
        assert http.post("/portal/logout").status_code == 204
        assert http.post("/portal/logout").status_code == 204
        http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": "secret-1"},
        )
        assert http.post("/portal/logout").status_code == 204
        assert http.post("/portal/logout").status_code == 204
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()


def test_logout_uses_session_facade_not_store():
    router = (
        Path(__file__).resolve().parents[1] / "app" / "portal" / "portal_login_router.py"
    )
    src = router.read_text(encoding="utf-8")
    assert "invalidate_session" in src
    assert "InMemorySessionStore" not in src
