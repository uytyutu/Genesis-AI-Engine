"""Backend import preflight — fail fast with a clear error (no Repair Loop)."""

from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from launcher.paths import backend_dir
from launcher.python_runtime import resolve_backend_python


@dataclass
class BackendPreflight:
    ok: bool
    issue: str
    message: str
    detail: str = ""
    can_auto_fix: bool = False


def run_backend_import_preflight(root: Path | None = None) -> BackendPreflight:
    """
    Run `from app.main import app` in a subprocess with PYTHONPATH=backend.
    If this fails, starting uvicorn will fail the same way — do not Repair-loop.
    """
    python = resolve_backend_python()
    if not python:
        return BackendPreflight(
            ok=False,
            issue="python_missing",
            message="Python 3.12 не найден — установите runtime перед запуском Backend.",
            can_auto_fix=False,
        )

    be = backend_dir(root)
    env = os.environ.copy()
    # Prefer backend on PYTHONPATH (Windows pathsep)
    env["PYTHONPATH"] = str(be) + os.pathsep + env.get("PYTHONPATH", "")

    creationflags = 0
    if sys.platform == "win32":
        creationflags = subprocess.CREATE_NO_WINDOW  # type: ignore[attr-defined]

    try:
        proc = subprocess.run(
            [
                *python.argv,
                "-c",
                "from app.main import app; print('OK', getattr(app, 'title', 'app'))",
            ],
            cwd=str(be),
            env=env,
            capture_output=True,
            text=True,
            timeout=90,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        return BackendPreflight(
            ok=False,
            issue="import_timeout",
            message="Backend import check timed out (90s).",
            can_auto_fix=False,
        )
    except OSError as exc:
        return BackendPreflight(
            ok=False,
            issue="import_spawn_failed",
            message=f"Could not run Python for import check: {exc}",
            can_auto_fix=False,
        )

    if proc.returncode == 0 and "OK" in (proc.stdout or ""):
        return BackendPreflight(
            ok=True,
            issue="ok",
            message="Backend import OK",
            detail=(proc.stdout or "").strip()[:200],
            can_auto_fix=False,
        )

    err = (proc.stderr or proc.stdout or "").strip()
    # Prefer last meaningful traceback line
    lines = [ln.strip() for ln in err.splitlines() if ln.strip()]
    focus = "\n".join(lines[-12:]) if lines else "unknown import error"
    # Human headline
    headline = "Backend startup failed: import error in app.main"
    for ln in reversed(lines):
        if "NameError" in ln or "ImportError" in ln or "ModuleNotFoundError" in ln:
            headline = f"Backend startup failed: {ln[:160]}"
            break
        if "Error" in ln and "File " not in ln:
            headline = f"Backend startup failed: {ln[:160]}"
            break

    can_fix = "ModuleNotFoundError" in err or "No module named" in err
    return BackendPreflight(
        ok=False,
        issue="import_error",
        message=headline,
        detail=focus[:2500],
        can_auto_fix=can_fix,
    )


def format_preflight_failure(pf: BackendPreflight) -> str:
    parts = [pf.message]
    if pf.detail:
        parts.append("\n--- import check ---")
        parts.append(pf.detail)
    if not pf.can_auto_fix:
        parts.append(
            "\nRepair Loop пропущен: это ошибка кода, не порта. "
            "Исправьте app.main / schemas и перезапустите."
        )
    return "\n".join(parts)
