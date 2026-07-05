"""HTTP health checks for Backend, Frontend and core modules."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen
import json

BACKEND_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://127.0.0.1:3000"
COMMAND_CENTER_URL = "http://localhost:3000"

# Owner UX: Mission Control needs Backend API + Frontend. Kernel/Brain are informational.
BACKEND_PROBE_TIMEOUT = 8.0
FRONTEND_PROBE_TIMEOUT = 6.0
SYSTEM_CHECK_TIMEOUT = 25.0
_PROBE_ATTEMPTS = 2

_FRONTEND_URLS = (
    FRONTEND_URL,
    COMMAND_CENTER_URL,
    "http://localhost:3000",
    "http://127.0.0.1:3000",
)


@dataclass
class ServiceHealth:
    backend: bool = False
    frontend: bool = False
    kernel: bool = False
    brain: bool = False
    api: bool = False
    overall: str = "stopped"  # stopped | starting_backend | starting_frontend | running | error
    error_message: str = ""
    details: list[str] = field(default_factory=list)


def _get_json(url: str, timeout: float = BACKEND_PROBE_TIMEOUT) -> dict | None:
    try:
        with urlopen(url, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except (URLError, OSError, json.JSONDecodeError, TimeoutError):
        return None


def _probe_url(url: str, timeout: float = BACKEND_PROBE_TIMEOUT, *, require_ok: bool = False) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:
            if require_ok:
                return response.status == 200
            return response.status < 500
    except (URLError, OSError, TimeoutError):
        return False


def _probe_with_retries(probe, *, attempts: int = _PROBE_ATTEMPTS) -> bool:
    for attempt in range(attempts):
        if probe():
            return True
        if attempt < attempts - 1:
            time.sleep(0.5 * (attempt + 1))
    return False


def probe_backend(
    timeout: float = BACKEND_PROBE_TIMEOUT,
    attempts: int = _PROBE_ATTEMPTS,
) -> bool:
    """True when /api/status responds — never checks / root."""

    def _try() -> bool:
        return _get_json(f"{BACKEND_URL}/api/status", timeout=timeout) is not None

    return _probe_with_retries(_try, attempts=attempts)


def probe_frontend(
    timeout: float = FRONTEND_PROBE_TIMEOUT,
    attempts: int = _PROBE_ATTEMPTS,
) -> bool:
    return probe_frontend_live(timeout=timeout, attempts=attempts)


def probe_frontend_live(
    timeout: float = FRONTEND_PROBE_TIMEOUT,
    attempts: int = _PROBE_ATTEMPTS,
) -> bool:
    """HTTP 200 on Mission Control URLs — same as the owner opens in the browser."""

    def _try() -> bool:
        for url in _FRONTEND_URLS:
            if _probe_url(url, timeout=timeout, require_ok=True):
                return True
        return False

    return _probe_with_retries(_try, attempts=attempts)


def frontend_port_listening() -> bool:
    """True when something listens on Mission Control port — process alive, not necessarily HTTP 200."""
    from launcher.process_cleanup import frontend_listener_pids

    return bool(frontend_listener_pids())


def probe_frontend_http_status(timeout: float = 3.0) -> int | None:
    """First HTTP status from Mission Control, or None when the port is closed."""
    for url in (FRONTEND_URL, COMMAND_CENTER_URL):
        try:
            with urlopen(url, timeout=timeout) as response:
                return int(response.status)
        except (URLError, OSError, TimeoutError, ValueError):
            continue
    return None


def probe_backend_live(
    timeout: float = BACKEND_PROBE_TIMEOUT,
    attempts: int = _PROBE_ATTEMPTS,
) -> bool:
    return probe_backend(timeout=timeout, attempts=attempts)


def owner_ready_live() -> bool:
    """Ground truth: both services answer HTTP 200 on the URLs owners use."""
    return probe_backend_live() and probe_frontend_live()


def owner_ready_from_probes(backend: bool, frontend: bool) -> bool:
    return backend and frontend


def owner_ready(health: ServiceHealth) -> bool:
    """Mission Control is usable for the owner."""
    return health.backend and health.frontend


def sync_with_mission_control(health: ServiceHealth, mission_control: dict | None) -> ServiceHealth:
    """Align launcher status with Mission Control API — no extra HTTP probes."""
    if owner_ready(health):
        health.overall = "running"
        health.error_message = ""
    if mission_control is not None:
        health.backend = health.backend or True
        if mission_control.get("system_running"):
            health.kernel = True
    if owner_ready(health):
        health.overall = "running"
        health.error_message = ""
    return health


def read_frontend_log_tail(root: Path | None = None, chars: int = 4000) -> str:
    from launcher.paths import log_dir

    fe_log = log_dir(root) / "frontend.log"
    if not fe_log.exists():
        return ""
    try:
        text = fe_log.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    return text[-chars:]


def diagnose_startup_failure(
    *,
    backend_up: bool,
    frontend_up: bool,
    frontend_exited: bool,
    root: Path | None = None,
    elapsed_sec: float = 0,
) -> str:
    if owner_ready_live():
        return ""

    from launcher.frontend_repair import diagnose_frontend, format_failure_message

    if not backend_up and probe_backend_live():
        backend_up = True
    if not frontend_up and probe_frontend_live():
        frontend_up = True
    if backend_up and frontend_up:
        return ""

    diag = diagnose_frontend(
        root,
        frontend_exited=frontend_exited and not probe_frontend_live(),
        frontend_up=frontend_up,
        elapsed_sec=elapsed_sec,
    )
    if diag.issue not in ("starting", "ok", "slow_probe"):
        return format_failure_message(diag)

    tail = read_frontend_log_tail(root)
    lowered = tail.lower()

    if "syntax error" in lowered or "build error" in lowered:
        if "globals.css" in lowered:
            return (
                "Frontend: ошибка в app/globals.css. "
                "Исправьте CSS и перезапустите Genesis."
            )
        return "Frontend: ошибка сборки Next.js. Откройте журнал frontend.log."

    if frontend_exited and not probe_frontend_live():
        return format_failure_message(diag)

    if not backend_up and frontend_up:
        return "Backend ещё запускается — подождите или нажмите «Запустить»."

    if backend_up and not frontend_up:
        return format_failure_message(
            diagnose_frontend(
                root,
                frontend_exited=frontend_exited,
                frontend_up=frontend_up,
                elapsed_sec=elapsed_sec,
            ),
            root,
        )

    if not backend_up:
        return "Backend ещё запускается — проверьте backend.log."

    return "Таймаут запуска. Подождите или проверьте журналы."


def check_services_fast(
    starting: bool = False,
    *,
    frontend_exited: bool = False,
    root: Path | None = None,
    launcher_idle: bool = False,
) -> ServiceHealth:
    """UI-safe health check — no slow system-check, single probe pass."""
    health = ServiceHealth()
    lines: list[str] = []

    health.backend = probe_backend_live()
    if health.backend:
        lines.append("✔ Backend работает (/api/status)")
    else:
        lines.append("✘ Backend не отвечает на /api/status")

    health.frontend = probe_frontend_live()
    if health.frontend:
        lines.append("✔ Frontend работает (HTTP 200)")
    else:
        lines.append("✘ Frontend не отвечает на :3000")

    health.details = lines

    if owner_ready(health):
        health.overall = "running"
        health.error_message = ""
        return health

    fe_crashed = frontend_exited and not health.frontend

    if launcher_idle and not owner_ready(health) and not fe_crashed:
        health.overall = "stopped"
        health.error_message = ""
        return health

    if fe_crashed or (not starting and health.backend and not health.frontend):
        health.overall = "error"
        health.error_message = diagnose_startup_failure(
            backend_up=health.backend,
            frontend_up=health.frontend,
            frontend_exited=fe_crashed,
            root=root,
        )
    elif starting:
        if health.backend and not health.frontend:
            health.overall = "starting_frontend"
        elif not health.backend:
            health.overall = "starting_backend"
        else:
            health.overall = "starting_frontend"
    elif health.backend or health.frontend:
        health.overall = "error"
        health.error_message = diagnose_startup_failure(
            backend_up=health.backend,
            frontend_up=health.frontend,
            frontend_exited=fe_crashed,
            root=root,
        )
    else:
        health.overall = "stopped"

    return health


def check_services(
    starting: bool = False,
    *,
    frontend_exited: bool = False,
    root: Path | None = None,
    include_slow_checks: bool = False,
) -> ServiceHealth:
    health = check_services_fast(
        starting=starting,
        frontend_exited=frontend_exited,
        root=root,
    )
    if not include_slow_checks:
        return health

    lines = list(health.details)
    if health.backend:
        health.api = _probe_url(
            f"{BACKEND_URL}/api/owner/system-check",
            timeout=SYSTEM_CHECK_TIMEOUT,
            require_ok=True,
        )
        if health.api:
            lines.append("✔ API system-check доступно")
        else:
            lines.append("🟡 system-check медленный — не блокирует работу")

        modules = _get_json(f"{BACKEND_URL}/api/modules")
        if modules and "modules" in modules:
            by_id = {m["id"]: m["status"] for m in modules["modules"]}
            health.kernel = by_id.get("kernel") == "online"
            health.brain = by_id.get("brain") in ("online", "degraded")
            if health.kernel:
                lines.append("✔ Kernel работает")
            else:
                lines.append("🟡 Kernel — проверка модулей")
            if health.brain:
                lines.append("✔ Brain работает")
            else:
                lines.append("🟡 Brain — не блокирует Mission Control")
        else:
            health.kernel = True
            health.brain = True
            lines.append("🟡 Модули ядра — ответ неполный (не критично)")

    health.details = lines
    return health


def overall_label(state: str, error_message: str = "") -> tuple[str, str]:
    labels = {
        "running": ("✔ Genesis полностью готов", "#22c55e"),
        "starting_backend": ("🟡 Запуск Backend...", "#eab308"),
        "starting_frontend": ("🟡 Запуск Mission Control...", "#eab308"),
        "starting": ("🟡 Запускается...", "#eab308"),
        "error": ("🔴 Ошибка запуска", "#ef4444"),
        "stopped": ("⚪ Genesis остановлен", "#9ca3af"),
    }
    text, color = labels.get(state, labels["stopped"])
    if state == "error" and error_message:
        short = error_message if len(error_message) <= 72 else error_message[:69] + "…"
        text = f"🔴 {short}"
    return text, color
