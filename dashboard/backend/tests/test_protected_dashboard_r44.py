"""R4.4 — Protected Dashboard (AuthN + Authorization + Dashboard)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.activation_token import activate_token, new_activation_token
from app.portal.authentication_facade import InMemoryAuthenticationDirectory
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.password_credential import (
    complete_account_activation,
    create_primary_password,
)
from app.portal.portal_authentication_middleware import (
    clear_portal_authentication_middleware,
    register_portal_authentication_middleware,
)
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import clear_website_dashboard_facade
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade
from app.portal.read_service import PortalCatalog
from app.portal.session_cookie import SessionCookieFactory
from app.portal.session_store import InMemorySessionStore


def _stack(*, with_ownership: bool = True):
    clear_authentication_facade()
    clear_portal_authentication_middleware()
    clear_website_dashboard_facade()

    account = new_account(email="owner@ex.de", display_name="Owner")
    token = activate_token(new_activation_token(account))
    activated, used = complete_account_activation(account, token)
    ready, cred = create_primary_password(
        activated,
        password_hash="secret-1",
        activation_token=used,
    )
    client = new_client(display_name="Co", primary_email="c@co.de")
    site = website_for_client(client, product_id="p1", market_code="DE")
    dep = new_deployment(website=site, artifact_id="art-1", status="active")
    site = attach_deployment(site, dep)

    directory = InMemoryAuthenticationDirectory(
        accounts_by_email={ready.email: ready},
        credentials_by_account={ready.account_id: cred},
    )
    ownerships = InMemoryOwnershipDirectory()
    if with_ownership:
        ownerships.add(grant_website_ownership(ready, site))

    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={dep.deployment_id: dep},
        assets={},
        edit_sessions={},
    )

    app = FastAPI()
    register_portal_login(
        app,
        directory=directory,
        session_store=InMemorySessionStore(),
        cookie_factory=SessionCookieFactory(secure=False),
    )
    register_portal_authentication_middleware(app)
    register_portal_dashboard(app, catalog=catalog, ownerships=ownerships)
    return TestClient(app), site.website_id, "secret-1"


def test_anonymous_gets_401():
    http, website_id, _ = _stack()
    try:
        r = http.get(f"/portal/websites/{website_id}/dashboard")
        assert r.status_code == 401
        assert r.json()["detail"] == "unauthorized"
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()
        clear_website_dashboard_facade()


def test_authenticated_without_ownership_gets_403():
    http, website_id, secret = _stack(with_ownership=False)
    try:
        assert http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": secret},
        ).json()["authenticated"] is True
        r = http.get(f"/portal/websites/{website_id}/dashboard")
        assert r.status_code == 403
        assert r.json()["detail"] == "forbidden"
        assert "ownership" not in r.text.lower()
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()
        clear_website_dashboard_facade()


def test_authenticated_with_ownership_gets_200():
    http, website_id, secret = _stack(with_ownership=True)
    try:
        assert http.post(
            "/portal/login",
            json={"email": "owner@ex.de", "password": secret},
        ).json()["authenticated"] is True
        r = http.get(f"/portal/websites/{website_id}/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["website"]["website_id"] == website_id
        assert body["current_deployment"] is not None
    finally:
        clear_authentication_facade()
        clear_portal_authentication_middleware()
        clear_website_dashboard_facade()
