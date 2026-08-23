"""Simple launcher log file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from launcher import paths


def append_log(message: str) -> None:
    path = paths.log_dir() / "genesis_launcher.log"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{stamp}] {message}\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)


def write_crash_log(message: str, *, exc: BaseException | None = None) -> Path:
    """RC1: always leave a crash breadcrumb for Owner diagnosis."""
    log_root = paths.log_dir()
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    body = f"[{stamp}] {message}\n"
    if exc is not None:
        import traceback

        body += "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    crash_path = log_root / "launcher_crash.log"
    startup_path = log_root / "startup.log"
    for path in (crash_path, startup_path):
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(body)
    append_log(f"CRASH recorded → {crash_path.name}")
    return crash_path


def read_log(tail: int = 200) -> str:
    path = paths.log_dir() / "genesis_launcher.log"
    if not path.exists():
        return "Журнал пока пуст."
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-tail:])
