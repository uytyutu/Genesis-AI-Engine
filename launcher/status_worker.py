"""Background status gathering — never block the Genesis OS UI thread."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from launcher.branding import BRAND_NAME
from launcher.api_client import fetch_mission_control
from launcher.deps import DepStatus, check_dependencies
from launcher.health import ServiceHealth, check_services_fast, owner_ready_from_probes, probe_services_live, sync_with_mission_control
from launcher.processes import reconnect_managed

_DEPS_CACHE: tuple[float, DepStatus] | None = None
_DEPS_CACHE_TTL_SEC = 45.0


@dataclass
class StatusSnapshot:
    health: ServiceHealth
    mission_control: dict | None
    dependency_hints: list[str]
    show_install_btn: bool


def _cached_dependencies(root: Path | None) -> DepStatus:
    global _DEPS_CACHE
    now = time.monotonic()
    if _DEPS_CACHE is not None and now - _DEPS_CACHE[0] < _DEPS_CACHE_TTL_SEC:
        return _DEPS_CACHE[1]
    deps = check_dependencies(root)
    _DEPS_CACHE = (now, deps)
    return deps


def gather_status(
    managed,
    root: Path | None,
    *,
    frontend_exited: bool,
    launcher_idle: bool = True,
) -> StatusSnapshot:
    """Blocking HTTP/deps work — call only from a worker thread."""
    backend_up, frontend_up = probe_services_live(idle=launcher_idle)

    if owner_ready_from_probes(backend_up, frontend_up):
        reconnect_managed(managed, root)

    fe_crashed = frontend_exited and not frontend_up
    health = check_services_fast(
        starting=False,
        frontend_exited=fe_crashed,
        root=root,
        launcher_idle=launcher_idle,
        backend_up=backend_up,
        frontend_up=frontend_up,
    )
    mc = fetch_mission_control(timeout=4.0 if launcher_idle else 8.0) if backend_up else None
    health = sync_with_mission_control(health, mc)

    deps = _cached_dependencies(root)
    hints: list[str] = []
    show_install = False
    if not deps.node_ok:
        hints.append("Нажмите «Запустить» — Virtus Core установит Node.js автоматически")
    elif not deps.frontend_deps_ok:
        hints.append("Mission Control не установлен — нажмите фиолетовую кнопку или «Запустить»")
        show_install = True
    if not deps.python_ok:
        hints.append("Нажмите «Запустить» — Virtus Core установит Python автоматически")
    if deps.node_ok and deps.frontend_deps_ok:
        hints.append(f"Закройте пульт — {BRAND_NAME} останется работать 24/7")

    return StatusSnapshot(
        health=health,
        mission_control=mc,
        dependency_hints=hints,
        show_install_btn=show_install,
    )
