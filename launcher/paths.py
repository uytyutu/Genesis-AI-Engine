"""Resolve Genesis project paths from script or frozen exe."""

from __future__ import annotations

import json
import sys
from pathlib import Path

MARKERS = ("PROJECT_STATE.md", "dashboard", "kernel")
FRONTEND_PACKAGE = Path("dashboard") / "frontend" / "package.json"
BACKEND_MAIN = Path("dashboard") / "backend" / "app" / "main.py"


def _is_genesis_root(candidate: Path) -> bool:
    """Root must have markers AND a real Mission Control package.json."""
    if not all((candidate / marker).exists() for marker in MARKERS):
        return False
    return (candidate / FRONTEND_PACKAGE).is_file() and (candidate / BACKEND_MAIN).is_file()


def _find_root_from(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if _is_genesis_root(candidate):
            return candidate
    raise FileNotFoundError(f"Genesis root not found from {start}")


def _read_saved_project_root() -> Path | None:
    """Load persisted root without calling find_project_root (avoids circular imports)."""
    search_starts: list[Path] = []
    if getattr(sys, "frozen", False):
        search_starts.append(Path(sys.executable).resolve().parent)
    search_starts.append(Path(__file__).resolve().parent.parent)

    config_rels = (
        Path("dashboard") / "backend" / "memory" / "launcher_config.json",
        Path("memory") / "launcher_config.json",
    )

    seen: set[Path] = set()
    for start in search_starts:
        for candidate in (start, *start.parents):
            resolved = candidate.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            for rel in config_rels:
                cfg_path = resolved / rel
                if not cfg_path.is_file():
                    continue
                try:
                    data = json.loads(cfg_path.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                raw = str(data.get("project_root", "") or "").strip()
                if not raw:
                    continue
                saved = Path(raw).resolve()
                if _is_genesis_root(saved):
                    return saved
    return None


def find_project_root(start: Path | None = None) -> Path:
    """Walk upward until Genesis project root is found."""
    if start is not None:
        return _find_root_from(start.resolve())

    saved = _read_saved_project_root()
    if saved is not None:
        return saved

    candidates: list[Path] = []
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent)
        candidates.append(Path.cwd())
    else:
        candidates.append(Path(__file__).resolve().parent.parent)

    seen: set[Path] = set()
    for origin in candidates:
        resolved = origin.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        try:
            return _find_root_from(resolved)
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        "Не найдена папка проекта Genesis.\n"
        "Убедитесь, что Virtus Core-AI-Engine установлен целиком и содержит "
        "dashboard/frontend/package.json."
    )


def validate_layout(root: Path | None = None) -> tuple[bool, str]:
    """Check Mission Control path exists — separate from stale .next build errors."""
    try:
        root_path = find_project_root(root)
    except FileNotFoundError as exc:
        return False, str(exc)

    fe = root_path / "dashboard" / "frontend"
    pkg = fe / "package.json"
    if not fe.is_dir():
        return False, (
            f"Папка Mission Control не найдена:\n{fe}\n\n"
            "Проверьте, что проект Genesis-AI-Engine не был перемещён неполностью."
        )
    if not pkg.is_file():
        return False, (
            f"Неверный каталог Frontend (нет package.json):\n{fe}\n\n"
            "Ожидается: dashboard/frontend/package.json"
        )
    return True, str(fe.resolve())


def backend_dir(root: Path | None = None) -> Path:
    return find_project_root(root) / "dashboard" / "backend"


def frontend_dir(root: Path | None = None) -> Path:
    root_path = find_project_root(root)
    fe = root_path / "dashboard" / "frontend"
    if not (fe / "package.json").is_file():
        raise FileNotFoundError(
            f"Mission Control не найден: {fe}\n"
            "Ожидается dashboard/frontend/package.json в корне Genesis."
        )
    return fe


def memory_dir(root: Path | None = None) -> Path:
    return backend_dir(root) / "memory"


def log_dir(root: Path | None = None) -> Path:
    path = find_project_root(root) / "launcher" / "logs"
    path.mkdir(parents=True, exist_ok=True)
    return path
