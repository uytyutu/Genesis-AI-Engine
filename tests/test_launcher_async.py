"""Process cleanup and async status tests."""

from launcher.health import check_services_fast
from launcher.process_cleanup import kill_port_listeners, pids_on_port


def test_check_services_fast_no_slow_system_check(monkeypatch):
    calls: list[str] = []

    def track_get_json(url, timeout=8.0):
        calls.append(url)
        if "/api/status" in url:
            return {"name": "Genesis"}
        return None

    monkeypatch.setattr("launcher.health.port_open", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health._get_json", track_get_json)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)

    health = check_services_fast()
    assert health.overall == "running"
    assert not any("system-check" in u for u in calls)


def test_start_backend_skips_when_status_up(monkeypatch):
    from launcher.processes import start_backend

    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {
            "runtime_identity": "genesis-backend-v1",
            "git_commit": "abc",
            "uptime_sec": 10,
        },
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (True, "ok"),
    )
    ok, msg, proc = start_backend()
    assert ok
    assert proc is None
    assert "работает" in msg.lower()


def test_start_backend_restarts_when_stale(monkeypatch):
    from launcher.backend_identity import StopBackendResult
    from launcher.processes import start_backend

    calls: list[str] = []

    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {"runtime_identity": "old", "git_commit": "dead", "uptime_sec": 10},
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (False, "invalid runtime_identity"),
    )
    monkeypatch.setattr(
        "launcher.backend_identity.stop_backend_listeners",
        lambda root=None: StopBackendResult(port_free=True),
    )
    monkeypatch.setattr("launcher.processes.backend_python_argv", lambda: ["py", "-3.12"])
    monkeypatch.setattr("launcher.deps.ensure_backend_deps", lambda root=None: (True, "ok"))
    monkeypatch.setattr("launcher.backend_repair.prepare_backend_port", lambda root=None: (True, "port ok"))
    monkeypatch.setattr("launcher.processes.backend_dir", lambda root=None: __import__("pathlib").Path("."))
    monkeypatch.setattr("launcher.processes.log_dir", lambda root=None: __import__("pathlib").Path("."))

    class FakePopen:
        pid = 4242

        def __init__(self, *a, **k):
            calls.append("started")

    monkeypatch.setattr("launcher.processes.subprocess.Popen", FakePopen)
    monkeypatch.setattr("builtins.open", lambda *a, **k: __import__("io").StringIO())

    ok, msg, proc = start_backend()
    assert ok
    assert proc is not None
    assert proc.pid == 4242
    assert calls == ["started"]


def test_start_frontend_skips_when_port_up(monkeypatch):
    from launcher.processes import start_frontend

    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    ok, msg, proc = start_frontend()
    assert ok
    assert proc is None


def test_launch_genesis_reconnects_when_already_running(monkeypatch):
    from launcher.processes import ManagedProcesses, launch_genesis

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda *a, **k: True)
    monkeypatch.setattr(
        "launcher.backend_identity.fetch_backend_status",
        lambda timeout=8.0: {"runtime_identity": "genesis-backend-v1", "git_commit": "abc"},
    )
    monkeypatch.setattr(
        "launcher.backend_identity.backend_runtime_compatible",
        lambda root, status: (True, "ok"),
    )
    monkeypatch.setattr("launcher.processes.reconnect_managed", lambda m, r=None: True)
    monkeypatch.setattr("launcher.processes.sync_state_from_ports", lambda *a, **k: None)
    monkeypatch.setattr("launcher.processes.record_ops_running", lambda *a, **k: None)

    ok, msg = launch_genesis(ManagedProcesses(), install_deps=False)
    assert ok
    assert "24/7" in msg or "работает" in msg.lower()
