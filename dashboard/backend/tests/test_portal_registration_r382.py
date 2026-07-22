"""R3.8.2 — Controlled Portal Registration (feature flag gate)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.portal.client import new_client
from app.portal.portal_profile import PORTAL_PROFILE
from app.portal.portal_registration import (
    ENGINE_ID,
    register_portal_read,
    registration_status,
)
from app.portal.read_service import PortalCatalog


def test_engine_id():
    assert ENGINE_ID == "portal_registration_v1"


def test_disabled_is_noop():
    assert PORTAL_PROFILE.feature_enabled is False
    app = FastAPI()
    before = list(app.routes)
    mounted = register_portal_read(app)
    assert mounted is False
    assert list(app.routes) == before


def test_enabled_mounts_via_profile():
    client = new_client(display_name="EL3", primary_email="a@b.c")
    catalog = PortalCatalog(
        clients={client.client_id: client},
        websites={},
        deployments={},
        assets={},
        edit_sessions={},
    )
    enabled = replace(PORTAL_PROFILE, feature_enabled=True)
    app = FastAPI()
    with patch("app.portal.portal_registration.PORTAL_PROFILE", enabled):
        with patch(
            "app.portal.portal_registration.is_portal_feature_enabled",
            return_value=True,
        ):
            assert register_portal_read(app, catalog=catalog) is True
    http = TestClient(app)
    r = http.get(f"/portal/clients/{client.client_id}")
    assert r.status_code == 200
    assert r.json()["client_id"] == client.client_id
    PORTAL_PROFILE.teardown()


def test_registration_status_reflects_flag():
    status = registration_status()
    assert status["feature_enabled"] is False
    assert status["would_mount"] is False
    assert status["decision_point"] == "PORTAL_PROFILE.feature_enabled"


def test_main_calls_register_not_include_router_directly():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "register_portal_read(app)" in text
    assert "include_router(portal_read_router)" not in text
    assert "include_router(stack.router)" not in text
