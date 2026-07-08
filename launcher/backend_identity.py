"""Backend runtime identity — git commit, process age, reconnect eligibility."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from launcher.health import BACKEND_URL, _get_json
from launcher.log_util import append_log
from launcher.paths import find_project_root

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses

VALID_RUNTIME_IDENTITIES = frozenset({"genesis-backend-v1"})
MAX_BACKEND_UPTIME_SEC = 86400.0  # 24h — stale .env / long-lived orphan guard


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def expected_git_commit(root: Path | None = None) -> str:
    try:
        repo = find_project_root(root)
        result = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=5,
            creationflags=_no_window(),
        )
        if result.returncode == 0:
            commit = result.stdout.strip()
            if commit:
                return commit
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        pass
    return "unknown"


def fetch_backend_status(timeout: float = 8.0) -> dict | None:
    return _get_json(f"{BACKEND_URL}/api/status", timeout=timeout)


def is_runtime_identity_valid(status: dict | None) -> bool:
    if not status:
        return False
    identity = str(status.get("runtime_identity") or "").strip()
    return identity in VALID_RUNTIME_IDENTITIES


def git_commit_matches(root: Path | None, status: dict | None) -> bool:
    if not status:
        return False
    expected = expected_git_commit(root)
    running = str(status.get("git_commit") or "").strip()
    if not running:
        return False
    if expected == "unknown" or running == "unknown":
        return expected == running
    return expected == running


def process_age_acceptable(status: dict | None) -> bool:
    if not status:
        return False
    uptime = status.get("uptime_sec")
    if uptime is None:
        return False
    try:
        return float(uptime) <= MAX_BACKEND_UPTIME_SEC
    except (TypeError, ValueError):
        return False


def backend_runtime_compatible(
    root: Path | None,
    status: dict | None,
) -> tuple[bool, str]:
    if status is None:
        return False, "backend /api/status unreachable"
    if not is_runtime_identity_valid(status):
        identity = status.get("runtime_identity")
        return False, f"invalid or missing runtime_identity ({identity!r})"
    if not git_commit_matches(root, status):
        return (
            False,
            f"git_commit mismatch: running={status.get('git_commit')!r} "
            f"expected={expected_git_commit(root)!r}",
        )
    if not process_age_acceptable(status):
        return False, f"process too old: uptime_sec={status.get('uptime_sec')}"
    return True, "ok"


def stop_backend_listeners(
    root: Path | None = None,
    managed: ManagedProcesses | None = None,
) -> list[str]:
    """Terminate every Genesis backend on :8000 and wait until the port is free."""
    from launcher.process_cleanup import (
        backend_listener_pids,
        kill_pid,
        kill_port_listeners,
        wait_port_free,
    )
    from launcher.processes import _kill_tree
    from launcher.runtime_state import load_state

    stopped: list[str] = []
    if managed is not None:
        if managed.backend is not None:
            stopped.append(f"managed:{managed.backend.pid}")
        _kill_tree(managed.backend)
        managed.backend = None

    state = load_state(root)
    saved_pid = state.get("backend_pid")
    if saved_pid:
        kill_pid(saved_pid)
        stopped.append(f"state:{saved_pid}")

    stopped.extend(
        kill_port_listeners(8000, allowed_names=("python.exe", "python3.exe", "py.exe"))
    )

    for pid in backend_listener_pids():
        kill_pid(pid)
        stopped.append(f"port:{pid}")

    if wait_port_free(8000, timeout=20.0):
        append_log("Port 8000 released after backend stop")
    else:
        remaining = backend_listener_pids()
        append_log(f"WARNING: port 8000 still held after stop: {remaining}")
    return stopped
