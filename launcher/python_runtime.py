"""Supported Python runtime for Virtus Core backend (matches runtime.txt)."""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SUPPORTED_PYTHON_MAJOR = 3
SUPPORTED_PYTHON_MINOR = 12
SUPPORTED_PYTHON_LABEL = f"{SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR}"


@dataclass(frozen=True)
class PythonRuntimeInfo:
    argv: list[str]
    version_text: str
    major: int
    minor: int

    @property
    def display_cmd(self) -> str:
        return " ".join(self.argv)

    @property
    def is_supported(self) -> bool:
        return (
            self.major == SUPPORTED_PYTHON_MAJOR
            and self.minor == SUPPORTED_PYTHON_MINOR
        )


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def parse_python_version_text(text: str) -> tuple[int, int, int] | None:
    match = re.search(r"(\d+)\.(\d+)(?:\.(\d+))?", text)
    if not match:
        return None
    patch = int(match.group(3) or 0)
    return int(match.group(1)), int(match.group(2)), patch


def _probe_python_argv(argv: list[str]) -> PythonRuntimeInfo | None:
    try:
        result = subprocess.run(
            [*argv, "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_no_window(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    version_text = (result.stdout or result.stderr).strip()
    parsed = parse_python_version_text(version_text)
    if not parsed:
        return None
    major, minor, _ = parsed
    return PythonRuntimeInfo(argv=argv, version_text=version_text, major=major, minor=minor)


def _candidates_from_py_launcher() -> list[list[str]]:
    if sys.platform != "win32" or not shutil.which("py"):
        return []
    candidates: list[list[str]] = [[ "py", f"-{SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR}" ]]
    try:
        result = subprocess.run(
            ["py", "-0p"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=_no_window(),
        )
    except (OSError, subprocess.TimeoutExpired):
        return candidates
    if result.returncode != 0:
        return candidates
    needle = f":{SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR}"
    for line in result.stdout.splitlines():
        if needle not in line:
            continue
        match = re.search(r"\s+(C:\\\S+python\.exe)\s*$", line.strip(), re.IGNORECASE)
        if match:
            candidates.append([match.group(1)])
    return candidates


def _fallback_candidates() -> list[list[str]]:
    names = (
        f"python{SUPPORTED_PYTHON_MAJOR}.{SUPPORTED_PYTHON_MINOR}",
        f"python{SUPPORTED_PYTHON_MAJOR}{SUPPORTED_PYTHON_MINOR}",
        "python3",
        "python",
    )
    out: list[list[str]] = []
    for name in names:
        path = shutil.which(name)
        if path:
            out.append([path])
    return out


def resolve_backend_python() -> PythonRuntimeInfo | None:
    """Return supported 3.12 interpreter argv, or None if not installed."""
    seen: set[tuple[str, ...]] = set()
    for argv in [*_candidates_from_py_launcher(), *_fallback_candidates()]:
        key = tuple(argv)
        if key in seen:
            continue
        seen.add(key)
        info = _probe_python_argv(argv)
        if info and info.is_supported:
            return info
    return None


def resolve_any_python() -> PythonRuntimeInfo | None:
    """Detect default Python (for diagnostics when 3.12 is missing)."""
    candidates: list[list[str]] = []
    if sys.platform == "win32" and shutil.which("py"):
        candidates.append(["py"])
    candidates.extend(_fallback_candidates())
    if not getattr(sys, "frozen", False):
        candidates.insert(0, [sys.executable])
    seen: set[tuple[str, ...]] = set()
    for argv in candidates:
        key = tuple(argv)
        if key in seen:
            continue
        seen.add(key)
        info = _probe_python_argv(argv)
        if info:
            return info
    return None


def unsupported_python_message(detected: PythonRuntimeInfo | None = None) -> str:
    found = detected.version_text if detected else "не найден"
    return (
        f"Требуется Python {SUPPORTED_PYTHON_LABEL} (как в runtime.txt проекта).\n"
        f"Сейчас обнаружен: {found}.\n\n"
        "Автоматическая установка зависимостей пропущена.\n"
        "Установите Python 3.12 (можно рядом с 3.14) и перезапустите Virtus Core."
    )


def backend_python_argv() -> list[str] | None:
    info = resolve_backend_python()
    return info.argv if info else None
