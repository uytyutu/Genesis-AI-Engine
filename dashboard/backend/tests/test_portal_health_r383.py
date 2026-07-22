"""R3.8.3 — Portal health snapshot (read-only; Portal stays off)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.portal.portal_health import ENGINE_ID, portal_registration_snapshot
from app.portal.portal_profile import is_portal_feature_enabled
from app.portal.portal_registration import (
    clear_registration_outcome,
    register_portal_read,
)


def test_engine_id():
    assert ENGINE_ID == "portal_health_v1"


def test_snapshot_before_any_registration():
    clear_registration_outcome()
    snap = portal_registration_snapshot()
    assert snap["feature_enabled"] is False
    assert snap["registration_attempted"] is False
    assert snap["registration_active"] is False


def test_snapshot_after_noop_registration():
    clear_registration_outcome()
    app = FastAPI()
    assert register_portal_read(app) is False
    snap = portal_registration_snapshot()
    assert snap["feature_enabled"] is False
    assert snap["registration_attempted"] is True
    assert snap["registration_active"] is False


def test_snapshot_does_not_activate_portal():
    clear_registration_outcome()
    before = portal_registration_snapshot()
    after = portal_registration_snapshot()
    assert before == after
    assert is_portal_feature_enabled() is False
    assert after["registration_active"] is False


def test_snapshot_has_no_side_effects_on_routes():
    clear_registration_outcome()
    app = FastAPI()
    register_portal_read(app)
    routes_before = list(app.routes)
    _ = portal_registration_snapshot()
    assert list(app.routes) == routes_before


def test_main_unchanged_in_r383():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "portal_health" not in text
    assert "portal_registration_snapshot" not in text
    assert "register_portal_read(app)" in text
