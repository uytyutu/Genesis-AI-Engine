"""Partial 24/7 reconnect must not mask dead frontend."""

from launcher.processes import ManagedProcesses, reconnect_managed


def test_reconnect_false_when_backend_only(monkeypatch):
    managed = ManagedProcesses()
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: False)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {
            "runtime_identity": "genesis-backend-v1",
            "git_commit": "abc",
            "uptime_sec": 5,
        },
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (True, "ok"),
    )
    monkeypatch.setattr("launcher.processes.load_state", lambda root=None: {"backend_pid": 999, "frontend_pid": None})
    monkeypatch.setattr("launcher.processes.pid_alive", lambda pid: pid == 999)
    monkeypatch.setattr("launcher.processes.append_log", lambda msg: None)
    monkeypatch.setattr("launcher.process_cleanup.backend_listener_pids", lambda: [999])
    monkeypatch.setattr("launcher.process_cleanup.frontend_listener_pids", lambda: [])

    assert reconnect_managed(managed) is False


def test_reconnect_true_when_owner_ready(monkeypatch):
    managed = ManagedProcesses()
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {
            "runtime_identity": "genesis-backend-v1",
            "git_commit": "abc",
            "uptime_sec": 5,
        },
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (True, "ok"),
    )
    monkeypatch.setattr("launcher.processes.load_state", lambda root=None: {"backend_pid": 1, "frontend_pid": 2})
    monkeypatch.setattr("launcher.processes.pid_alive", lambda pid: True)
    monkeypatch.setattr("launcher.process_cleanup.backend_listener_pids", lambda: [1])
    monkeypatch.setattr("launcher.process_cleanup.frontend_listener_pids", lambda: [2])

    assert reconnect_managed(managed) is True


def test_reconnect_kills_stale_backend(monkeypatch):
    managed = ManagedProcesses()
    stopped: list[str] = []
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {"runtime_identity": "old"},
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (False, "stale"),
    )
    monkeypatch.setattr(
        "launcher.backend_identity.stop_backend_listeners",
        lambda root=None, managed=None: stopped.append("stopped") or ["python:1"],
    )
    monkeypatch.setattr("launcher.processes.load_state", lambda root=None: {})
    monkeypatch.setattr("launcher.process_cleanup.backend_listener_pids", lambda: [])
    monkeypatch.setattr("launcher.process_cleanup.frontend_listener_pids", lambda: [2])

    assert reconnect_managed(managed) is False
    assert stopped == ["stopped"]
