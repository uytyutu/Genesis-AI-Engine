from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from launcher.deps import (
    build_frontend,
    check_dependencies,
    clear_frontend_build,
    ensure_frontend_ready,
    find_npm,
    frontend_build_integrity,
    frontend_build_ready,
    frontend_deps_ready,
    install_frontend_deps,
)
from launcher.health import read_frontend_log_tail
from launcher.log_parse import extract_frontend_error, format_owner_error
from launcher.log_util import append_log

if TYPE_CHECKING:
    from launcher.processes import ManagedProcesses


@dataclass
class FrontendDiagnosis:
    issue: str
    message: str
    can_auto_fix: bool
    log_excerpt: str = ""


_READY_MARKERS = (
    "ready in",
    "started server on",
    "local:        http",
    "local: http",
    "✓ ready",
)

_ERROR_MARKERS: tuple[tuple[str, str, bool], ...] = (
    ("syntax error", "Ошибка в коде или CSS Mission Control.", True),
    ("build error", "Next.js не смог собрать интерфейс.", True),
    ("failed to compile", "Ошибка компиляции Mission Control.", True),
    ("cannot find module", "Зависимости Mission Control не установлены полностью.", True),
    ("enoent", "Не найден файл сборки — Virtus Core выполнит npm run build.", True),
    ("routes-manifest", "Mission Control не собран (.next отсутствует).", True),
    ("eaddrinuse", "Порт 3000 уже занят — Virtus Core попробует освободить.", True),
    ("address already in use", "Порт 3000 уже занят — Virtus Core попробует освободить.", True),
    ("npm err!", "Ошибка npm при установке или запуске.", True),
    ("node:internal", "Node.js завершился с внутренней ошибкой.", True),
)


def frontend_log_indicates_ready(root: Path | None = None) -> bool:
    tail = read_frontend_log_tail(root, chars=8000).lower()
    return any(marker in tail for marker in _READY_MARKERS)


def frontend_log_indicates_error(root: Path | None = None) -> bool:
    from launcher.health import probe_frontend_live

    if probe_frontend_live():
        return False
    tail = read_frontend_log_tail(root, chars=2500).lower()
    if not tail:
        return False
    ready_idx = max((tail.rfind(marker) for marker in _READY_MARKERS), default=-1)
    if ready_idx >= 0:
        tail = tail[ready_idx:]
    return any(marker in tail for marker, _, _ in _ERROR_MARKERS)


def _log_excerpt(root: Path | None, lines: int = 25) -> str:
    _, meaningful = extract_frontend_error(root)
    if meaningful:
        return "\n".join(meaningful[-lines:])
    tail = read_frontend_log_tail(root, chars=6000)
    if not tail:
        return ""
    parts = [ln.strip() for ln in tail.splitlines() if ln.strip() and not ln.strip().startswith("GET /")]
    return "\n".join(parts[-lines:])


