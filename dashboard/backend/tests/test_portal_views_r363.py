"""R3.6.3 — Portal View Models (data only)."""

from __future__ import annotations

from dataclasses import fields

from app.portal.asset import new_asset
from app.portal.client import new_client
from app.portal.deployment import new_deployment
from app.portal.views import (
    ENGINE_ID,
    AssetView,
    ClientView,
    DeploymentView,
    WebsiteView,
    to_asset_view,
    to_client_view,
    to_deployment_view,
    to_website_view,
)
from app.portal.website import new_website


def test_view_engine_id():
    assert ENGINE_ID == "portal_view_v1"


def test_view_shapes():
    assert {f.name for f in fields(ClientView)} == {
        "client_id",
        "display_name",
        "primary_email",
        "preferred_language",
    }
    assert {f.name for f in fields(WebsiteView)} == {
        "website_id",
        "client_id",
        "product_id",
        "market_code",
        "deployment_id",
        "status",
    }
    assert {f.name for f in fields(DeploymentView)} == {
        "deployment_id",
        "website_id",
        "artifact_id",
        "version",
        "status",
    }
    assert {f.name for f in fields(AssetView)} == {
        "asset_id",
        "website_id",
        "asset_type",
        "artifact_ref",
    }


def test_mappers_from_domain():
    c = new_client(display_name="A", primary_email="a@b.c")
    w = new_website(client_id=c.client_id, product_id="p", market_code="DE")
    d = new_deployment(website=w, artifact_id="art")
    a = new_asset(website=w, asset_type="logo", artifact_ref="ref/1")
    assert to_client_view(c).client_id == c.client_id
    assert to_website_view(w).website_id == w.website_id
    assert to_deployment_view(d).deployment_id == d.deployment_id
    assert to_asset_view(a).artifact_ref == "ref/1"


def test_views_have_no_domain_verbs():
    for cls in (ClientView, WebsiteView, DeploymentView, AssetView):
        names = {n for n in dir(cls) if not n.startswith("_")}
        assert not names & {"save", "publish", "upload", "validate", "execute"}
