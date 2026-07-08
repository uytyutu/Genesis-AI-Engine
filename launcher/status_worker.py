"""Background status gathering — never block the Genesis OS UI thread."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from launcher.branding import BRAND_NAME
from launcher.api_client import fetch_mission_control
from launcher.deps import check_dependencies
from launcher.health import ServiceHealth, check_services_fast, sync_with_mission_control
from launcher.processes import reconnect_managed


@dataclass
class StatusSnapshot:
    health: ServiceHealth
    mission_control: dict | None
    dependency_hints: list[str]
    show_install_btn: bool


def gather_status(
    managed,
    root: Path | None,
    *,
    frontend_exited: bool,
    launcher_idle: bool = True,
) -> StatusSnapshot:
    """Blocking HTTP/deps work — call only from a worker thread."""
    from launcher.health import owner_ready_live, probe_frontend_live

    if owner_ready_live():
        reconnect_managed(managed, root)

    fe_crashed = frontend_exited and not probe_frontend_live()
    health = check_services_fast(
        starting=False,
        frontend_exited=fe_crashed,
        root=root,
        launcher_idle=launcher_idle,
    )
    mc = fetch_mission_control()
    health = sync_with_mission_control(health, mc)

    deps = check_dependencies(root)
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
