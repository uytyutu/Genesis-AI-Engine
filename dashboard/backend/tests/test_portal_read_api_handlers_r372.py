"""R3.7.2 — Portal Read API Handlers (Contract → ReadService → View)."""

from __future__ import annotations

from app.portal.asset import new_asset
from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.edit_session import new_edit_session
from app.portal.read_api_contract import (
    PORTAL_READ_ROUTES,
    ClientPath,
    WebsiteAssetsQuery,
    WebsitePath,
)
from app.portal.read_api_handlers import (
    ENGINE_ID,
    HANDLER_NAMES,
    PortalReadHandlers,
)
from app.portal.read_service import PortalCatalog, PortalReadService
from app.portal.views import (
    AssetView,
    ClientView,
    DeploymentView,
    EditSessionView,
    WebsiteView,
)


def _build_handlers() -> tuple[PortalReadHandlers, dict]:
    client = new_client(display_name="EL3", primary_email="el3@example.com")
    website = website_for_client(client, product_id="prod-1", market_code="DE")
    deployment = new_deployment(website=website, artifact_id="art-1", status="active")
    website = attach_deployment(website, deployment)
    logo = new_asset(website=website, asset_type="logo", artifact_ref="ref/logo")
    image = new_asset(website=website, asset_type="image", artifact_ref="ref/img")
    session = new_edit_session(website=website)
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={website.website_id: website},
        deployments={deployment.deployment_id: deployment},
        assets={logo.asset_id: logo, image.asset_id: image},
        edit_sessions={session.session_id: session},
    )
    ids = {
        "client_id": client.client_id,
        "website_id": website.website_id,
        "deployment_id": deployment.deployment_id,
        "session_id": session.session_id,
    }
    return PortalReadHandlers(PortalReadService(catalog)), ids


def test_engine_id():
    assert ENGINE_ID == "portal_read_api_handlers_v1"


def test_every_contract_route_has_handler():
    assert set(HANDLER_NAMES) == {r.name for r in PORTAL_READ_ROUTES}
    for name in HANDLER_NAMES:
        assert callable(getattr(PortalReadHandlers, name))


def test_handlers_return_views():
    h, ids = _build_handlers()
    assert isinstance(h.get_client(ClientPath(client_id=ids["client_id"])), ClientView)
    assert isinstance(
        h.get_website(WebsitePath(website_id=ids["website_id"])), WebsiteView
    )
    assert isinstance(
        h.get_current_deployment(WebsitePath(website_id=ids["website_id"])),
        DeploymentView,
    )
    assets = h.get_assets(WebsiteAssetsQuery(website_id=ids["website_id"]))
    assert assets and all(isinstance(a, AssetView) for a in assets)
    assert isinstance(
        h.get_open_edit_session(WebsitePath(website_id=ids["website_id"])),
        EditSessionView,
    )


def test_handlers_missing_return_none_or_empty():
    h, _ = _build_handlers()
    assert h.get_client(ClientPath(client_id="missing")) is None
    assert h.get_website(WebsitePath(website_id="missing")) is None
    assert h.get_current_deployment(WebsitePath(website_id="missing")) is None
    assert h.get_assets(WebsiteAssetsQuery(website_id="missing")) == ()
    assert h.get_open_edit_session(WebsitePath(website_id="missing")) is None


def test_handlers_call_only_read_service_surface():
    """Handlers map path/query → service; no HTTP framework types."""
    import app.portal.read_api_handlers as mod

    src = open(mod.__file__, encoding="utf-8").read()
    assert "from fastapi" not in src
    assert "import fastapi" not in src
    assert "APIRouter" not in src
    assert "starlette" not in src.lower()
    assert "JSONResponse" not in src
    assert "status_code" not in src
    assert "PortalReadService" in src


def test_asset_filter_via_contract_query():
    h, ids = _build_handlers()
    logos = h.get_assets(
        WebsiteAssetsQuery(website_id=ids["website_id"], asset_type="logo")
    )
    assert len(logos) == 1
    assert logos[0].asset_type == "logo"
