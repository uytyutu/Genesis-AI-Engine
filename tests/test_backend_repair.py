"""Tests for Backend startup recovery."""

from __future__ import annotations

from launcher.backend_repair import (
    backend_log_indicates_error,
    diagnose_backend,
    prepare_backend_port,
)


def test_backend_log_port_conflict(monkeypatch):
    monkeypatch.setattr(
        "launcher.backend_repair.read_backend_log_tail",
        lambda root, chars=6000: "ERROR: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)\n",
    )
    assert backend_log_indicates_error(None)
    diag = diagnose_backend(None, backend_exited=True)
    assert diag.can_auto_fix
    assert "8000" in diag.message


def test_prepare_backend_port_when_healthy(monkeypatch):
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
    ok, msg = prepare_backend_port(None)
    assert ok
    assert "отвечает" in msg


def test_diagnose_stale_port(monkeypatch):
    monkeypatch.setattr("launcher.deps.find_python", lambda: "py")
    monkeypatch.setattr("launcher.backend_repair._pids_on_port", lambda port: [1234])
    monkeypatch.setattr("launcher.backend_repair.backend_responds", lambda root=None, timeout=2.0: False)
    monkeypatch.setattr("launcher.backend_repair.read_backend_log_tail", lambda root, chars=6000: "")
    diag = diagnose_backend(None, backend_up=False, elapsed_sec=5)
    assert diag.issue == "stale_port"
    assert diag.can_auto_fix
