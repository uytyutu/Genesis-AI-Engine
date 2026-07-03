"""Simple launcher log file."""

from __future__ import annotations

from datetime import datetime

from launcher import paths


def append_log(message: str) -> None:
    path = paths.log_dir() / "genesis_launcher.log"
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def read_log(tail: int = 200) -> str:
    path = paths.log_dir() / "genesis_launcher.log"
    if not path.exists():
        return "Журнал пока пуст."
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    return "\n".join(lines[-tail:])
