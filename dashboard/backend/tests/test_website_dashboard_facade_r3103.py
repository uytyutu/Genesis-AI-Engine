"""R3.10.3 — Website Dashboard Facade (Query → DashboardView)."""

from __future__ import annotations

from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.read_service import PortalCatalog
from app.portal.website import Website
from app.portal.website_dashboard_facade import ENGINE_ID, WebsiteDashboardFacade
from app.portal.website_dashboard_query import WebsiteDashboardQuery
from app.portal.website_dashboard_view import WebsiteDashboardView


def _facade() -> tuple[WebsiteDashboardFacade, str]:
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
    query = WebsiteDashboardQuery.from_catalog(catalog)
    return WebsiteDashboardFacade.from_query(query), site.website_id


def test_engine_id():
    assert ENGINE_ID == "website_dashboard_facade_v1"


def test_get_dashboard_returns_view():
    facade, website_id = _facade()
    dash = facade.get_dashboard(website_id)
    assert isinstance(dash, WebsiteDashboardView)
    assert not isinstance(dash, Website)
    assert dash.website.website_id == website_id
    assert dash.current_deployment is not None


def test_get_dashboard_missing_returns_none():
    facade, _ = _facade()
    assert facade.get_dashboard("missing") is None


def test_facade_uses_only_dashboard_query():
    import app.portal.website_dashboard_facade as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "WebsiteDashboardQuery" in src
    assert "from app.portal.website import" not in src
    assert "PortalReadService" not in src
    assert "from fastapi" not in src
    assert "APIRouter" not in src


def test_surface_is_get_dashboard_only():
    public = {n for n in dir(WebsiteDashboardFacade) if not n.startswith("_")}
    assert "get_dashboard" in public
    assert "from_query" in public
    for forbidden in ("save", "update", "execute", "publish", "write"):
        assert forbidden not in public
