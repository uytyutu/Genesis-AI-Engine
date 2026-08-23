"""RC1-D supervisor — Frontend soft-restart without full stack reboot."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

from launcher.processes import ManagedProcesses
from launcher.service_supervisor import ServiceSupervisor


def test_supervisor_starts_and_stops(tmp_path: Path) -> None:
    managed = ManagedProcesses()
    sup = ServiceSupervisor(managed, tmp_path, poll_sec=0.2, repair_cooldown_sec=0.5)
    sup.start()
    assert sup.running
    sup.start()  # idempotent
    assert sup.running
    sup.stop()
    assert not sup.running


def test_supervisor_soft_restarts_frontend_when_backend_up(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    managed = ManagedProcesses()
    calls: list[tuple] = []

    monkeypatch.setattr(
        "launcher.health.probe_backend_live", lambda idle=False: True
    )
    monkeypatch.setattr(
        "launcher.health.probe_frontend_live",
        lambda idle=False: False,
    )

    def fake_repair(managed_arg, root, *, allow_rebuild=True):
        calls.append((managed_arg, root, allow_rebuild))
        return True, "ok"

    monkeypatch.setattr("launcher.frontend_repair.repair_frontend", fake_repair)
    monkeypatch.setattr(
        "launcher.processes.sync_state_from_ports", lambda *_a, **_k: None
    )

    sup = ServiceSupervisor(
        managed, tmp_path, poll_sec=0.15, repair_cooldown_sec=0.2
    )
    # Confirm window is 8s in module — shorten via direct tick after forcing down_since
    from launcher import service_supervisor as mod

    monkeypatch.setattr(mod, "_FE_DOWN_CONFIRM_SEC", 0.05)
    sup.start()
    deadline = time.time() + 3.0
    while time.time() < deadline and not calls:
        time.sleep(0.05)
    sup.stop()
    assert calls, "supervisor must call repair_frontend"
    assert calls[0][2] is False  # allow_rebuild=False


def test_supervisor_does_not_touch_frontend_when_backend_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    managed = ManagedProcesses()
    called = {"n": 0}
    monkeypatch.setattr(
        "launcher.health.probe_backend_live", lambda idle=False: False
    )
    monkeypatch.setattr(
        "launcher.health.probe_frontend_live", lambda idle=False: False
    )

    def fake_repair(*_a, **_k):
        called["n"] += 1
        return False, "no"

    monkeypatch.setattr("launcher.frontend_repair.repair_frontend", fake_repair)
    from launcher import service_supervisor as mod

    monkeypatch.setattr(mod, "_FE_DOWN_CONFIRM_SEC", 0.01)
    sup = ServiceSupervisor(
        managed, tmp_path, poll_sec=0.1, repair_cooldown_sec=0.1
    )
    sup.start()
    time.sleep(0.45)
    sup.stop()
    assert called["n"] == 0


def test_soft_repair_uses_dev_server_without_production_build(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """allow_rebuild=False must soft-start next:dev when BUILD_ID is missing."""
    from launcher.frontend_build_policy import POLICY_DEV_SERVER
    from launcher.frontend_repair import FrontendDiagnosis, repair_frontend

    managed = ManagedProcesses()
    policies: list[str] = []

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda idle=False: False)
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda idle=False: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda idle=False: False)
    monkeypatch.setattr("launcher.process_cleanup.stop_frontend_listeners", lambda *_a, **_k: None)
    monkeypatch.setattr("launcher.processes._kill_tree", lambda *_a, **_k: None)
    monkeypatch.setattr(
        "launcher.frontend_repair.find_npm", lambda: "npm"
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.frontend_deps_ready", lambda _=None: True
    )
    monkeypatch.setattr(
        "launcher.frontend_repair._port_conflict_in_log", lambda _=None: False
    )
    monkeypatch.setattr(
        "launcher.frontend_repair._pids_on_port", lambda _p=3000: []
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.frontend_build_integrity", lambda _=None: False
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.frontend_build_ready", lambda _=None: False
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.ensure_frontend_ready",
        lambda *_a, **_k: (True, "deps ok"),
    )
    monkeypatch.setattr(
        "launcher.frontend_repair.diagnose_frontend",
        lambda *_a, **_k: FrontendDiagnosis("missing_build", "m", True, ""),
    )

    def fake_start(root, *, managed=None, build_policy="launch_stable", **_k):
        policies.append(build_policy)
        return True, "started", None

    monkeypatch.setattr("launcher.processes.start_frontend", fake_start)
    ok, msg = repair_frontend(managed, tmp_path, allow_rebuild=False)
    assert ok is True
    assert policies == [POLICY_DEV_SERVER]
    assert "next:dev" in msg


def test_dev_cache_without_build_id_is_missing_not_corrupt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """next:dev leaves routes-manifest without BUILD_ID — must be missing, not corrupt loop."""
    from launcher import deps
    from launcher.frontend_build_policy import STATUS_MISSING, assess_production_build

    fe = tmp_path / "dashboard" / "frontend"
    nxt = fe / ".next"
    nxt.mkdir(parents=True)
    (nxt / "routes-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "server").mkdir(parents=True)
    (nxt / "server" / "pages-manifest.json").write_text("{}", encoding="utf-8")
    (nxt / "server" / "app").mkdir(parents=True)
    (nxt / "server" / "app" / "page.js").write_text("//", encoding="utf-8")
    # No BUILD_ID — classic next:dev cache

    monkeypatch.setattr(deps, "frontend_dir", lambda _=None: fe)
    monkeypatch.setattr(
        "launcher.frontend_build_policy.frontend_build_ready", deps.frontend_build_ready
    )
    monkeypatch.setattr(
        "launcher.frontend_build_policy.frontend_build_integrity",
        deps.frontend_build_integrity,
    )
    monkeypatch.setattr(
        "launcher.frontend_build_policy.frontend_build_stale", deps.frontend_build_stale
    )

    assert deps.frontend_build_ready(tmp_path) is False
    assert deps.frontend_build_integrity(tmp_path) is False
    state = assess_production_build(tmp_path)
    assert state.status == STATUS_MISSING
