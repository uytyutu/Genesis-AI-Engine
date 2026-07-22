"""R3.11.1 — Dashboard Read Endpoint (now protected by R4.4)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import (
    ENGINE_ID,
    clear_website_dashboard_facade,
    portal_dashboard_router,
)
from app.portal.read_service import PortalCatalog


def _catalog_with_site():
    client = new_client(display_name="EL3", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    dep = new_deployment(website=site, artifact_id="art-1", status="active")
    site = attach_deployment(site, dep)
    account = new_account(email="a@b.c", display_name="A", status="ready")
    ownerships = InMemoryOwnershipDirectory(
        ownerships=[grant_website_ownership(account, site)]
    )
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={dep.deployment_id: dep},
        assets={},
        edit_sessions={},
    )
    return catalog, ownerships, site.website_id, account


def test_engine_id():
    assert ENGINE_ID == "portal_dashboard_router_v1"


def test_anonymous_blocked_401():
    clear_website_dashboard_facade()
    catalog, ownerships, website_id, _ = _catalog_with_site()
    app = FastAPI()
    register_portal_dashboard(app, catalog=catalog, ownerships=ownerships)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/dashboard").status_code
            == 401
        )
    finally:
        clear_website_dashboard_facade()


def test_get_dashboard_happy_path_with_principal():
    clear_website_dashboard_facade()
    catalog, ownerships, website_id, account = _catalog_with_site()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_dashboard(app, catalog=catalog, ownerships=ownerships)
    http = TestClient(app)
    try:
        r = http.get(f"/portal/websites/{website_id}/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["website"]["website_id"] == website_id
        assert body["current_deployment"] is not None
    finally:
        clear_website_dashboard_facade()


def test_get_dashboard_missing_404_when_authorized():
    clear_website_dashboard_facade()
    catalog, ownerships, _, account = _catalog_with_site()
    # Grant ownership on a website_id that is not in catalog
    from app.portal.website import new_website

    ghost = new_website(client_id="c", product_id="ghost", market_code="DE")
    ownerships.add(grant_website_ownership(account, ghost))
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_dashboard(app, catalog=catalog, ownerships=ownerships)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{ghost.website_id}/dashboard").status_code
            == 404
        )
    finally:
        clear_website_dashboard_facade()


def test_router_only_get_dashboard():
    paths = [
        getattr(route, "path", "")
        for route in portal_dashboard_router.routes
        if hasattr(route, "methods")
    ]
    assert any(p.endswith("/websites/{website_id}/dashboard") for p in paths)
    for route in portal_dashboard_router.routes:
        if hasattr(route, "methods"):
            assert route.methods == {"GET"}


def test_main_registers_dashboard():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_dashboard(app)" in text
    assert "include_router(portal_dashboard_router)" not in text


def test_unconfigured_authz_503_when_authenticated():
    clear_website_dashboard_facade()
    account = new_account(email="a@b.c", display_name="A", status="ready")
    app = FastAPI()
    app.include_router(portal_dashboard_router)

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    # authz facade unset → 503
    assert TestClient(app).get("/portal/websites/x/dashboard").status_code == 503
