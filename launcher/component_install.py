"""Install missing runtime components on Windows (owner-friendly)."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import webbrowser
from pathlib import Path

NODE_URL = "https://nodejs.org/en/download"
PYTHON_URL = "https://www.python.org/downloads/"

_WINGET_PACKAGES = {
    "node": "OpenJS.NodeJS.LTS",
    "python": "Python.Python.3.12",
}


def _no_window() -> int:
    if sys.platform == "win32":
        return subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]
    return 0


def find_winget() -> str | None:
    return shutil.which("winget")


def install_component(component: str, *, log_dir: Path | None = None) -> tuple[bool, str]:
    """Try silent install via winget. component: 'node' | 'python'."""
    package = _WINGET_PACKAGES.get(component)
    if not package:
        return False, f"Неизвестный компонент: {component}"

    winget = find_winget()
    if not winget:
        return False, "winget недоступен на этом компьютере"

    log_path = (log_dir or Path.cwd()) / f"install_{component}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as log:
        log.write(f"\n--- winget install {package} ---\n")
        log.flush()
        try:
            result = subprocess.run(
                [
                    winget,
                    "install",
                    "-e",
                    "--id",
                    package,
                    "--accept-package-agreements",
                    "--accept-source-agreements",
                    "--disable-interactivity",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                creationflags=_no_window(),
                timeout=900,
                env=os.environ.copy(),
            )
        except subprocess.TimeoutExpired:
            return False, f"Установка заняла слишком много времени. См. {log_path}"

    if result.returncode not in (0, 2316632107, -1978335212):
        # 2316632107 / negative = already installed on some winget versions
        return False, f"winget завершился с кодом {result.returncode}. См. {log_path}"

    return True, f"{component} установлен"


def open_component_site(component: str) -> None:
    url = NODE_URL if component == "node" else PYTHON_URL
    webbrowser.open(url)