def diagnose_frontend(
    root: Path | None = None,
    *,
    frontend_exited: bool = False,
    frontend_up: bool = False,
    elapsed_sec: float = 0,
) -> FrontendDiagnosis:
    deps = check_dependencies(root)
    excerpt = _log_excerpt(root)
    lowered = excerpt.lower()

    if not deps.node_ok or not deps.npm_ok:
        return FrontendDiagnosis(
            issue="node_missing",
            message=(
                "Node.js или npm не найдены.\n"
                "Нажмите «Запустить» — Virtus Core установит компоненты автоматически."
            ),
            can_auto_fix=False,
            log_excerpt=excerpt,
        )

    if not deps.frontend_deps_ok:
        if _npm_install_failed(root):
            npm_tail = read_npm_install_log_tail(root, chars=1500)
            npm_lines = [ln for ln in npm_tail.splitlines() if ln.strip()]
            return FrontendDiagnosis(
                issue="npm_install_failed",
                message="Не удалось выполнить npm install. Проверьте интернет и npm_install.log.",
                can_auto_fix=True,
                log_excerpt="\n".join(npm_lines[-6:]) if npm_lines else npm_tail,
            )
        return FrontendDiagnosis(
            issue="missing_deps",
            message="Зависимости Mission Control не установлены (npm install не завершён).",
            can_auto_fix=True,
            log_excerpt=excerpt,
        )

    if root is not None and deps.frontend_deps_ok and (
        not frontend_build_ready(root) or not frontend_build_integrity(root)
    ):
        if "cannot find module" in lowered:
            msg = (
                "Сборка Mission Control устарела (битые файлы в .next).\n"
                "Virtus Core удалит кэш и выполнит npm run build заново."
            )
        elif "routes-manifest" in lowered or "enoent" in lowered:
            msg = (
                "Mission Control не собран: отсутствует .next/routes-manifest.json.\n"
                "Virtus Core выполнит npm run build автоматически."
            )
        elif not frontend_build_integrity(root):
            msg = (
                "Сборка Mission Control неполная (повреждён .next).\n"
                "Virtus Core пересоберёт интерфейс перед запуском."
            )
        else:
            msg = (
                "Mission Control ещё не собран (нет папки .next).\n"
                "Virtus Core выполнит сборку перед запуском."
            )
        return FrontendDiagnosis(
            issue="missing_build",
            message=msg,
            can_auto_fix=True,
            log_excerpt=excerpt,
        )

    if not excerpt and elapsed_sec >= 45 and not frontend_up:
        return FrontendDiagnosis(
            issue="no_log_output",
            message=(
                "Frontend не пишет журнал и не отвечает на :3000.\n"
                "Возможны: Node.js не в PATH, зависший процесс или первая сборка без вывода."
            ),
            can_auto_fix=True,
            log_excerpt="(frontend.log пуст)",
        )

    for marker, human, can_fix in _ERROR_MARKERS:
        if marker in lowered:
            extra = ""
            if marker in ("eaddrinuse", "address already in use"):
                extra = "\nVirtus Core попробует освободить порт автоматически."
            return FrontendDiagnosis(
                issue=marker.replace(" ", "_"),
                message=f"Frontend: {human}{extra}",
                can_auto_fix=can_fix,
                log_excerpt=excerpt,
            )

    if frontend_exited:
        headline, _ = extract_frontend_error(root)
        return FrontendDiagnosis(
            issue="process_crashed",
            message=f"Frontend завершился.\n\nПричина:\n{headline}",
            can_auto_fix=True,
            log_excerpt=_log_excerpt(root),
        )

    if frontend_up:
        return FrontendDiagnosis(
            issue="ok",
            message="Mission Control работает.",
            can_auto_fix=False,
            log_excerpt=excerpt,
        )

    if frontend_log_indicates_ready(root) and not frontend_up:
        return FrontendDiagnosis(
            issue="slow_probe",
            message="Next.js запустился, но порт :3000 ещё не отвечает — подождите немного.",
            can_auto_fix=False,
            log_excerpt=excerpt,
        )

    if elapsed_sec >= 60:
        return FrontendDiagnosis(
            issue="timeout",
            message=(
                f"Frontend не ответил за {int(elapsed_sec)} с.\n"
                "Возможны: первая сборка Next.js (до 3 мин), неполный npm install или ошибка в журнале."
            ),
            can_auto_fix=True,
            log_excerpt=excerpt,
        )

    return FrontendDiagnosis(
        issue="starting",
        message="Mission Control запускается…",
        can_auto_fix=False,
        log_excerpt=excerpt,
    )


def _clear_next_cache(root: Path | None, managed=None) -> None:
    clear_frontend_build(root, managed=managed)
    append_log("Cleared .next cache")


def _needs_frontend_rebuild(root: Path | None, diag: FrontendDiagnosis) -> bool:
    if not frontend_build_ready(root) or not frontend_build_integrity(root):
        return True
    excerpt = _log_excerpt(root).lower()
    if "cannot find module" in excerpt:
        return True
    if "routes-manifest" in excerpt and "enoent" in excerpt:
        return True
    return diag.issue in ("missing_build", "enoent", "routes-manifest", "cannot_find_module")


def _port_conflict_in_log(root: Path | None) -> bool:
    tail = read_frontend_log_tail(root, chars=4000).lower()
    return "eaddrinuse" in tail or "address already in use" in tail


def _pids_on_port(port: int) -> list[int]:
    import re
    import subprocess
    import sys

    if sys.platform != "win32":
        return []
    try:
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True,
            text=True,
            timeout=15,
            creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0,  # type: ignore[attr-defined]
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    needle = f":{port}"
    pids: list[int] = []
    for line in result.stdout.splitlines():
        upper = line.upper()
        if needle not in line or "LISTENING" not in upper:
            continue
        match = re.search(r"(\d+)\s*$", line.strip())
        if match:
            pids.append(int(match.group(1)))
    return list(dict.fromkeys(pids))


