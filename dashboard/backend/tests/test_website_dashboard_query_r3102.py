"""R3.10.2 — Website Dashboard Query (Facade → DashboardView)."""

from __future__ import annotations

from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.read_service import PortalCatalog
from app.portal.views import DeploymentView
from app.portal.website import Website
from app.portal.website_dashboard_query import ENGINE_ID, WebsiteDashboardQuery
from app.portal.website_dashboard_view import WebsiteDashboardView


def _catalog_with_deployment():
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
    return catalog, site.website_id, dep.deployment_id


def test_engine_id():
    assert ENGINE_ID == "website_dashboard_query_v1"


def test_execute_returns_dashboard_view():
    catalog, website_id, dep_id = _catalog_with_deployment()
    q = WebsiteDashboardQuery.from_catalog(catalog)
    dash = q.execute(website_id)
    assert isinstance(dash, WebsiteDashboardView)
    assert not isinstance(dash, Website)
    assert dash.website.website_id == website_id
    assert dash.status == dash.website.status
    assert isinstance(dash.current_deployment, DeploymentView)
    assert dash.current_deployment.deployment_id == dep_id


def test_execute_missing_returns_none():
    catalog, _, _ = _catalog_with_deployment()
    q = WebsiteDashboardQuery.from_catalog(catalog)
    assert q.execute("missing") is None


def test_execute_without_deployment():
    client = new_client(display_name="A", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="NL")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={},
        assets={},
        edit_sessions={},
    )
    dash = WebsiteDashboardQuery.from_catalog(catalog).execute(site.website_id)
    assert dash is not None
    assert dash.current_deployment is None


def test_query_does_not_import_domain_website():
    import app.portal.website_dashboard_query as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from app.portal.website import" not in src
    assert "WebsiteReadFacade" in src
    assert "from fastapi" not in src
    assert "APIRouter" not in src


def test_surface_is_execute_only():
    public = {n for n in dir(WebsiteDashboardQuery) if not n.startswith("_")}
    assert "execute" in public
    for forbidden in ("save", "update", "delete", "publish", "write"):
        assert forbidden not in public
