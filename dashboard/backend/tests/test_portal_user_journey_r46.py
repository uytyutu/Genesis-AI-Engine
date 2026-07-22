"""R4.6 — End-to-End User Journey (no new domain — orchestration proof)."""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.activation_token import activate_token, consume_token, new_activation_token
from app.portal.portal_authentication_middleware import (
    clear_portal_authentication_middleware,
    register_portal_authentication_middleware,
)
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import clear_website_dashboard_facade
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.portal_user_journey import (
    ENGINE_ID,
    build_published_owner_journey,
)
from app.portal.session_cookie import DEFAULT_COOKIE_NAME, SessionCookieFactory
from app.portal.session_store import InMemorySessionStore


def _mount_journey_app(state):
    clear_authentication_facade()
    clear_portal_authentication_middleware()
    clear_website_dashboard_facade()
    store = InMemorySessionStore()
    app = FastAPI()
    register_portal_login(
        app,
        directory=state.auth_directory,
        session_store=store,
        cookie_factory=SessionCookieFactory(secure=False),
    )
    register_portal_authentication_middleware(app)
    register_portal_dashboard(
        app,
        catalog=state.catalog,
        ownerships=state.ownership_directory,
    )

    @app.get("/portal/_whoami")
    def whoami(request: Request):
        account = getattr(request.state, "account", None)
        return {"authenticated": account is not None}

    return TestClient(app), store


def test_engine_id():
    assert ENGINE_ID == "portal_user_journey_v1"


def test_full_user_journey_login_dashboard_logout():
    state = build_published_owner_journey()
    assert state.account.status == "ready"
    assert state.website.status == "published"
    assert state.ownership.account_id == state.account.account_id

    http, store = _mount_journey_app(state)
    website_id = state.website.website_id
    try:
        # Anonymous cannot open dashboard
        assert http.get(f"/portal/websites/{website_id}/dashboard").status_code == 401

        # Login → session cookie
        login = http.post(
            "/portal/login",
            json={"email": state.account.email, "password": state.password_material},
        )
        assert login.status_code == 200
        assert login.json() == {"authenticated": True}
        sid = login.cookies.get(DEFAULT_COOKIE_NAME)
        assert sid
        assert store.get(sid) is not None
        assert http.get("/portal/_whoami").json()["authenticated"] is True

        # Protected Dashboard
        dash = http.get(f"/portal/websites/{website_id}/dashboard")
        assert dash.status_code == 200
        body = dash.json()
        assert body["website"]["website_id"] == website_id
        assert body["current_deployment"] is not None

        # Logout → Anonymous
        assert http.post("/portal/logout").status_code == 204
        assert store.get(sid) is None
        assert http.get("/portal/_whoami").json()["authenticated"] is False
        assert http.get(f"/portal/websites/{website_id}/dashboard").status_code == 401
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()
        clear_website_dashboard_facade()


def test_journey_preserves_one_shot_activation_and_password_gate():
    from app.portal.account import new_account
    from app.portal.password_credential import (
        PasswordCredentialError,
        complete_account_activation,
        create_primary_password,
    )
    import pytest

    account = new_account(email="a@b.c", display_name="A")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    assert used.status == "used"
    with pytest.raises(Exception):
        consume_token(used)

    ready, cred = create_primary_password(
        activated,
        password_hash="x" * 12,
        activation_token=used,
    )
    assert ready.status == "ready"
    with pytest.raises(PasswordCredentialError, match="already set"):
        create_primary_password(
            ready,
            password_hash="y" * 12,
            activation_token=used,
            existing=cred,
        )


def test_journey_module_adds_no_new_auth_rules():
    """R4.6 must not redefine AuthN/AuthZ — only import composers."""
    import ast
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[1]
        / "app"
        / "portal"
        / "portal_user_journey.py"
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    }
    # Only orchestration surface
    assert "build_published_owner_journey" in defined
    assert "authenticate" not in defined
    assert "authorize" not in defined
    assert "PortalAuthenticationMiddleware" not in defined