def _process_basename(pid: int) -> str:
    import subprocess
    import sys

    if sys.platform != "win32":
        return ""
    try:
        result = subprocess.run(
            ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            timeout=10,
            creationflags=subprocess.CREATE_NO_WINDOW,  # type: ignore[attr-defined]
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    if result.returncode != 0 or not result.stdout.strip():
        return ""
    line = result.stdout.strip().splitlines()[0]
    if line.startswith('"'):
        return line.split('"')[1].lower()
    return line.split(",")[0].lower()


def _try_free_port(port: int = 3000) -> tuple[bool, str]:
    """Kill stale node.exe listeners on port — safe auto-fix for Genesis restarts."""
    from launcher.health import probe_frontend_live
    from launcher.process_cleanup import kill_port_listeners, pids_on_port

    if probe_frontend_live():
        return True, f"Порт {port} уже обслуживает Mission Control"

    outcomes = kill_port_listeners(port, allowed_names=("node.exe", "nodejs.exe"))
    if outcomes:
        time.sleep(1)
        freed = [f"node.exe:{r.pid}" for r in outcomes if r.ok]
        if freed:
            return True, f"Освобождён порт {port} ({', '.join(freed)})"
        failed = [f"pid={r.pid}:{r.reason}" for r in outcomes if not r.ok]
        return False, f"Порт {port} всё ещё занят ({'; '.join(failed)})"
    if pids_on_port(port):
        return False, f"Порт {port} занят не-Node процессом — закройте его вручную"
    return True, f"Порт {port} свободен"


def repair_frontend(
    managed: ManagedProcesses,
    root: Path | None = None,
) -> tuple[bool, str]:
    """Kill frontend, rebuild .next if needed, restart production server (next start)."""
    from launcher.health import owner_ready_live, probe_frontend_live
    from launcher.processes import _kill_tree, start_frontend

    if not owner_ready_live():
        from launcher.health import probe_backend_live

        if not probe_backend_live():
            from launcher.backend_repair import diagnose_backend, format_backend_failure

            diag = diagnose_backend(root, backend_up=False)
            return False, (
                "Backend не запущен — ремонт Frontend пропущен.\n\n"
                f"{format_backend_failure(diag, root)}"
            )

    from launcher.process_cleanup import stop_frontend_listeners

    if owner_ready_live():
        return True, "Virtus Core уже готов — Mission Control отвечает на :3000"
    if probe_frontend_live():
        return True, "Frontend уже работает на :3000 — ремонт не нужен"

    stop_frontend_listeners(root, managed)
    _kill_tree(managed.frontend)
    managed.frontend = None

    diag = diagnose_frontend(root, frontend_exited=True)
    steps: list[str] = []

    if not find_npm():
        return False, diag.message

    if not frontend_deps_ready(root):
        ok, msg = install_frontend_deps(root)
        steps.append(msg)
        if not ok:
            return False, f"{diag.message}\n\n{msg}"

    if _port_conflict_in_log(root) or _pids_on_port(3000):
        ok, msg = _try_free_port(3000)
        steps.append(msg)
        if not ok:
            return False, f"{diag.message}\n\n{msg}"

    if root is not None and _needs_frontend_rebuild(root, diag):
        _clear_next_cache(root, managed)
        ok, msg = build_frontend(root, managed=managed)
        steps.append(msg)
        if not ok:
            return False, f"{diag.message}\n\n{msg}"
        if not frontend_build_integrity(root):
            return False, (
                f"{diag.message}\n\n"
                "Сборка Mission Control не завершилась — .next всё ещё неполный.\n"
                "См. launcher/logs/frontend_build.log"
            )

    ok, msg = ensure_frontend_ready(root, for_production=True, managed=managed)
    steps.append(msg)
    if not ok:
        return False, f"{diag.message}\n\n{msg}"

    ok, msg, proc = start_frontend(root, managed=managed)
    steps.append(msg)
    if not ok:
        return False, f"{diag.message}\n\n{msg}"

    managed.frontend = proc
    append_log("Frontend repair: restarted production server (next start)")
    time.sleep(2)
    return True, "\n".join(steps)


def format_failure_message(diag: FrontendDiagnosis, root: Path | None = None) -> str:
    parts = [diag.message]
    excerpt = diag.log_excerpt or _log_excerpt(root)
    if excerpt:
        parts.append("\n--- frontend.log ---")
        parts.append(excerpt)
    return "\n".join(parts)


def failure_headline(diag: FrontendDiagnosis, root: Path | None = None) -> str:
    """One-line reason for launcher status (owner-facing)."""
    parsed, _ = extract_frontend_error(root)
    if parsed and "RegExp" not in parsed and "ArrayBuffer" not in parsed:
        short = parsed if len(parsed) <= 64 else parsed[:61] + "…"
        return f"❌ {short}"
    headlines = {
        "node_missing": "❌ Node.js не найден",
        "missing_deps": "❌ Не удалось выполнить npm install",
        "syntax error": "❌ Ошибка сборки Next.js",
        "build error": "❌ Ошибка сборки Next.js",
        "failed_to_compile": "❌ Ошибка сборки Next.js",
        "cannot_find_module": "❌ Зависимости Mission Control не установлены",
        "enoent": "❌ Зависимости Mission Control не установлены",
        "eaddrinuse": "❌ Порт 3000 занят",
        "address_already_in_use": "❌ Порт 3000 занят",
        "npm_err!": "❌ Ошибка npm",
        "node:internal": "❌ Frontend завершился с ошибкой",
        "process_crashed": "❌ Frontend завершился с ошибкой",
        "timeout": "❌ Mission Control не запустился вовремя",
        "no_log_output": "❌ Frontend не отвечает (пустой журнал)",
        "npm_install_failed": "❌ Не удалось выполнить npm install",
        "missing_build": "❌ Mission Control не собран",
        "routes-manifest": "❌ Mission Control не собран",
    }
    return headlines.get(diag.issue, f"❌ {diag.message.splitlines()[0][:64]}")


def read_npm_install_log_tail(root: Path | None = None, chars: int = 3000) -> str:
    from launcher.paths import log_dir

    npm_log = log_dir(root) / "npm_install.log"
    if not npm_log.exists():
        return ""
    try:
        return npm_log.read_text(encoding="utf-8", errors="replace")[-chars:]
    except OSError:
        return ""


def _npm_install_failed(root: Path | None) -> bool:
    tail = read_npm_install_log_tail(root).lower()
    if not tail:
        return False
    return "npm err!" in tail or "error code" in tail or "eresolve" in tail
