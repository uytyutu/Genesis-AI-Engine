"""R3.8.1 — Portal Integration Profile (feature off; not mounted)."""

from __future__ import annotations

from pathlib import Path

from app.portal.portal_bootstrap import teardown_portal_read
from app.portal.portal_profile import (
    ENGINE_ID,
    PORTAL_PROFILE,
    is_portal_feature_enabled,
    portal_profile_snapshot,
)
from app.portal.portal_read_router import portal_read_router


def test_engine_id():
    assert ENGINE_ID == "portal_profile_v1"


def test_feature_disabled_by_default():
    assert PORTAL_PROFILE.feature_enabled is False
    assert is_portal_feature_enabled() is False


def test_providers_point_at_composition_root():
    assert PORTAL_PROFILE.router_provider() is portal_read_router
    teardown_portal_read()
    try:
        stack = PORTAL_PROFILE.bootstrap_provider()
        assert stack.router is portal_read_router
        assert stack.service is not None
        assert stack.handlers is not None
    finally:
        PORTAL_PROFILE.teardown()


def test_profile_snapshot_inactive():
    snap = portal_profile_snapshot()
    assert snap["feature_enabled"] is False
    assert snap["mounted_in_app"] is False
    assert snap["auth"] is False
    assert snap["bootstrap"] == "compose_portal_read"


def test_main_unchanged_and_portal_inactive():
    main = Path(__file__).resolve().parents[1] / "app" / "main.py"
    text = main.read_text(encoding="utf-8")
    assert "portal_profile" not in text
    assert "PORTAL_PROFILE" not in text
    assert "compose_portal_read" not in text
    assert "portal_read_router" not in text


def test_profile_has_no_mount_or_auth_logic():
    import app.portal.portal_profile as mod

    src = Path(mod.__file__).read_text(encoding="utf-8")
    assert "include_router" not in src
    assert "HTTPException" not in src
    assert "oauth" not in src.lower()
    assert "password" not in src.lower()
