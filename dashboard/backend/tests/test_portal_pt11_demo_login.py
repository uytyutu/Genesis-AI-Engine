"""PT1.1 — Portal demo directory enables First Run login."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.portal_demo_directory import (
    DEMO_PORTAL_EMAIL,
    DEMO_PORTAL_PASSWORD,
    build_demo_authentication_directory,
)
from app.portal.portal_login_registration import register_portal_login
from app.portal.portal_login_router import clear_authentication_facade


def test_demo_directory_login_succeeds():
    clear_authentication_facade()
    app = FastAPI()
    assert register_portal_login(app) is True  # default demo directory
    http = TestClient(app)
    try:
        r = http.post(
            "/portal/login",
            json={"email": DEMO_PORTAL_EMAIL, "password": DEMO_PORTAL_PASSWORD},
        )
        assert r.status_code == 200
        assert r.json() == {"authenticated": True}
        assert "set-cookie" in {k.lower() for k in r.headers.keys()}
    finally:
        clear_authentication_facade()


def test_build_demo_directory_contains_ready_account():
    directory = build_demo_authentication_directory()
    account = directory.find_account_by_email(DEMO_PORTAL_EMAIL)
    assert account is not None
    assert account.status == "ready"
    cred = directory.find_credential(account.account_id)
    assert cred is not None
    assert cred.password_hash == DEMO_PORTAL_PASSWORD
