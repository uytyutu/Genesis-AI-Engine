"""R3.9.2 — Website View Contract (immutable; used by Read Context)."""

from __future__ import annotations

from dataclasses import fields

from app.portal.client import new_client, website_for_client
from app.portal.read_service import PortalCatalog
from app.portal.website import Website
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_view import (
    ENGINE_ID,
    WEBSITE_VIEW_FIELDS,
    WebsiteView,
    to_website_view,
)


def test_engine_id():
    assert ENGINE_ID == "website_view_contract_v1"


def test_website_view_fields():
    assert tuple(f.name for f in fields(WebsiteView)) == WEBSITE_VIEW_FIELDS
    assert WEBSITE_VIEW_FIELDS == (
        "website_id",
        "client_id",
        "product_id",
        "market_code",
        "status",
        "deployment_id",
    )


def test_website_view_is_frozen():
    client = new_client(display_name="A", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    view = to_website_view(site)
    try:
        view.status = "published"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised


def test_context_returns_view_not_domain():
    client = new_client(display_name="A", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="NL")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={},
        assets={},
        edit_sessions={},
    )
    result = WebsiteReadContext.from_catalog(catalog).get_website(site.website_id)
    assert isinstance(result, WebsiteView)
    assert not isinstance(result, Website)
    assert result.website_id == site.website_id
    assert result.client_id == client.client_id


def test_mapper_has_no_business_verbs():
    assert callable(to_website_view)
    names = {n for n in dir(WebsiteView) if not n.startswith("_")}
    assert not names & {"save", "update", "publish", "validate", "execute"}
