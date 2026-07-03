"""Launcher health-check sync tests."""

from __future__ import annotations

from launcher.health import ServiceHealth, owner_ready, sync_with_mission_control


def test_owner_ready_requires_backend_and_frontend():
    h = ServiceHealth(backend=True, frontend=False)
    assert not owner_ready(h)
    h.frontend = True
    assert owner_ready(h)


def test_sync_with_mission_control_marks_running(monkeypatch):
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    h = ServiceHealth(backend=True, frontend=True, overall="error", error_message="old")
    h = sync_with_mission_control(h, {"system_running": True, "greeting": "Hi"})
    assert h.overall == "running"
    assert h.error_message == ""


def test_running_without_kernel_brain_blockers():
    health = ServiceHealth(backend=True, frontend=True, kernel=False, brain=False)
    assert owner_ready(health)

    h = ServiceHealth(backend=True, frontend=True)
    h.overall = "running" if owner_ready(h) else "error"
    assert h.overall == "running"


def test_frontend_log_ignores_stale_errors(monkeypatch):
    from launcher.frontend_repair import frontend_log_indicates_error

    monkeypatch.setattr(
        "launcher.frontend_repair.read_frontend_log_tail",
        lambda root, chars=2500: (
            "cannot find module './885.js'\n"
            "started server on http://127.0.0.1:3000\n"
            "GET / 200\n"
        ),
    )
    assert not frontend_log_indicates_error(None)


def test_owner_ready_live(monkeypatch):
    from launcher.health import owner_ready_live

    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    assert owner_ready_live()
