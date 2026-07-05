"""Partial 24/7 reconnect must not mask dead frontend."""

from launcher.processes import ManagedProcesses, reconnect_managed


def test_reconnect_false_when_backend_only(monkeypatch):
    managed = ManagedProcesses()
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: False)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: False)
    monkeypatch.setattr("launcher.processes.load_state", lambda root=None: {"backend_pid": 999, "frontend_pid": None})
    monkeypatch.setattr("launcher.processes.pid_alive", lambda pid: pid == 999)
    monkeypatch.setattr("launcher.processes.append_log", lambda msg: None)

    assert reconnect_managed(managed) is False


def test_reconnect_true_when_owner_ready(monkeypatch):
    managed = ManagedProcesses()
    monkeypatch.setattr("launcher.health.probe_backend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.probe_frontend_live", lambda *a, **k: True)
    monkeypatch.setattr("launcher.health.owner_ready_live", lambda: True)
    monkeypatch.setattr("launcher.processes.load_state", lambda root=None: {"backend_pid": 1, "frontend_pid": 2})
    monkeypatch.setattr("launcher.processes.pid_alive", lambda pid: True)

    assert reconnect_managed(managed) is True
