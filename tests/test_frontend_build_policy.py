"""Launcher build policy — Normal Launch must not auto-rebuild on stale sources."""

from __future__ import annotations

from pathlib import Path

import pytest

from launcher.deps import ensure_frontend_ready
from launcher.frontend_build_policy import (
    POLICY_LAUNCH_STABLE,
    POLICY_REBUILD_NOW,
    STATUS_MISSING,
    STATUS_READY,
    STATUS_STALE,
    assess_production_build,
    default_policy_for_launch,
    needs_stale_choice,
)
from launcher.launch_mode import LAUNCH_MODE_DEVELOPMENT, LAUNCH_MODE_OWNER


def test_assess_missing_when_no_build(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_ready", lambda _=None: False)
    state = assess_production_build(tmp_path)
    assert state.status == STATUS_MISSING
    assert state.can_launch_without_rebuild is False


def test_owner_stale_needs_choice(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_ready", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_integrity", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_stale", lambda _=None: True)
    state = assess_production_build()
    assert state.status == STATUS_STALE
    assert needs_stale_choice(LAUNCH_MODE_OWNER, state)
    assert not needs_stale_choice(LAUNCH_MODE_DEVELOPMENT, state)


def test_owner_default_policy_launch_stable_on_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_ready", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_integrity", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_stale", lambda _=None: True)
    state = assess_production_build()
    assert default_policy_for_launch(LAUNCH_MODE_OWNER, state) == POLICY_LAUNCH_STABLE


def test_development_default_policy_rebuild_on_stale(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_ready", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_integrity", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_stale", lambda _=None: True)
    state = assess_production_build()
    assert default_policy_for_launch(LAUNCH_MODE_DEVELOPMENT, state) == POLICY_REBUILD_NOW


def test_launch_stable_skips_build_when_stale(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fe = tmp_path / "dashboard" / "frontend"
    nxt = fe / ".next"
    nxt.mkdir(parents=True)
    (nxt / "routes-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "BUILD_ID").write_text("id", encoding="utf-8")
    (nxt / "server").mkdir(parents=True)
    (nxt / "server" / "pages-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "server" / "app").mkdir(parents=True)
    (nxt / "server" / "app" / "page.js").write_text("//", encoding="utf-8")

    monkeypatch.setattr("launcher.deps.frontend_dir", lambda _=None: fe)
    monkeypatch.setattr("launcher.deps.frontend_deps_ready", lambda _=None: True)
    monkeypatch.setattr("launcher.deps.frontend_build_stale", lambda _=None: True)
    built = {"called": False}

    def _fake_build(*_a, **_k):
        built["called"] = True
        return False, "should not build"

    monkeypatch.setattr("launcher.deps.build_frontend", _fake_build)
    monkeypatch.setattr(
        "launcher.stable_release.ensure_active_release_deployed",
        lambda _=None: (True, "ok"),
    )

    ok, msg = ensure_frontend_ready(tmp_path, for_production=True, build_policy=POLICY_LAUNCH_STABLE)
    assert ok is True
    assert built["called"] is False
    assert "стабильный релиз" in msg


def test_ready_build_assessment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_ready", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_integrity", lambda _=None: True)
    monkeypatch.setattr("launcher.frontend_build_policy.frontend_build_stale", lambda _=None: False)
    state = assess_production_build()
    assert state.status == STATUS_READY


def test_needs_recovery_only_for_ceo_missing() -> None:
    from launcher.frontend_build_policy import ProductionBuildState, needs_recovery_mode

    state = ProductionBuildState(
        status=STATUS_MISSING,
        can_launch_without_rebuild=False,
        detail="x",
    )
    assert needs_recovery_mode("owner", state)
    assert not needs_recovery_mode("development", state)
