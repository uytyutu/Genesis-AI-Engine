"""R5.1 — Website Settings Basic Profile (reference module)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client, website_for_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_website_settings_registration import (
    register_portal_website_settings,
)
from app.portal.portal_website_settings_router import (
    ENGINE_ID,
    clear_website_settings_facade,
    portal_website_settings_router,
)
from app.portal.website_settings import (
    WebsiteSettingsError,
    WebsiteSettingsUpdate,
    apply_website_settings_update,
    empty_website_settings,
)
from app.portal.website_settings_facade import WebsiteSettingsFacade
from app.portal.website_settings_store import InMemoryWebsiteSettingsStore


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
    assert ENGINE_ID == "portal_website_settings_router_v1"


def test_domain_apply_basic_profile():
    current = empty_website_settings("w1")
    updated = apply_website_settings_update(
        current,
        WebsiteSettingsUpdate(
            website_name=" Praxis Nord ",
            company_name=" EL3 GmbH ",
            contact_email=" hello@el3.de ",
            phone=" +49 30 123 ",
            social_links={"instagram": " https://instagram.com/el3 ", "x": ""},
        ),
    )
    assert updated.website_name == "Praxis Nord"
    assert updated.company_name == "EL3 GmbH"
    assert updated.contact_email == "hello@el3.de"
    assert updated.phone == "+49 30 123"
    assert updated.social_links == (("instagram", "https://instagram.com/el3"),)


def test_domain_rejects_bad_email_and_unknown_network():
    current = empty_website_settings("w1")
    try:
        apply_website_settings_update(
            current,
            WebsiteSettingsUpdate(
                website_name="A",
                company_name="",
                contact_email="not-an-email",
                phone="",
                social_links={},
            ),
        )
        assert False, "expected WebsiteSettingsError"
    except WebsiteSettingsError as exc:
        assert "contact_email" in str(exc)

    try:
        apply_website_settings_update(
            current,
            WebsiteSettingsUpdate(
                website_name="A",
                company_name="",
                contact_email="",
                phone="",
                social_links={"myspace": "https://x"},
            ),
        )
        assert False, "expected WebsiteSettingsError"
    except WebsiteSettingsError as exc:
        assert "social_network" in str(exc)


def test_facade_get_empty_then_update_roundtrip():
    store = InMemoryWebsiteSettingsStore()
    facade = WebsiteSettingsFacade.from_store(store)
    view = facade.get_settings("w-empty")
    assert view.website_id == "w-empty"
    assert view.website_name == ""
    assert view.social_links == {}

    saved = facade.update_settings(
        "w-empty",
        website_name="Site",
        company_name="Co",
        contact_email="a@b.c",
        phone="1",
        social_links={"facebook": "https://facebook.com/co"},
    )
    assert saved.website_name == "Site"
    assert facade.get_settings("w-empty").as_dict() == saved.as_dict()


def test_anonymous_get_401():
    clear_website_settings_facade()
    website_id, _, ownerships = _site_and_owner()
    app = FastAPI()
    register_portal_website_settings(app, ownerships=ownerships)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/settings").status_code
            == 401
        )
    finally:
        clear_website_settings_facade()


def test_no_ownership_403():
    clear_website_settings_facade()
    website_id, account, _ = _site_and_owner()
    empty = InMemoryOwnershipDirectory()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_settings(app, ownerships=empty)
    try:
        assert (
            TestClient(app).get(f"/portal/websites/{website_id}/settings").status_code
            == 403
        )
    finally:
        clear_website_settings_facade()


def test_get_put_happy_path_uses_existing_authz():
    clear_website_settings_facade()
    website_id, account, ownerships = _site_and_owner()
    store = InMemoryWebsiteSettingsStore()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_settings(app, ownerships=ownerships, store=store)
    http = TestClient(app)
    try:
        g = http.get(f"/portal/websites/{website_id}/settings")
        assert g.status_code == 200
        assert g.json()["website_id"] == website_id
        assert g.json()["website_name"] == ""

        p = http.put(
            f"/portal/websites/{website_id}/settings",
            json={
                "website_name": "Mein Portal",
                "company_name": "Virtus Demo",
                "contact_email": "kontakt@demo.de",
                "phone": "+49 40 1",
                "social_links": {"linkedin": "https://linkedin.com/company/demo"},
            },
        )
        assert p.status_code == 200
        body = p.json()
        assert body["website_name"] == "Mein Portal"
        assert body["company_name"] == "Virtus Demo"
        assert body["contact_email"] == "kontakt@demo.de"
        assert body["phone"] == "+49 40 1"
        assert body["social_links"] == {
            "linkedin": "https://linkedin.com/company/demo"
        }

        again = http.get(f"/portal/websites/{website_id}/settings")
        assert again.status_code == 200
        assert again.json() == body
    finally:
        clear_website_settings_facade()


def test_put_invalid_settings_400():
    clear_website_settings_facade()
    website_id, account, ownerships = _site_and_owner()
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    register_portal_website_settings(app, ownerships=ownerships)
    try:
        r = TestClient(app).put(
            f"/portal/websites/{website_id}/settings",
            json={
                "website_name": "X",
                "company_name": "",
                "contact_email": "bad",
                "phone": "",
                "social_links": {},
            },
        )
        assert r.status_code == 400
        assert r.json()["detail"] == "invalid_settings"
    finally:
        clear_website_settings_facade()


def test_router_only_get_put_settings():
    methods: set[str] = set()
    matched = False
    for route in portal_website_settings_router.routes:
        path = getattr(route, "path", "")
        if not path.endswith("/websites/{website_id}/settings"):
            continue
        matched = True
        methods |= set(getattr(route, "methods", set()) or set())
    assert matched
    assert methods == {"GET", "PUT"}


def test_main_registers_website_settings():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_website_settings(app)" in text
    assert "include_router(portal_website_settings_router)" not in text


def test_reference_module_shape_for_repeatability():
    """Analytics/ChatBot/CRM should be able to copy this file set."""
    portal = Path(__file__).resolve().parents[1] / "app" / "portal"
    required = [
        "website_settings.py",
        "website_settings_store.py",
        "website_settings_view.py",
        "website_settings_facade.py",
        "portal_website_settings_router.py",
        "portal_website_settings_registration.py",
    ]
    for name in required:
        assert (portal / name).is_file(), name

    # Module must not redefine Authorization / Authentication / Session.
    domain = (portal / "website_settings.py").read_text(encoding="utf-8")
    facade = (portal / "website_settings_facade.py").read_text(encoding="utf-8")
    router = (portal / "portal_website_settings_router.py").read_text(
        encoding="utf-8"
    )
    for text in (domain, facade):
        assert "from app.portal.authentication" not in text
        assert "from app.portal.authorization" not in text
        assert "from app.portal.session" not in text
        assert "def authenticate" not in text
        assert "def authorize" not in text
    assert "AuthorizationFacade" in router
    assert "check_website_access" in router
    assert "WebsiteSettingsFacade" in router
    assert "from app.portal.authorization_facade import AuthorizationFacade" in router
