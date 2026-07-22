"""R4.2 — Session Infrastructure (+ login cookie integration)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.session import ENGINE_ID as SESSION_ENGINE, create_session, is_session_active
from app.portal.session_cookie import (
    DEFAULT_COOKIE_NAME,
    ENGINE_ID as COOKIE_ENGINE,
    SessionCookieFactory,
)
from app.portal.session_facade import ENGINE_ID as FACADE_ENGINE, SessionFacade
from app.portal.session_store import (
    ENGINE_ID as STORE_ENGINE,
    InMemorySessionStore,
)


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
        ready.account_id,
    )


def test_engine_ids():
    assert SESSION_ENGINE == "session_domain_v1"
    assert STORE_ENGINE == "session_store_v1"
    assert FACADE_ENGINE == "session_facade_v1"
    assert COOKIE_ENGINE == "session_cookie_v1"


def test_session_store_create_get_invalidate():
    store = InMemorySessionStore()
    facade = SessionFacade(store)
    session = facade.start_session("acc-1")
    assert session.account_id == "acc-1"
    assert len(session.session_id) >= 32
    assert facade.get_active_session(session.session_id) is not None
    assert facade.invalidate_session(session.session_id) is True
    assert facade.get_active_session(session.session_id) is None
    assert facade.invalidate_session(session.session_id) is False


def test_expired_session_not_active():
    past = datetime.now(timezone.utc) - timedelta(hours=2)
    session = create_session(
        "acc-1",
        ttl=timedelta(hours=1),
        now=past,
    )
    assert not is_session_active(session)


def test_cookie_httponly_defaults():
    factory = SessionCookieFactory(secure=False)
    spec = factory.build("sid-abc")
    assert spec.key == DEFAULT_COOKIE_NAME
    assert spec.value == "sid-abc"
    assert spec.httponly is True
    assert spec.secure is False
    assert spec.samesite == "lax"
    kwargs = spec.as_set_cookie_kwargs()
    assert kwargs["httponly"] is True


def test_login_sets_httponly_cookie_on_success():
    directory, secret, account_id = _ready_directory()
    store = InMemorySessionStore()
    clear_authentication_facade()
    app = FastAPI()
    register_portal_login(
        app,
        directory=directory,
        session_store=store,
        cookie_factory=SessionCookieFactory(secure=False),
    )
    http = TestClient(app)
    try:
        r = http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": secret},
        )
        assert r.status_code == 200
        assert r.json() == {"authenticated": True}
        assert DEFAULT_COOKIE_NAME in r.cookies
        sid = r.cookies[DEFAULT_COOKIE_NAME]
        saved = store.get(sid)
        assert saved is not None
        assert saved.account_id == account_id
        # Set-Cookie attributes
        set_cookie = r.headers.get("set-cookie", "").lower()
        assert "httponly" in set_cookie
        assert "samesite=lax" in set_cookie
    finally:
        clear_authentication_facade()


def test_login_failure_no_cookie():
    directory, _, _ = _ready_directory()
    clear_authentication_facade()
    app = FastAPI()
    register_portal_login(app, directory=directory)
    http = TestClient(app)
    try:
        r = http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": "wrong"},
        )
        assert r.status_code == 200
        assert r.json() == {"authenticated": False}
        assert DEFAULT_COOKIE_NAME not in r.cookies
        assert "set-cookie" not in {k.lower() for k in r.headers.keys()} or (
            DEFAULT_COOKIE_NAME not in r.headers.get("set-cookie", "")
        )
    finally:
        clear_authentication_facade()


def test_auth_domain_untouched_by_session():
    import ast
    from pathlib import Path

    import app.portal.authentication as auth_mod

    tree = ast.parse(Path(auth_mod.__file__).read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert "session" not in node.module
        if isinstance(node, ast.Import):
            for a in node.names:
                assert "session" not in a.name
