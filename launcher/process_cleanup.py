"""Free Genesis ports and prune stale node/python listeners."""

from __future__ import annotations

import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from launcher.log_util import append_log
from launcher.runtime_state import load_state, pid_alive

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def pids_on_port(port: int) -> list[int]:
    if sys.platform != "win32":
        return []
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=_no_window(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    needle = f":{port}"
    pids: list[int] = []
    for line in result.stdout.splitlines():
        upper = line.upper()
        if needle not in line or "LISTENING" not in upper:
            continue
        match = re.search(r"(\d+)\s*$", line.strip())
        if match:
            pids.append(int(match.group(1)))
    return list(dict.fromkeys(pids))


def process_basename(pid: int) -> str:
    if sys.platform != "win32":
        return ""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_no_window(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0 or not result.stdout.strip():
        return ""
    line = result.stdout.strip().splitlines()[0]
    if line.startswith('"'):
        return line.split('"')[1].lower()
    return line.split(",")[0].lower()


@dataclass(frozen=True)
class KillResult:
    pid: int
    ok: bool
    reason: str


def _classify_taskkill_failure(returncode: int, detail: str) -> str:
    low = detail.lower()
    if returncode == 128 and ("не найден" in low or "not found" in low or "не удается найти" in low):
        return "process_not_found"
    if "access is denied" in low or "отказано в доступе" in low:
        return "access_denied"
    if returncode != 0:
        return f"taskkill_failed rc={returncode}"
    return "taskkill_failed"


def kill_pid(pid: int | None) -> KillResult:
    if not pid:
        return KillResult(0, True, "no_pid")
    if not pid_alive(pid):
        return KillResult(pid, True, "already_stopped")
    if sys.platform == "win32":
        result = subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            text=True,
            creationflags=_no_window(),
        )
        detail = (result.stderr or result.stdout or "").strip()
        if result.returncode != 0:
            reason = _classify_taskkill_failure(result.returncode, detail)
            if detail:
                reason = f"{reason}: {detail[:180]}"
            return KillResult(pid, False, reason)
        if pid_alive(pid):
            return KillResult(pid, False, "process_still_alive")
        return KillResult(pid, True, "ok")
    try:
        import os

        os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return KillResult(pid, False, f"sigterm_failed: {exc}")
    if pid_alive(pid):
        return KillResult(pid, False, "process_still_alive")
    return KillResult(pid, True, "ok")


def kill_port_listeners(port: int, *, allowed_names: tuple[str, ...]) -> list[KillResult]:
    """Kill processes listening on port if basename matches allowed_names."""
    results: list[KillResult] = []
    for pid in pids_on_port(port):
        name = process_basename(pid)
        if name not in allowed_names:
            append_log(
                f"Skip port {port} pid={pid} ({name or 'unknown'}) — not in allowed list"
            )
            continue
        outcome = kill_pid(pid)
        results.append(outcome)
        if outcome.ok:
            append_log(f"Freed port {port} — stopped {name} pid={pid}")
        else:
            append_log(f"Failed to stop {name} pid={pid} on port {port}: {outcome.reason}")
    return results


def wait_port_free(port: int, *, timeout: float = 15.0, interval: float = 0.5) -> bool:
    """Block until no process listens on port or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not pids_on_port(port):
            return True
        time.sleep(interval)
    return not pids_on_port(port)


def frontend_listener_pids() -> list[int]:
    return pids_on_port(3000)


def backend_listener_pids() -> list[int]:
    return pids_on_port(8000)


def frontend_port_listening() -> bool:
    return bool(frontend_listener_pids())


def stop_frontend_listeners(
    root: Path | None = None,
    managed: ManagedProcesses | None = None,
) -> None:
    """Stop every Genesis frontend process before mutating .next or rebuilding."""
    from launcher.processes import _kill_tree

    if managed is not None:
        _kill_tree(managed.frontend)
        managed.frontend = None

    state = load_state(root)
    kill_pid(state.get("frontend_pid"))
    kill_port_listeners(3000, allowed_names=("node.exe", "nodejs.exe"))
    time.sleep(0.5)


def kill_genesis_ports(root: Path | None = None) -> None:
    """Stop Genesis Backend/Frontend listeners on :8000 and :3000."""
    state = load_state(root)
    for pid in (state.get("backend_pid"), state.get("frontend_pid")):
        outcome = kill_pid(pid)
        if pid and not outcome.ok:
            append_log(f"Failed to stop saved pid={pid}: {outcome.reason}")

    kill_port_listeners(8000, allowed_names=("python.exe", "python3.exe", "py.exe"))
    kill_port_listeners(3000, allowed_names=("node.exe", "nodejs.exe"))

    if not wait_port_free(8000, timeout=20.0):
        remaining = pids_on_port(8000)
        append_log(f"WARNING: port 8000 still occupied after stop (timeout): {remaining}")
        for pid in remaining:
            name = process_basename(pid)
            if name in ("python.exe", "python3.exe", "py.exe"):
                outcome = kill_pid(pid)
                if not outcome.ok:
                    append_log(f"Retry stop pid={pid} failed: {outcome.reason}")
        if not wait_port_free(8000, timeout=10.0):
            append_log(f"WARNING: port 8000 still occupied after retry: {pids_on_port(8000)}")

    if not wait_port_free(3000, timeout=15.0):
        remaining = pids_on_port(3000)
        append_log(f"WARNING: port 3000 still occupied after stop (timeout): {remaining}")
