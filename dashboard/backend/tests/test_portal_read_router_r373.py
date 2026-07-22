"""R3.7.3 — FastAPI Portal Read Router (unmounted; handlers only)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.asset import new_asset
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.edit_session import new_edit_session
from app.portal.portal_read_router import (
    ENGINE_ID,
    clear_portal_read_handlers,
    portal_read_router,
    set_portal_read_handlers,
)
from app.portal.read_api_handlers import PortalReadHandlers
from app.portal.read_service import PortalCatalog, PortalReadService


def _client() -> tuple[TestClient, dict]:
    clear_portal_read_handlers()
    owner = new_client(display_name="EL3", primary_email="el3@example.com")
    website = website_for_client(owner, product_id="prod-1", market_code="DE")
    deployment = new_deployment(website=website, artifact_id="art-1", status="active")
    website = attach_deployment(website, deployment)
    logo = new_asset(website=website, asset_type="logo", artifact_ref="ref/logo")
    session = new_edit_session(website=website)
    catalog = PortalCatalog(
        clients={owner.client_id: owner},
        websites={website.website_id: website},
        deployments={deployment.deployment_id: deployment},
        assets={logo.asset_id: logo},
        edit_sessions={session.session_id: session},
    )
    set_portal_read_handlers(PortalReadHandlers(PortalReadService(catalog)))
    app = FastAPI()
    app.include_router(portal_read_router)
    ids = {
        "client_id": owner.client_id,
        "website_id": website.website_id,
        "deployment_id": deployment.deployment_id,
        "session_id": session.session_id,
    }
    return TestClient(app), ids


def test_engine_id():
    assert ENGINE_ID == "portal_read_router_v1"


def test_only_get_routes():
    methods = {tuple(r.methods) for r in portal_read_router.routes if hasattr(r, "methods")}
    assert methods == {("GET",)} or all(m == {"GET"} for m in methods)


def test_get_endpoints_happy_path():
    client, ids = _client()
    try:
        r = client.get(f"/portal/clients/{ids['client_id']}")
        assert r.status_code == 200
        assert r.json()["client_id"] == ids["client_id"]

        r = client.get(f"/portal/websites/{ids['website_id']}")
        assert r.status_code == 200
        assert r.json()["website_id"] == ids["website_id"]

        r = client.get(f"/portal/websites/{ids['website_id']}/deployment")
        assert r.status_code == 200
        assert r.json()["deployment_id"] == ids["deployment_id"]

        r = client.get(f"/portal/websites/{ids['website_id']}/assets")
        assert r.status_code == 200
        assert isinstance(r.json(), list) and len(r.json()) == 1

        r = client.get(f"/portal/websites/{ids['website_id']}/edit-session")
        assert r.status_code == 200
        assert r.json()["session_id"] == ids["session_id"]
    finally:
        clear_portal_read_handlers()


def test_missing_maps_to_404_at_http_layer():
    client, _ = _client()
    try:
        assert client.get("/portal/clients/missing").status_code == 404
        assert client.get("/portal/websites/missing").status_code == 404
        assert client.get("/portal/websites/missing/deployment").status_code == 404
        assert client.get("/portal/websites/missing/edit-session").status_code == 404
        # assets: empty list is a valid read (handler does not invent 404)
        assert client.get("/portal/websites/missing/assets").status_code == 200
        assert client.get("/portal/websites/missing/assets").json() == []
    finally:
        clear_portal_read_handlers()


def test_router_not_in_main():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "portal_read_router" not in text
    assert "set_portal_read_handlers" not in text


def test_unconfigured_handlers_return_503():
    clear_portal_read_handlers()
    app = FastAPI()
    app.include_router(portal_read_router)
    client = TestClient(app)
    assert client.get("/portal/clients/x").status_code == 503
