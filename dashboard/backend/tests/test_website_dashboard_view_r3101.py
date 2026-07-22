"""R3.10.1 — Website Dashboard View (immutable cabinet aggregate)."""

from __future__ import annotations

from dataclasses import fields
from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.deployment import attach_deployment, new_deployment
from app.portal.views import DeploymentView, to_deployment_view
from app.portal.website_dashboard_view import (
    ENGINE_ID,
    WebsiteDashboardView,
    build_website_dashboard_view,
)
from app.portal.website_view import WebsiteView, to_website_view


def test_engine_id():
    assert ENGINE_ID == "website_dashboard_view_v1"


def test_dashboard_view_shape():
    assert {f.name for f in fields(WebsiteDashboardView)} == {
        "website",
        "status",
        "current_deployment",
    }


def test_build_without_deployment():
    client = new_client(display_name="A", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    wv = to_website_view(site)
    dash = build_website_dashboard_view(wv)
    assert isinstance(dash, WebsiteDashboardView)
    assert isinstance(dash.website, WebsiteView)
    assert dash.status == wv.status
    assert dash.current_deployment is None


def test_build_with_current_deployment():
    client = new_client(display_name="A", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="FR")
    dep = new_deployment(website=site, artifact_id="art-1", status="active")
    site = attach_deployment(site, dep)
    wv = to_website_view(site)
    dv = to_deployment_view(dep)
    dash = build_website_dashboard_view(wv, current_deployment=dv)
    assert isinstance(dash.current_deployment, DeploymentView)
    assert dash.current_deployment.deployment_id == dep.deployment_id
    assert dash.website.deployment_id == dep.deployment_id


def test_dashboard_view_is_frozen():
    client = new_client(display_name="A", primary_email="a@b.c")
    wv = to_website_view(website_for_client(client, product_id="p1", market_code="DE"))
    dash = build_website_dashboard_view(wv)
    try:
        dash.status = "published"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_no_api_auth_write_surface():
    import app.portal.website_dashboard_view as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from fastapi" not in src
    assert "APIRouter" not in src
    assert "HTTPException" not in src
    for forbidden in ("save", "update", "publish", "register_portal"):
        assert forbidden not in src
