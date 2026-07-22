"""R3.9.1 — Website Read Context (read-only; no Auth/endpoints)."""

from __future__ import annotations

from pathlib import Path

from app.portal.client import new_client, website_for_client
from app.portal.read_service import PortalCatalog
from app.portal.views import WebsiteView
from app.portal.website_read_context import ENGINE_ID, WebsiteReadContext


def _catalog_with_site():
    client = new_client(display_name="EL3", primary_email="a@b.c")
    website = website_for_client(client, product_id="prod-1", market_code="DE")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={website.website_id: website},
        deployments={},
        assets={},
        edit_sessions={},
    )
    return catalog, website.website_id


def test_engine_id():
    assert ENGINE_ID == "website_read_context_v1"


def test_get_website_by_id():
    catalog, website_id = _catalog_with_site()
    ctx = WebsiteReadContext.from_catalog(catalog)
    view = ctx.get_website(website_id)
    assert isinstance(view, WebsiteView)
    assert view.website_id == website_id
    assert view.market_code == "DE"


def test_get_website_missing_returns_none():
    catalog, _ = _catalog_with_site()
    ctx = WebsiteReadContext.from_catalog(catalog)
    assert ctx.get_website("missing") is None


def test_read_only_surface():
    names = {n for n in dir(WebsiteReadContext) if not n.startswith("_")}
    assert "get_website" in names
    for forbidden in ("save", "update", "delete", "create", "publish", "write"):
        assert forbidden not in names


def test_no_http_auth_in_module():
    import app.portal.website_read_context as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "from fastapi" not in src
    assert "import fastapi" not in src
    assert "APIRouter" not in src
    assert "HTTPException" not in src
    assert "oauth" not in src.lower()
    assert "password" not in src.lower()
