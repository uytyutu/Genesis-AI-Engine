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

    monkeypatch.setattr("launcher.health._get_json", track_get_json)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)

    health = check_services_fast()
    assert health.overall == "running"
    assert not any("system-check" in u for u in calls)


def test_start_backend_skips_when_status_up(monkeypatch):
    from launcher.processes import ManagedProcesses, start_backend

    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    ok, msg, proc = start_backend()
    assert ok
    assert proc is None
    assert "уже работает" in msg.lower() or "api/status" in msg.lower()


def test_start_frontend_skips_when_port_up(monkeypatch):
    from launcher.processes import start_frontend

    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    ok, msg, proc = start_frontend()
    assert ok
    assert proc is None


def test_launch_genesis_reconnects_when_already_running(monkeypatch):
    from launcher.processes import ManagedProcesses, launch_genesis

    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr("launcher.processes.reconnect_managed", lambda m, r=None: True)
    monkeypatch.setattr("launcher.processes.sync_state", lambda *a, **k: None)
    monkeypatch.setattr("launcher.processes.record_ops_running", lambda *a, **k: None)

    ok, msg = launch_genesis(ManagedProcesses(), install_deps=False)
    assert ok
    assert "24/7" in msg or "работает" in msg.lower()
