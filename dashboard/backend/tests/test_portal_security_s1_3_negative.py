"""S1.3 — Negative testing (must fail closed)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from starlette.requests import Request as StarletteRequest

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.billing_store import InMemoryBillingStore
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)
from app.portal.portal_authentication_middleware import (
    clear_portal_authentication_middleware,
    configure_portal_authentication_middleware,
    resolve_request_principal,
)
from app.portal.portal_billing_registration import register_portal_billing
from app.portal.portal_billing_router import clear_billing_facade
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.session import create_session, is_session_active
from app.portal.session_cookie import SessionCookieFactory
from app.portal.session_facade import SessionFacade
from app.portal.session_store import InMemorySessionStore


def test_nonexistent_billing_id_is_404():
    clear_billing_facade()
    account = new_account(email="neg@s13.test", display_name="Neg", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_billing(app, store=InMemoryBillingStore())
    http = TestClient(app)
    try:
        assert http.get("/portal/billing/does-not-exist").status_code == 404
    finally:
        clear_billing_facade()


def test_malformed_json_on_login_rejected():
    clear_authentication_facade()
    app = FastAPI()
    register_portal_login(
        app,
        directory=InMemoryAuthenticationDirectory(
            accounts_by_email={},
            credentials_by_account={},
        ),
        session_store=InMemorySessionStore(),
        cookie_factory=SessionCookieFactory(secure=False),
    )
    http = TestClient(app)
    try:
        res = http.post(
            "/portal/login",
            content="{not-json",
            headers={"Content-Type": "application/json"},
        )
        assert res.status_code in {400, 422}
    finally:
        clear_authentication_facade()


def test_wrong_http_method_on_billing_list():
    clear_billing_facade()
    account = new_account(email="m@s13.test", display_name="M", status="ready")
    app = FastAPI()

    @app.middleware("http")
    async def inject(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_billing(app, store=InMemoryBillingStore())
    http = TestClient(app)
    try:
        assert http.post("/portal/billing").status_code == 405
        assert http.delete("/portal/billing").status_code == 405
    finally:
        clear_billing_facade()


def test_oversized_and_empty_login_fields():
    clear_authentication_facade()
    account = new_account(
        email="ready@s13.test", display_name="R", status="pending_activation"
    )
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated, password_hash="secret-ok", activation_token=used
    )
    directory = InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: cred},
    )
    app = FastAPI()
    register_portal_login(
        app,
        directory=directory,
        session_store=InMemorySessionStore(),
        cookie_factory=SessionCookieFactory(secure=False),
    )
    http = TestClient(app)
    try:
        empty = http.post("/portal/login", json={"email": "", "password": ""})
        assert empty.status_code in {200, 400, 401, 422}
        if empty.status_code == 200:
            assert empty.json().get("authenticated") is False
        huge = http.post(
            "/portal/login",
            json={"email": ("a" * 5000) + "@x.test", "password": "p" * 5000},
        )
        assert huge.status_code in {200, 400, 401, 422}
        if huge.status_code == 200:
            assert huge.json().get("authenticated") is False
        bad = http.post(
            "/portal/login",
            json={"email": ready.email, "password": "wrong-password"},
        )
        assert bad.status_code == 200
        assert bad.json().get("authenticated") is False
    finally:
        clear_authentication_facade()


def test_expired_session_not_active():
    past = datetime.now(timezone.utc) - timedelta(hours=3)
    session = create_session("acc-neg", ttl=timedelta(hours=1), now=past)
    assert not is_session_active(session)


def test_empty_session_cookie_is_anonymous_principal():
    clear_portal_authentication_middleware()
    store = InMemorySessionStore()
    facade = SessionFacade(store)
    directory = InMemoryAuthenticationDirectory(
        accounts_by_email={},
        credentials_by_account={},
    )
    configure_portal_authentication_middleware(
        session_facade=facade, directory=directory
    )
    try:
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": [],
            "client": ("127.0.0.1", 123),
            "server": ("test", 80),
        }
        request = StarletteRequest(scope)
        principal = resolve_request_principal(request)
        assert principal.account is None
    finally:
        clear_portal_authentication_middleware()
