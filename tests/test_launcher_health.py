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


def test_probe_skips_http_when_port_closed(monkeypatch):
    from launcher.health import probe_backend_live, probe_frontend_live

    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: False)
    calls: list[str] = []

    def track_get_json(url, timeout=8.0):
        calls.append(url)
        return {"ok": True}

    monkeypatch.setattr("launcher.health._get_json", track_get_json)
    monkeypatch.setattr("launcher.health._probe_url", lambda *a, **k: True)

    assert not probe_backend_live()
    assert not probe_frontend_live()
    assert calls == []


def test_gather_status_single_probe_pass(monkeypatch):
    from launcher.processes import ManagedProcesses
    from launcher.status_worker import gather_status

    probe_calls = {"n": 0}

    def count_probe(*, idle=False):
        probe_calls["n"] += 1
        return True, True

    monkeypatch.setattr("launcher.status_worker.probe_services_live", count_probe)
    monkeypatch.setattr("launcher.status_worker.reconnect_managed", lambda *a, **k: None)
    monkeypatch.setattr("launcher.status_worker.fetch_mission_control", lambda **k: {"system_running": True})
    monkeypatch.setattr(
        "launcher.status_worker._cached_dependencies",
        lambda root: type("D", (), {"node_ok": True, "frontend_deps_ok": True, "python_ok": True})(),
    )

    gather_status(ManagedProcesses(), None, frontend_exited=False, launcher_idle=True)
    assert probe_calls["n"] == 1
