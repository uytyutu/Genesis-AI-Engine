"""Free Genesis ports and prune stale node/python listeners."""

from __future__ import annotations

import re
import signal
import subprocess
import sys
import time
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


def kill_pid(pid: int | None) -> None:
    if not pid or not pid_alive(pid):
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/F", "/T", "/PID", str(pid)],
            capture_output=True,
            creationflags=_no_window(),
        )
    else:
        try:
            import os

            os.kill(pid, signal.SIGTERM)
        except OSError:
            pass


def kill_port_listeners(port: int, *, allowed_names: tuple[str, ...]) -> list[str]:
    """Kill processes listening on port if basename matches allowed_names."""
    freed: list[str] = []
    for pid in pids_on_port(port):
        name = process_basename(pid)
        if name not in allowed_names:
            continue
        kill_pid(pid)
        freed.append(f"{name}:{pid}")
        append_log(f"Freed port {port} — stopped {name} pid={pid}")
    return freed


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
        kill_pid(pid)

    kill_port_listeners(8000, allowed_names=("python.exe", "python3.exe", "py.exe"))
    kill_port_listeners(3000, allowed_names=("node.exe", "nodejs.exe"))
