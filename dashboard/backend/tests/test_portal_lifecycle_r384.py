"""R3.8.4 — Portal Lifecycle Contract (terminology + resolve only)."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from app.portal.portal_bootstrap import teardown_portal_read
from app.portal.portal_lifecycle import (
    ENGINE_ID,
    PORTAL_LIFECYCLE_STATES,
    PORTAL_LIFECYCLE_TRANSITIONS,
    clear_portal_lifecycle_notes,
    is_transition_allowed,
    portal_lifecycle_snapshot,
    resolve_portal_lifecycle_state,
)
from app.portal.portal_profile import is_portal_feature_enabled
from app.portal.portal_registration import (
    clear_registration_outcome,
    register_portal_read,
)


def test_engine_id():
    assert ENGINE_ID == "portal_lifecycle_v1"


def test_states_and_happy_path_transitions():
    assert PORTAL_LIFECYCLE_STATES == (
        "disabled",
        "registered",
        "active",
        "teardown",
    )
    assert is_transition_allowed("disabled", "registered")
    assert is_transition_allowed("registered", "active")
    assert is_transition_allowed("active", "teardown")
    assert not is_transition_allowed("disabled", "active")


def test_resolve_disabled_by_default():
    clear_registration_outcome()
    clear_portal_lifecycle_notes()
    assert resolve_portal_lifecycle_state() == "disabled"
    assert is_portal_feature_enabled() is False


def test_resolve_registered_after_noop_register():
    clear_registration_outcome()
    clear_portal_lifecycle_notes()
    assert register_portal_read(FastAPI()) is False
    assert resolve_portal_lifecycle_state() == "registered"


def test_resolve_teardown_after_teardown_call():
    clear_registration_outcome()
    clear_portal_lifecycle_notes()
    register_portal_read(FastAPI())
    teardown_portal_read()
    assert resolve_portal_lifecycle_state() == "teardown"


def test_lifecycle_snapshot_includes_contract():
    clear_registration_outcome()
    clear_portal_lifecycle_notes()
    snap = portal_lifecycle_snapshot()
    assert snap["lifecycle_state"] == "disabled"
    assert snap["feature_enabled"] is False
    assert snap["registration_active"] is False
    assert "disabled" in snap["states"]
    assert "registered" in snap["transitions"]["disabled"]


def test_no_endpoints_and_main_unchanged():
    import app.portal.portal_lifecycle as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "APIRouter" not in src
    assert "include_router" not in src
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "portal_lifecycle" not in text
