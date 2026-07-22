"""R3.6.1 — PortalReadService (read-only; no API/UI/persistence)."""

from __future__ import annotations

from app.portal.asset import new_asset
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.edit_session import close_edit_session, new_edit_session
from app.portal.read_service import ENGINE_ID, PortalCatalog, PortalReadService


def _build_service() -> tuple[PortalReadService, dict]:
    client = new_client(display_name="EL3", primary_email="el3@example.com")
    website = website_for_client(client, product_id="prod-1", market_code="DE")
    deployment = new_deployment(
        website=website,
        artifact_id="art-1",
        status="active",
    )
    website = attach_deployment(website, deployment)
    asset_a = new_asset(website=website, asset_type="logo", artifact_ref="ref/logo")
    asset_b = new_asset(website=website, asset_type="image", artifact_ref="ref/img")
    open_session = new_edit_session(website=website)
    closed = close_edit_session(new_edit_session(website=website))

    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={website.website_id: website},
        deployments={deployment.deployment_id: deployment},
        assets={asset_a.asset_id: asset_a, asset_b.asset_id: asset_b},
        edit_sessions={
            open_session.session_id: open_session,
            closed.session_id: closed,
        },
    )
    ids = {
        "client_id": client.client_id,
        "website_id": website.website_id,
        "deployment_id": deployment.deployment_id,
        "open_session_id": open_session.session_id,
    }
    return PortalReadService(catalog), ids


def test_engine_id():
    assert ENGINE_ID == "portal_read_service_v1"


def test_get_client_and_website():
    svc, ids = _build_service()
    c = svc.get_client(ids["client_id"])
    w = svc.get_website(ids["website_id"])
    assert c is not None and c.client_id == ids["client_id"]
    assert w is not None and w.client_id == c.client_id
    assert svc.get_client("missing") is None
    assert svc.get_website("missing") is None


def test_get_current_deployment():
    svc, ids = _build_service()
    d = svc.get_current_deployment(ids["website_id"])
    assert d is not None
    assert d.deployment_id == ids["deployment_id"]
    assert d.website_id == ids["website_id"]
    assert svc.get_current_deployment("missing") is None


def test_get_assets():
    svc, ids = _build_service()
    assets = svc.get_assets(ids["website_id"])
    assert len(assets) == 2
    assert {a.asset_type for a in assets} == {"logo", "image"}
    assert svc.get_assets("missing") == ()


def test_get_open_edit_session():
    svc, ids = _build_service()
    s = svc.get_open_edit_session(ids["website_id"])
    assert s is not None
    assert s.session_id == ids["open_session_id"]
    assert s.status == "open"
    assert svc.get_open_edit_session("missing") is None


def test_read_service_has_no_write_methods():
    forbidden = {
        "save",
        "create",
        "update",
        "delete",
        "put",
        "write",
        "persist",
        "attach",
        "close",
    }
    names = {n for n in dir(PortalReadService) if not n.startswith("_")}
    assert not (names & forbidden)
    assert {"get_client", "get_website", "get_current_deployment", "get_assets", "get_open_edit_session"} <= names
