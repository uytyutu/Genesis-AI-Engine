"""Owner-facing runtime diagnostics for Launcher support."""

from __future__ import annotations

from pathlib import Path

from launcher.deps import backend_requirements_satisfied, check_dependencies
from launcher.health import probe_backend_live, probe_frontend_live
from launcher.launch_mode import launch_mode_label, load_launch_mode
from launcher.python_runtime import (
    SUPPORTED_PYTHON_LABEL,
    resolve_any_python,
    resolve_backend_python,
)


def format_runtime_diagnostics(root: Path | None = None) -> str:
    runtime = resolve_backend_python()
    detected = resolve_any_python() if runtime is None else None
    deps = check_dependencies(root)

    if runtime:
        python_line = runtime.version_text.replace("Python ", "")
        python_cmd = runtime.display_cmd
        packages_ok, _ = backend_requirements_satisfied(runtime.argv, root)
        dependencies = "OK" if packages_ok else "Missing"
    elif detected:
        python_line = detected.version_text.replace("Python ", "")
        python_cmd = detected.display_cmd
        dependencies = f"Need {SUPPORTED_PYTHON_LABEL}"
    else:
        python_line = "не найден"
        python_cmd = "—"
        dependencies = "—"

    backend = "Running" if probe_backend_live(idle=True) else "Stopped"
    frontend = "Running" if probe_frontend_live(idle=True) else "Stopped"
    mode = launch_mode_label(load_launch_mode())

    return (
        "Runtime\n"
        f"Python: {python_line} ({python_cmd})\n"
        f"Mode: {mode}\n"
        f"Backend: {backend}\n"
        f"Frontend: {frontend}\n"
        f"Dependencies: {dependencies}"
    )
