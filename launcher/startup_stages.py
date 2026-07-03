"""Sequential startup: Backend → Frontend. No frontend repair while backend is down."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

from launcher.health import probe_backend_live, probe_frontend_live

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses

Stage = Literal["ready", "backend_down", "frontend_down"]


@dataclass
class StageAssessment:
    stage: Stage
    message: str
    backend_up: bool
    frontend_up: bool


def assess_startup(root=None) -> StageAssessment:
    """Stage 1: Backend. Stage 2: Frontend (only if backend up). Stage 3: ready."""
    from launcher.backend_repair import diagnose_backend, format_backend_failure
    from launcher.frontend_repair import diagnose_frontend, format_failure_message
    from launcher.health import owner_ready_live

    if owner_ready_live():
        return StageAssessment(
            stage="ready",
            message="✔ Genesis полностью готов",
            backend_up=True,
            frontend_up=True,
        )

    backend_up = probe_backend_live()
    frontend_up = probe_frontend_live() if backend_up else False

    if not backend_up:
        diag = diagnose_backend(root, backend_up=False, elapsed_sec=0)
        body = format_backend_failure(diag, root)
        return StageAssessment(
            stage="backend_down",
            message=f"Backend не запущен.\n\n{body}",
            backend_up=False,
            frontend_up=frontend_up,
        )

    if not frontend_up:
        diag = diagnose_frontend(root, frontend_up=False, elapsed_sec=0)
        return StageAssessment(
            stage="frontend_down",
            message=format_failure_message(diag, root),
            backend_up=True,
            frontend_up=False,
        )

    return StageAssessment(
        stage="ready",
        message="✔ Genesis полностью готов",
        backend_up=True,
        frontend_up=True,
    )


def failure_for_stage(
    root=None,
    *,
    frontend_exited: bool = False,
    elapsed_sec: float = 0,
) -> str:
    if probe_backend_live() and probe_frontend_live():
        return ""
    assessment = assess_startup(root)
    if assessment.stage == "ready":
        return ""
    if assessment.stage == "backend_down":
        return assessment.message
    if frontend_exited and assessment.stage == "frontend_down":
        from launcher.frontend_repair import diagnose_frontend, format_failure_message

        diag = diagnose_frontend(
            root,
            frontend_exited=True,
            frontend_up=False,
            elapsed_sec=elapsed_sec,
        )
        return format_failure_message(diag, root)
    return assessment.message


def repair_staged(
    managed: ManagedProcesses,
    root=None,
    *,
    fix_backend: bool = True,
    fix_frontend: bool = True,
) -> tuple[bool, str]:
    """Repair only what the current stage requires — never frontend before backend."""
    from launcher.backend_repair import repair_backend
    from launcher.frontend_repair import repair_frontend
    from launcher.health import owner_ready_live

    if owner_ready_live():
        return True, "✔ Genesis полностью готов — ремонт не нужен"

    assessment = assess_startup(root)
    if assessment.stage == "ready":
        return True, assessment.message

    steps: list[str] = []

    if assessment.stage == "backend_down":
        if not fix_backend:
            return False, assessment.message
        ok, msg = repair_backend(managed, root)
        steps.append(msg)
        if not ok or not probe_backend_live():
            return False, "\n".join(steps)
        assessment = assess_startup(root)
        if assessment.stage == "ready":
            return True, "\n".join(steps + [assessment.message])

    if assessment.stage == "frontend_down":
        if not fix_frontend:
            return False, assessment.message
        if not probe_backend_live():
            assessment = assess_startup(root)
            return False, assessment.message
        ok, msg = repair_frontend(managed, root)
        steps.append(msg)
        if not ok:
            return False, "\n".join(steps)
        assessment = assess_startup(root)
        if assessment.stage == "ready":
            return True, "\n".join(steps + [assessment.message])
        return False, assessment.message

    return assessment.stage == "ready", assessment.message
