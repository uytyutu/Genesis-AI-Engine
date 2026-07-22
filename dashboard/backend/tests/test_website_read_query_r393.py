"""R3.9.3 — Website Read Query (Context → WebsiteView)."""

from __future__ import annotations

from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.read_service import PortalCatalog
from app.portal.website import Website
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_read_query import ENGINE_ID, WebsiteReadQuery
from app.portal.website_view import WebsiteView


def _query() -> tuple[WebsiteReadQuery, str]:
    client = new_client(display_name="EL3", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={},
        assets={},
        edit_sessions={},
    )
    ctx = WebsiteReadContext.from_catalog(catalog)
    return WebsiteReadQuery.from_context(ctx), site.website_id


def test_engine_id():
    assert ENGINE_ID == "website_read_query_v1"


def test_execute_returns_website_view():
    q, website_id = _query()
    view = q.execute(website_id)
    assert isinstance(view, WebsiteView)
    assert not isinstance(view, Website)
    assert view.website_id == website_id


def test_execute_missing_returns_none():
    q, _ = _query()
    assert q.execute("missing") is None


def test_query_does_not_import_domain_website():
    import app.portal.website_read_query as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from app.portal.website import" not in src
    assert "WebsiteReadContext" in src
    assert "WebsiteView" in src
    assert "from fastapi" not in src
    assert "APIRouter" not in src


def test_query_surface_is_execute_only():
    public = {n for n in dir(WebsiteReadQuery) if not n.startswith("_")}
    assert "execute" in public
    assert "from_context" in public
    for forbidden in ("save", "update", "delete", "publish", "write"):
        assert forbidden not in public
