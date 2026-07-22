"""R3.9.4 — Website Read Facade (Query → WebsiteView)."""

from __future__ import annotations

from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.read_service import PortalCatalog
from app.portal.website import Website
from app.portal.website_read_context import WebsiteReadContext
from app.portal.website_read_facade import ENGINE_ID, WebsiteReadFacade
from app.portal.website_read_query import WebsiteReadQuery
from app.portal.website_view import WebsiteView


def _facade() -> tuple[WebsiteReadFacade, str]:
    client = new_client(display_name="EL3", primary_email="a@b.c")
    site = website_for_client(client, product_id="p1", market_code="DE")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={site.website_id: site},
        deployments={},
        assets={},
        edit_sessions={},
    )
    query = WebsiteReadQuery.from_context(WebsiteReadContext.from_catalog(catalog))
    return WebsiteReadFacade.from_query(query), site.website_id


def test_engine_id():
    assert ENGINE_ID == "website_read_facade_v1"


def test_get_website_returns_view():
    facade, website_id = _facade()
    view = facade.get_website(website_id)
    assert isinstance(view, WebsiteView)
    assert not isinstance(view, Website)
    assert view.website_id == website_id


def test_get_website_missing_returns_none():
    facade, _ = _facade()
    assert facade.get_website("missing") is None


def test_facade_uses_only_query():
    import app.portal.website_read_facade as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "WebsiteReadQuery" in src
    assert "from app.portal.website import" not in src
    assert "PortalReadService" not in src
    assert "from fastapi" not in src
    assert "APIRouter" not in src


def test_facade_surface_is_get_website_only():
    public = {n for n in dir(WebsiteReadFacade) if not n.startswith("_")}
    assert "get_website" in public
    assert "from_query" in public
    for forbidden in ("save", "update", "delete", "execute", "publish"):
        assert forbidden not in public
