"""R3.11.1 — Dashboard Read Endpoint (Facade only; Auth stub)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import (
    ENGINE_ID,
    clear_website_dashboard_facade,
    portal_dashboard_router,
)
from app.portal.read_service import PortalCatalog


def _app_with_site() -> tuple[TestClient, str]:
    clear_website_dashboard_facade()
    client = new_client(display_name="EL3", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    dep = new_deployment(website=site, artifact_id="art-1", status="active")
    site = attach_deployment(site, dep)
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={dep.deployment_id: dep},
        assets={},
        edit_sessions={},
    )
    app = FastAPI()
    assert register_portal_dashboard(app, catalog=catalog) is True
    return TestClient(app), site.website_id


def test_engine_id():
    assert ENGINE_ID == "portal_dashboard_router_v1"


def test_get_dashboard_happy_path():
    http, website_id = _app_with_site()
    try:
        r = http.get(f"/portal/websites/{website_id}/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["website"]["website_id"] == website_id
        assert body["status"] == body["website"]["status"]
        assert body["current_deployment"] is not None
        assert body["current_deployment"]["website_id"] == website_id
    finally:
        clear_website_dashboard_facade()


def test_get_dashboard_missing_404():
    http, _ = _app_with_site()
    try:
        assert http.get("/portal/websites/missing/dashboard").status_code == 404
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


def test_unconfigured_facade_503():
    clear_website_dashboard_facade()
    app = FastAPI()
    app.include_router(portal_dashboard_router)
    assert TestClient(app).get("/portal/websites/x/dashboard").status_code == 503
