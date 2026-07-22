"""R3.7.4 — Portal Composition Root (wiring only)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.client import new_client, website_for_client
from app.portal.portal_bootstrap import (
    ENGINE_ID,
    PortalReadStack,
    compose_portal_read,
    empty_portal_catalog,
    teardown_portal_read,
)
from app.portal.read_api_handlers import PortalReadHandlers
from app.portal.read_service import PortalCatalog, PortalReadService


def test_engine_id():
    assert ENGINE_ID == "portal_bootstrap_v1"


def test_compose_assembles_full_stack():
    teardown_portal_read()
    try:
        stack = compose_portal_read()
        assert isinstance(stack, PortalReadStack)
        assert isinstance(stack.catalog, PortalCatalog)
        assert isinstance(stack.service, PortalReadService)
        assert isinstance(stack.handlers, PortalReadHandlers)
        assert stack.router is not None
        assert stack.router.prefix == "/portal"
    finally:
        teardown_portal_read()


def test_compose_with_catalog_wires_router():
    teardown_portal_read()
    try:
        client = new_client(display_name="EL3", primary_email="a@b.c")
        website = website_for_client(client, product_id="p1", market_code="DE")
        catalog = PortalCatalog(
            clients={client.client_id: client},
            websites={website.website_id: website},
            deployments={},
            assets={},
            edit_sessions={},
        )
        stack = compose_portal_read(catalog)
        app = FastAPI()
        app.include_router(stack.router)
        http = TestClient(app)
        r = http.get(f"/portal/clients/{client.client_id}")
        assert r.status_code == 200
        assert r.json()["client_id"] == client.client_id
    finally:
        teardown_portal_read()


def test_empty_catalog_factory():
    cat = empty_portal_catalog()
    assert cat.clients == {}
    assert cat.websites == {}


def test_bootstrap_is_only_composition_site():
    """Composition root imports the stack pieces; main.py stays clean."""
    import app.portal.portal_bootstrap as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "PortalReadService" in src
    assert "PortalReadHandlers" in src
    assert "set_portal_read_handlers" in src
    assert "portal_read_router" in src
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "compose_portal_read" not in text
    assert "portal_bootstrap" not in text


def test_no_business_logic_in_bootstrap():
    import app.portal.portal_bootstrap as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    for forbidden in ("publish", "upload", "auth", "password", "HTTPException"):
        assert forbidden not in src.lower() or forbidden == "auth" and "No Auth" in src
    assert "HTTPException" not in src
