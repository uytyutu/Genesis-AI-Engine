"""R5.2 — Analytics Overview (read-only reference module)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.analytics import AnalyticsOverview, empty_analytics_overview
from app.portal.analytics_facade import AnalyticsFacade
from app.portal.analytics_store import InMemoryAnalyticsStore
from app.portal.client import new_client, website_for_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_analytics_registration import register_portal_analytics
from app.portal.portal_analytics_router import (
    ENGINE_ID,
    clear_analytics_facade,
    portal_analytics_router,
)


def _site_and_owner():
    client = new_client(display_name="EL3", primary_email="owner@example.com")
    site = website_for_client(client, product_id="p1", market_code="DE")
    account = new_account(
        email="owner@example.com", display_name="Owner", status="ready"
    )
    ownerships = InMemoryOwnershipDirectory(
        ownerships=[grant_website_ownership(account, site)]
    )
    return site.website_id, account, ownerships


def test_engine_id():
    assert ENGINE_ID == "portal_analytics_router_v1"


def test_domain_empty_and_normalize():
    empty = empty_analytics_overview("w1")
    assert empty.visitors == 0
    assert empty.page_views == 0
    assert empty.data_source == "in_memory"

    from app.portal.analytics import normalize_analytics_overview

    raw = AnalyticsOverview(
        website_id="w1",
        visitors=-3,
        page_views=-1,
        last_updated="2026-07-22T00:00:00+00:00",
        data_source="in_memory",
    )
    fixed = normalize_analytics_overview(raw)
    assert fixed.visitors == 0
    assert fixed.page_views == 0


def test_facade_get_empty_and_seeded():
    store = InMemoryAnalyticsStore()
    facade = AnalyticsFacade.from_store(store)
    view = facade.get_overview("w-empty")
    assert view.website_id == "w-empty"
    assert view.visitors == 0
    assert view.page_views == 0

    store.put_overview(
        AnalyticsOverview(
            website_id="w-seed",
            visitors=12,
            page_views=40,
            last_updated="2026-07-22T12:00:00+00:00",
            data_source="in_memory",
        )
    )
    seeded = facade.get_overview("w-seed")
    assert seeded.visitors == 12
    assert seeded.page_views == 40
    assert seeded.data_source == "in_memory"


def test_anonymous_get_401():
    clear_analytics_facade()
    website_id, _, ownerships = _site_and_owner()
    app = FastAPI()
    register_portal_analytics(app, ownerships=ownerships)
    try:
        assert (
            TestClient(app)
            .get(f"/portal/websites/{website_id}/analytics")
            .status_code
            == 401
        )
    finally:
        clear_analytics_facade()


def test_no_ownership_403():
    clear_analytics_facade()
    website_id, account, _ = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_analytics(app, ownerships=InMemoryOwnershipDirectory())
    try:
        assert (
            TestClient(app)
            .get(f"/portal/websites/{website_id}/analytics")
            .status_code
            == 403
        )
    finally:
        clear_analytics_facade()


def test_get_overview_happy_path():
    clear_analytics_facade()
    website_id, account, ownerships = _site_and_owner()
    store = InMemoryAnalyticsStore()
    store.put_overview(
        AnalyticsOverview(
            website_id=website_id,
            visitors=100,
            page_views=250,
            last_updated="2026-07-22T15:00:00+00:00",
            data_source="in_memory",
        )
    )
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_analytics(app, ownerships=ownerships, store=store)
    try:
        r = TestClient(app).get(f"/portal/websites/{website_id}/analytics")
        assert r.status_code == 200
        body = r.json()
        assert body["website_id"] == website_id
        assert body["visitors"] == 100
        assert body["page_views"] == 250
        assert body["last_updated"] == "2026-07-22T15:00:00+00:00"
        assert body["data_source"] == "in_memory"
    finally:
        clear_analytics_facade()


def test_router_get_only_no_put():
    methods: set[str] = set()
    matched = False
    for route in portal_analytics_router.routes:
        path = getattr(route, "path", "")
        if not path.endswith("/websites/{website_id}/analytics"):
            continue
        matched = True
        methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"GET"}


def test_main_registers_analytics():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_analytics(app)" in text
    assert "include_router(portal_analytics_router)" not in text


def test_read_module_blueprint_repeatability():
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    required = [
        "analytics.py",
        "analytics_store.py",
        "analytics_view.py",
        "analytics_facade.py",
        "portal_analytics_router.py",
        "portal_analytics_registration.py",
    ]
    for name in required:
        assert (portal / name).is_file(), name

    facade = (portal / "analytics_facade.py").read_text(encoding="utf-8")
    router = (portal / "portal_analytics_router.py").read_text(encoding="utf-8")
    domain = (portal / "analytics.py").read_text(encoding="utf-8")
    assert "def update_" not in facade
    assert "put(" not in router.lower() or "@portal_analytics_router.put" not in router
    assert "@portal_analytics_router.put" not in router
    assert "@portal_analytics_router.post" not in router
    assert "from app.portal.authentication" not in domain
    assert "from app.portal.authorization" not in domain
    assert "AuthorizationFacade" in router
    assert "AnalyticsFacade" in router
