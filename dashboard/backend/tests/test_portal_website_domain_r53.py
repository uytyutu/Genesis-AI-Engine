"""R5.3 — Website Domain Management (resource-state reference module)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client, website_for_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_website_domain_registration import (
    register_portal_website_domain,
)
from app.portal.portal_website_domain_router import (
    ENGINE_ID,
    clear_website_domain_facade,
    portal_website_domain_router,
)
from app.portal.website_domain import (
    WebsiteDomainError,
    WebsiteDomainUpdate,
    apply_website_domain_update,
    empty_website_domain,
)
from app.portal.website_domain_facade import WebsiteDomainFacade
from app.portal.website_domain_store import InMemoryWebsiteDomainStore


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
    assert ENGINE_ID == "portal_website_domain_router_v1"


def test_domain_apply_and_reject_invalid():
    current = empty_website_domain("w1")
    assert current.domain_status == "none"
    assert current.verification_status == "unverified"

    updated = apply_website_domain_update(
        current,
        WebsiteDomainUpdate(
            primary_domain=" Demo.Virtus.Core ",
            custom_domain=" Praxis-Nord.de ",
            domain_status="pending",
            verification_status="pending",
        ),
    )
    assert updated.primary_domain == "demo.virtus.core"
    assert updated.custom_domain == "praxis-nord.de"
    assert updated.domain_status == "pending"
    assert updated.verification_status == "pending"

    try:
        apply_website_domain_update(
            current,
            WebsiteDomainUpdate(
                primary_domain="https://bad.example",
                custom_domain="",
                domain_status="none",
                verification_status="unverified",
            ),
        )
        assert False, "expected WebsiteDomainError"
    except WebsiteDomainError as exc:
        assert "primary_domain" in str(exc)

    try:
        apply_website_domain_update(
            current,
            WebsiteDomainUpdate(
                primary_domain="",
                custom_domain="",
                domain_status="flying",
                verification_status="unverified",
            ),
        )
        assert False, "expected WebsiteDomainError"
    except WebsiteDomainError as exc:
        assert "domain_status" in str(exc)


def test_facade_get_empty_then_update_roundtrip():
    store = InMemoryWebsiteDomainStore()
    facade = WebsiteDomainFacade.from_store(store)
    view = facade.get_domain("w-empty")
    assert view.primary_domain == ""
    assert view.domain_status == "none"

    saved = facade.update_domain(
        "w-empty",
        primary_domain="site.example.com",
        custom_domain="brand.de",
        domain_status="active",
        verification_status="verified",
    )
    assert saved.primary_domain == "site.example.com"
    assert saved.custom_domain == "brand.de"
    assert facade.get_domain("w-empty").as_dict() == saved.as_dict()


def test_anonymous_get_401():
    clear_website_domain_facade()
    website_id, _, ownerships = _site_and_owner()
    app = FastAPI()
    register_portal_website_domain(app, ownerships=ownerships)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/domain").status_code
            == 401
        )
    finally:
        clear_website_domain_facade()


def test_no_ownership_403():
    clear_website_domain_facade()
    website_id, account, _ = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_domain(app, ownerships=InMemoryOwnershipDirectory())
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/domain").status_code
            == 403
        )
    finally:
        clear_website_domain_facade()


def test_get_put_happy_path():
    clear_website_domain_facade()
    website_id, account, ownerships = _site_and_owner()
    store = InMemoryWebsiteDomainStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_domain(app, ownerships=ownerships, store=store)
    http = TestClient(app)
    try:
        g = http.get(f"/portal/websites/{website_id}/domain")
        assert g.status_code == 200
        assert g.json()["domain_status"] == "none"
        assert g.json()["verification_status"] == "unverified"

        p = http.put(
            f"/portal/websites/{website_id}/domain",
            json={
                "primary_domain": "el3.virtus.local",
                "custom_domain": "el3.de",
                "domain_status": "pending",
                "verification_status": "pending",
            },
        )
        assert p.status_code == 200
        body = p.json()
        assert body["primary_domain"] == "el3.virtus.local"
        assert body["custom_domain"] == "el3.de"
        assert body["domain_status"] == "pending"
        assert body["verification_status"] == "pending"

        again = http.get(f"/portal/websites/{website_id}/domain")
        assert again.status_code == 200
        assert again.json() == body
    finally:
        clear_website_domain_facade()


def test_put_invalid_400():
    clear_website_domain_facade()
    website_id, account, ownerships = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_domain(app, ownerships=ownerships)
    try:
        r = TestClient(app).put(
            f"/portal/websites/{website_id}/domain",
            json={
                "primary_domain": "not a host",
                "custom_domain": "",
                "domain_status": "none",
                "verification_status": "unverified",
            },
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "invalid_domain"
    finally:
        clear_website_domain_facade()


def test_router_get_put_only():
    methods: set[str] = set()
    matched = False
    for route in portal_website_domain_router.routes:
        path = getattr(route, "path", "")
        if not path.endswith("/websites/{website_id}/domain"):
            continue
        matched = True
        methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"GET", "PUT"}


def test_main_registers_website_domain():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_website_domain(app)" in text
    assert "include_router(portal_website_domain_router)" not in text


def test_resource_module_blueprint_and_evolutionary_contract():
    """Contract fields stay stable for future DNS/SSL store backends."""
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    required = [
        "website_domain.py",
        "website_domain_store.py",
        "website_domain_view.py",
        "website_domain_facade.py",
        "portal_website_domain_router.py",
        "portal_website_domain_registration.py",
    ]
    for name in required:
        assert (portal / name).is_file(), name

    domain = (portal / "website_domain.py").read_text(encoding="utf-8")
    facade = (portal / "website_domain_facade.py").read_text(encoding="utf-8")
    router = (portal / "portal_website_domain_router.py").read_text(encoding="utf-8")
    view = (portal / "website_domain_view.py").read_text(encoding="utf-8")

    for text in (domain, facade):
        assert "from app.portal.authentication" not in text
        assert "from app.portal.authorization" not in text
        assert "import requests" not in text
        assert "httpx" not in text
        assert "def provision_ssl" not in text
        assert "def create_dns_record" not in text

    for field in (
        "primary_domain",
        "custom_domain",
        "domain_status",
        "verification_status",
    ):
        assert field in view
        assert field in router

    assert "AuthorizationFacade" in router
    assert "WebsiteDomainFacade" in router
    assert "WebsiteDomainStore" in (
        portal / "website_domain_store.py"
    ).read_text(encoding="utf-8")
