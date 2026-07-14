"""Genesis Runtime Boot — automated Backend / Frontend / Mission Control pipeline."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from launcher.log_util import append_log


@dataclass
class BootPhase:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class BootResult:
    success: bool
    ready: bool
    launch_ok: bool
    message: str = ""
    error: str = ""
    cause: str = ""
    phases: list[BootPhase] = field(default_factory=list)


def _phase(phases: list[BootPhase], name: str, ok: bool, detail: str = "") -> None:
    phases.append(BootPhase(name=name, ok=ok, detail=detail))
    append_log(f"Runtime Boot · {name}: {'OK' if ok else 'FAIL'} {detail}".strip())


def run_runtime_boot(
    managed,
    root: Path | None = None,
    *,
    on_phase: Callable[[str], None] | None = None,
    on_progress: Callable[[str], None] | None = None,
    build_policy: str = "launch_stable",
) -> BootResult:
    """Check services, launch if needed, recover, verify HTTP 200. No UI."""
    from launcher.health import owner_ready_live, probe_backend_live, probe_frontend_live
    from launcher.processes import launch_genesis, reconnect_managed, wait_until_ready

    phases: list[BootPhase] = []

    if owner_ready_live():
        reconnect_managed(managed, root)
        _phase(phases, "backend", True, "already running")
        _phase(phases, "frontend", True, "HTTP 200")
        _phase(phases, "mission_control", True, "ready")
        return BootResult(
            success=True,
            ready=True,
            launch_ok=True,
            message="Virtus Core уже работает",
            phases=phases,
        )

    backend_up = probe_backend_live()
    _phase(phases, "backend", backend_up, "probe /api/status")

    if not backend_up:
        if on_phase:
            on_phase("backend")
        ok, msg = launch_genesis(
            managed,
            root=root,
            on_phase=on_phase,
            on_progress=on_progress,
            build_policy=build_policy,
        )
        if not ok:
            _phase(phases, "recovery", False, msg)
            return BootResult(
                success=False,
                ready=False,
                launch_ok=False,
                message=msg,
                error=msg,
                cause=_cause_from_message(msg),
                phases=phases,
            )
        ready, err = wait_until_ready(
            timeout=150.0,
            poll=0.8,
            managed=managed,
            root=root,
            on_progress=on_progress,
            auto_repair=True,
        )
        if not ready and owner_ready_live():
            ready, err = True, ""
        if not ready:
            _phase(phases, "recovery", False, err or "timeout")
            return BootResult(
                success=False,
                ready=False,
                launch_ok=True,
                message=msg,
                error=err or "Не удалось запустить Virtus Core",
                cause=_cause_from_message(err or msg),
                phases=phases,
            )
        _phase(phases, "backend", probe_backend_live(), "after boot")
        _phase(phases, "frontend", probe_frontend_live(), "HTTP 200")
        _phase(phases, "mission_control", owner_ready_live(), "verified")
        return BootResult(
            success=True,
            ready=True,
            launch_ok=True,
            message=msg,
            phases=phases,
        )

    frontend_up = probe_frontend_live()
    _phase(phases, "frontend", frontend_up, "HTTP 200" if frontend_up else "not ready")

    if frontend_up:
        reconnect_managed(managed, root)
        _phase(phases, "mission_control", True, "ready")
        return BootResult(
            success=True,
            ready=True,
            launch_ok=True,
            message="Backend и Frontend работают",
            phases=phases,
        )

    if on_phase:
        on_phase("frontend")
    ok, msg = launch_genesis(
        managed,
        root=root,
        on_phase=on_phase,
        on_progress=on_progress,
        build_policy=build_policy,
    )
    if not ok:
        _phase(phases, "recovery", False, msg)
        return BootResult(
            success=False,
            ready=False,
            launch_ok=False,
            message=msg,
            error=msg,
            cause=_cause_from_message(msg),
            phases=phases,
        )

    ready, err = wait_until_ready(
        timeout=150.0,
        poll=0.8,
        managed=managed,
        root=root,
        on_progress=on_progress,
        auto_repair=True,
    )
    if not ready and owner_ready_live():
        ready, err = True, ""

    if not ready:
        _phase(phases, "recovery", False, err or "timeout")
        return BootResult(
            success=False,
            ready=False,
            launch_ok=True,
            message=msg,
            error=err or "Mission Control не отвечает",
            cause=_cause_from_message(err or msg),
            phases=phases,
        )

    _phase(phases, "frontend", probe_frontend_live(), "after recovery")
    _phase(phases, "mission_control", owner_ready_live(), "verified")
    return BootResult(
        success=True,
        ready=True,
        launch_ok=True,
        message=msg,
        phases=phases,
    )


def _cause_from_message(message: str) -> str:
    text = (message or "").lower()
    if "frontend" in text or "mission control" in text or ":3000" in text:
        return "Mission Control не запустился или вернул ошибку."
    if "backend" in text or ":8000" in text or "python" in text:
        return "Backend не отвечает."
    if "node" in text or "npm" in text:
        return "Не установлен Node.js или повреждена сборка Frontend."
    return "Virtus Core не смог полностью запуститься."


def write_boot_report(result: BootResult, root: Path | None = None) -> Path:
    from launcher import paths

    memory = paths.memory_dir(root)
    memory.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    payload = {
        "created_at": stamp,
        "success": result.success,
        "ready": result.ready,
        "cause": result.cause or _cause_from_message(result.error),
        "error": result.error,
        "message": result.message,
        "phases": [
            {"name": p.name, "ok": p.ok, "detail": p.detail} for p in result.phases
        ],
        "build_id": _read_build_id(),
    }
    latest = memory / "runtime_boot_report_latest.json"
    latest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    history = memory / "runtime_boot_reports"
    history.mkdir(parents=True, exist_ok=True)
    archived = history / f"boot_report_{stamp.replace(':', '-').replace('+', '_')}.json"
    archived.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    append_log(f"Runtime Boot report saved: {latest}")
    return latest


def _read_build_id() -> str:
    try:
        from launcher import build_info

        return build_info.BUILD_ID
    except Exception:
        return "unknown"


def format_boot_failure_message(result: BootResult) -> str:
    lines = [
        result.cause or _cause_from_message(result.error),
        "",
        result.error or result.message or "Неизвестная ошибка",
        "",
        "Что уже проверено:",
    ]
    for phase in result.phases:
        mark = "✓" if phase.ok else "✗"
        detail = f" — {phase.detail}" if phase.detail else ""
        lines.append(f"  {mark} {phase.name}{detail}")
    lines.extend(
        [
            "",
            "Нажмите «Сообщить о проблеме» — отчёт сохранится для поддержки.",
            "Или «Исправить автоматически» на главном экране.",
        ]
    )
    return "\n".join(lines)
