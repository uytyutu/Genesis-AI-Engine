"""Windows pid_alive and port-kill verification tests."""

from __future__ import annotations

import os
import sys

import pytest

from launcher.process_cleanup import KillResult, kill_port_listeners
from launcher.runtime_state import pid_alive


def test_kill_port_listeners_requires_process_gone(monkeypatch):
    logs: list[str] = []
    monkeypatch.setattr("launcher.process_cleanup.append_log", logs.append)
    monkeypatch.setattr("launcher.process_cleanup.pids_on_port", lambda port: [123])
    monkeypatch.setattr("launcher.process_cleanup.process_basename", lambda pid: "node.exe")
    monkeypatch.setattr(
        "launcher.process_cleanup.kill_pid",
        lambda pid: KillResult(pid, True, "not_running"),
    )
    monkeypatch.setattr("launcher.process_cleanup.pid_alive", lambda pid: True)

    results = kill_port_listeners(3000, allowed_names=("node.exe",))

    assert len(results) == 1
    assert results[0].ok is False
    assert results[0].reason == "process_still_alive"
    assert any("Failed to stop" in line for line in logs)
    assert not any("Freed port" in line for line in logs)


def test_kill_port_listeners_logs_freed_only_when_gone(monkeypatch):
    logs: list[str] = []
    calls = {"n": 0}

    def port_pids(port: int) -> list[int]:
        calls["n"] += 1
        return [456] if calls["n"] == 1 else []

    monkeypatch.setattr("launcher.process_cleanup.append_log", logs.append)
    monkeypatch.setattr("launcher.process_cleanup.pids_on_port", port_pids)
    monkeypatch.setattr("launcher.process_cleanup.process_basename", lambda pid: "node.exe")
    monkeypatch.setattr(
        "launcher.process_cleanup.kill_pid",
        lambda pid: KillResult(pid, True, "ok"),
    )
    monkeypatch.setattr("launcher.process_cleanup.pid_alive", lambda pid: False)

    results = kill_port_listeners(3000, allowed_names=("node.exe",))

    assert results[0].ok is True
    assert any("Freed port 3000" in line for line in logs)


@pytest.mark.skipif(sys.platform != "win32", reason="WinAPI pid check")
def test_pid_alive_open_process_vs_os_kill():
    """Living processes must be visible to pid_alive even when os.kill(pid,0) fails."""
    import ctypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, os.getpid())
    assert handle, "OpenProcess must open the current process"

    kernel32.CloseHandle(handle)
    assert pid_alive(os.getpid()) is True

    os_kill_failed = False
    try:
        os.kill(os.getpid(), 0)
    except OSError:
        os_kill_failed = True

    if os_kill_failed:
        assert pid_alive(os.getpid()) is True
