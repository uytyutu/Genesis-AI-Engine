"""Launch Cursor IDE for Genesis workspace (semi-auto bridge until R8 API)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from app.integration.genesis_brain.public_brand import BRAND_NAME


def find_cursor_cli() -> str | None:
    found = shutil.which("cursor")
    if found:
        return found
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA", "")
        candidates = [
            Path(local) / "Programs" / "cursor" / "Cursor.exe",
            Path(local) / "Programs" / "Cursor" / "Cursor.exe",
        ]
        for path in candidates:
            if path.is_file():
                return str(path)
    return None


def open_workspace(project_root: Path | None) -> tuple[bool, str]:
    """Open Genesis repo in Cursor. Prompt must be pasted by owner (no public task API yet)."""
    if project_root is None or not project_root.is_dir():
        return False, f"Корень проекта {BRAND_NAME} не найден."

    cli = find_cursor_cli()
    if not cli:
        return (
            False,
            "Cursor CLI не найден. Установите Cursor и добавьте в PATH, "
            "или откройте папку проекта вручную.",
        )

    try:
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0  # type: ignore[attr-defined]
        subprocess.Popen(
            [cli, str(project_root)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=flags,
        )
    except OSError as exc:
        return False, f"Не удалось открыть Cursor: {exc}"

    return True, f"Cursor открыт на проекте: {project_root.name}"
