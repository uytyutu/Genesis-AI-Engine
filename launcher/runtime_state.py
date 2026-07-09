"""Persist Genesis backend/frontend PIDs for 24/7 operation."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from launcher import paths


def _state_path(root: Path | None = None) -> Path:
    return paths.memory_dir(root) / "genesis_runtime.json"


def _pid_alive_windows(pid: int) -> bool:
    """OpenProcess is reliable on Windows; os.kill(pid, 0) can raise WinError 87."""
    import ctypes

    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    kernel32.CloseHandle(handle)
    return True


def pid_alive(pid: int | None) -> bool:
    if not pid or pid <= 0:
        return False
    if sys.platform == "win32":
        return _pid_alive_windows(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def load_state(root: Path | None = None) -> dict:
    path = _state_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def save_state(
    *,
    backend_pid: int | None,
    frontend_pid: int | None,
    root: Path | None = None,
) -> None:
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "backend_pid": backend_pid,
        "frontend_pid": frontend_pid,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_state(root: Path | None = None) -> None:
    path = _state_path(root)
    ops = _ops_path(root)
    if path.exists():
        path.unlink(missing_ok=True)
    _touch_ops_last_stopped(root)


def _ops_path(root: Path | None = None) -> Path:
    return paths.memory_dir(root) / "genesis_ops.json"


def record_ops_running(root: Path | None = None) -> None:
    from datetime import datetime, timezone

    path = _ops_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["last_started_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _touch_ops_last_stopped(root: Path | None = None) -> None:
    from datetime import datetime, timezone

    path = _ops_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data["last_stopped_at"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def load_ops(root: Path | None = None) -> dict:
    path = _ops_path(root)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def sync_state(
    backend_pid: int | None,
    frontend_pid: int | None,
    root: Path | None = None,
) -> None:
    if backend_pid and pid_alive(backend_pid):
        be = backend_pid
    else:
        be = None
    if frontend_pid and pid_alive(frontend_pid):
        fe = frontend_pid
    else:
        fe = None
    if be or fe:
        save_state(backend_pid=be, frontend_pid=fe, root=root)
    else:
        clear_state(root)
