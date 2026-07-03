"""Backend startup recovery — stale port 8000, crashed uvicorn, deps."""

from __future__ import annotations

import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from launcher.deps import find_python, install_backend_deps
from launcher.health import probe_backend
from launcher.log_util import append_log
from launcher.paths import log_dir

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses


@dataclass
class BackendDiagnosis:
    issue: str
    message: str
    can_auto_fix: bool
    log_excerpt: str = ""


_ERROR_MARKERS: tuple[tuple[str, str, bool], ...] = (
    ("10048", "Порт 8000 занят — Genesis освободит и перезапустит Backend.", True),
    ("eaddrinuse", "Порт 8000 занят — Genesis освободит и перезапустит Backend.", True),
    ("address already in use", "Порт 8000 занят — Genesis освободит и перезапустит Backend.", True),
    ("modulenotfounderror", "Не установлены Python-зависимости Backend.", True),
    ("importerror", "Ошибка импорта Backend — проверьте requirements.txt.", True),
    ("traceback", "Backend завершился с ошибкой Python.", True),
)


def read_backend_log_tail(root: Path | None = None, chars: int = 6000) -> str:
    path = log_dir(root) / "backend.log"
    if not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")[-chars:]
    except OSError:
        return ""


def backend_responds(root: Path | None = None, timeout: float = 8.0) -> bool:
    return probe_backend(timeout=timeout, attempts=2)


def backend_log_indicates_error(root: Path | None = None) -> bool:
    tail = read_backend_log_tail(root).lower()
    return any(marker in tail for marker, _, _ in _ERROR_MARKERS)


def _log_excerpt(root: Path | None, lines: int = 20) -> str:
    tail = read_backend_log_tail(root, chars=8000)
    if not tail:
        return ""
    parts = [ln.strip() for ln in tail.splitlines() if ln.strip()]
    return "\n".join(parts[-lines:])


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def _pids_on_port(port: int) -> list[int]:
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


def _process_basename(pid: int) -> str:
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


def prepare_backend_port(root: Path | None = None) -> tuple[bool, str]:
    """Free port 8000 when a stale Python listener blocks a healthy Backend."""
    if backend_responds(root, timeout=2.0):
        return True, "Backend уже отвечает на :8000"

    freed: list[str] = []
    for pid in _pids_on_port(8000):
        name = _process_basename(pid)
        if name not in ("python.exe", "python3.exe", "py.exe"):
            continue
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                capture_output=True,
                creationflags=_no_window(),
            )
        else:
            import os
            import signal

            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                pass
        freed.append(f"{name}:{pid}")
        append_log(f"Freed backend port 8000 — stopped {name} pid={pid}")

    if freed:
        time.sleep(1.5)
        if backend_responds(root, timeout=4.0):
            return True, f"Backend снова отвечает после освобождения порта ({', '.join(freed)})"
        return True, f"Освобождён порт 8000 ({', '.join(freed)})"

    if _pids_on_port(8000):
        return False, "Порт 8000 занят не-Python процессом — закройте его вручную"
    return True, "Порт 8000 свободен"


def diagnose_backend(
    root: Path | None = None,
    *,
    backend_exited: bool = False,
    backend_up: bool = False,
    elapsed_sec: float = 0,
) -> BackendDiagnosis:
    excerpt = _log_excerpt(root)
    lowered = excerpt.lower()

    if backend_up:
        return BackendDiagnosis("ok", "Backend работает.", False, excerpt)

    if not find_python():
        return BackendDiagnosis(
            "python_missing",
            "Python не найден. Установите Python 3.11+ или нажмите «Запустить» в Genesis.",
            False,
            excerpt,
        )

    for marker, human, can_fix in _ERROR_MARKERS:
        if marker in lowered:
            return BackendDiagnosis(marker.replace(" ", "_"), f"Backend: {human}", can_fix, excerpt)

    if _pids_on_port(8000) and not backend_up:
        return BackendDiagnosis(
            "stale_port",
            "Порт 8000 занят, но Backend не отвечает — зависший процесс Python.",
            True,
            excerpt,
        )

    if backend_exited:
        return BackendDiagnosis(
            "process_crashed",
            f"Backend завершился.\n\n{excerpt or 'См. backend.log'}",
            True,
            excerpt,
        )

    if elapsed_sec >= 45 and not backend_up:
        return BackendDiagnosis(
            "timeout",
            f"Backend не ответил за {int(elapsed_sec)} с. Проверьте backend.log.",
            True,
            excerpt,
        )

    return BackendDiagnosis("starting", "Backend запускается…", False, excerpt)


def repair_backend(
    managed: ManagedProcesses,
    root: Path | None = None,
) -> tuple[bool, str]:
    """Kill stale Backend, reinstall deps if needed, restart uvicorn."""
    from launcher.health import owner_ready_live, probe_backend_live
    from launcher.processes import _kill_tree, start_backend

    if owner_ready_live():
        return True, "Genesis уже готов — Backend и Frontend отвечают"
    if probe_backend_live():
        return True, "Backend уже отвечает на /api/status — ремонт не нужен"

    diag = diagnose_backend(root, backend_exited=True)
    steps: list[str] = []

    _kill_tree(managed.backend)
    managed.backend = None

    ok, msg = prepare_backend_port(root)
    steps.append(msg)
    if not ok:
        return False, f"{diag.message}\n\n{msg}"

    if backend_responds(root):
        steps.append("Backend отвечает — перезапуск не нужен")
        return True, "\n".join(steps)

    ok, msg = install_backend_deps(root)
    steps.append(msg)
    if not ok:
        return False, f"{diag.message}\n\n{msg}"

    ok, msg, proc = start_backend(root)
    steps.append(msg)
    if not ok:
        return False, f"{diag.message}\n\n{msg}"

    managed.backend = proc
    append_log("Backend repair: restarted uvicorn on :8000")

    for _ in range(20):
        if backend_responds(root, timeout=2.0):
            steps.append("Backend отвечает на /api/status")
            return True, "\n".join(steps)
        time.sleep(0.75)

    return False, "\n".join(steps + ["Backend запущен, но пока не отвечает — см. backend.log"])


def format_backend_failure(diag: BackendDiagnosis, root: Path | None = None) -> str:
    parts = [diag.message]
    excerpt = diag.log_excerpt or _log_excerpt(root)
    if excerpt:
        parts.append("\n--- backend.log ---")
        parts.append(excerpt)
    return "\n".join(parts)
