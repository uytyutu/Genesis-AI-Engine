"""R3.6.1 / R3.6.2 — PortalReadService + Query objects."""

from __future__ import annotations

from app.portal.asset import new_asset
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.edit_session import close_edit_session, new_edit_session
from app.portal.queries import AssetQuery, ClientQuery, WebsiteQuery
from app.portal.read_service import (
    ENGINE_ID,
    PortalCatalog,
    PortalCatalogView,
    PortalReadService,
)


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
    c = svc.get_client(ClientQuery(client_id=ids["client_id"]))
    w = svc.get_website(WebsiteQuery(website_id=ids["website_id"]))
    assert c is not None and c.client_id == ids["client_id"]
    assert w is not None and w.client_id == c.client_id
    assert svc.get_client(ClientQuery(client_id="missing")) is None
    assert svc.get_website(WebsiteQuery(website_id="missing")) is None


def test_get_current_deployment():
    svc, ids = _build_service()
    d = svc.get_current_deployment(WebsiteQuery(website_id=ids["website_id"]))
    assert d is not None
    assert d.deployment_id == ids["deployment_id"]
    assert d.website_id == ids["website_id"]
    assert svc.get_current_deployment(WebsiteQuery(website_id="missing")) is None


def test_get_assets():
    svc, ids = _build_service()
    assets = svc.get_assets(AssetQuery(website_id=ids["website_id"]))
    assert len(assets) == 2
    assert {a.asset_type for a in assets} == {"logo", "image"}
    assert svc.get_assets(AssetQuery(website_id="missing")) == ()


def test_get_open_edit_session():
    svc, ids = _build_service()
    s = svc.get_open_edit_session(WebsiteQuery(website_id=ids["website_id"]))
    assert s is not None
    assert s.session_id == ids["open_session_id"]
    assert s.status == "open"
    assert svc.get_open_edit_session(WebsiteQuery(website_id="missing")) is None


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
    assert {
        "get_client",
        "get_website",
        "get_current_deployment",
        "get_assets",
        "get_open_edit_session",
    } <= names


def test_catalog_is_protocol_view():
    svc, _ = _build_service()
    assert isinstance(svc._catalog, PortalCatalogView)


def test_asset_query_optional_type_filter():
    svc, ids = _build_service()
    logos = svc.get_assets(
        AssetQuery(website_id=ids["website_id"], asset_type="logo")
    )
    assert len(logos) == 1
    assert logos[0].asset_type == "logo"


def test_query_objects_have_no_behavior():
    for cls in (ClientQuery, WebsiteQuery, AssetQuery):
        methods = {
            n
            for n in dir(cls)
            if not n.startswith("_") and callable(getattr(cls, n, None))
        }
        # dataclasses may expose asdict-like helpers via inheritance — keep empty of domain verbs
        assert not methods & {"execute", "run", "fetch", "save", "validate"}
