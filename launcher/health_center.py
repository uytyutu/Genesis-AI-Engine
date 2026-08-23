"""RC1 Health Center — subsystem rows + Last Crash for Launcher UI."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class HealthRow:
    id: str
    label: str
    mark: str
    detail: str
    ms: float | None = None


def _rel_age(mtime: float, *, now: float | None = None) -> str:
    age = (now or time.time()) - mtime
    if age < 120:
        return "just now"
    if age < 3600:
        return f"{int(age // 60)} min ago"
    if age < 86400:
        return f"{int(age // 3600)} hours ago"
    return f"{int(age // 86400)} days ago"


def last_crash_summary(root: Path | None = None) -> dict[str, Any]:
    """Read launcher_crash.log mtime / last line for Owner Health Center."""
    try:
        from launcher.paths import log_dir

        crash = log_dir(root) / "launcher_crash.log"
    except Exception:
        return {"label": "Last Crash", "mark": "🟢", "detail": "Never"}

    if not crash.is_file() or crash.stat().st_size == 0:
        return {"label": "Last Crash", "mark": "🟢", "detail": "Never"}

    try:
        text = crash.read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return {"label": "Last Crash", "mark": "🟡", "detail": "log unreadable"}

    if not text:
        return {"label": "Last Crash", "mark": "🟢", "detail": "Never"}

    mtime = crash.stat().st_mtime
    age = _rel_age(mtime)
    last_line = text.splitlines()[-1][:120]
    auto = "restart" in text.lower() or "recovery" in text.lower()
    if auto and (time.time() - mtime) < 7200:
        detail = f"Restarted automatically · {age}"
        mark = "🟡"
    else:
        detail = f"{age} · {last_line}"
        mark = "🔴" if (time.time() - mtime) < 3600 else "🟡"
    return {
        "label": "Last Crash",
        "mark": mark,
        "detail": detail,
        "path": str(crash),
        "mtime": datetime.fromtimestamp(mtime).isoformat(timespec="seconds"),
    }


def build_health_center_rows(
    *,
    backend: bool,
    frontend: bool,
    backend_ms: float | None = None,
    frontend_ms: float | None = None,
    vector_ready: bool | None = None,
    root: Path | None = None,
) -> list[dict[str, Any]]:
    """Owner-facing rows for Launcher Health Center."""
    rows: list[dict[str, Any]] = []

    def ms_label(ok: bool, ms: float | None, down: str = "down") -> str:
        if not ok:
            return down
        if ms is None:
            return "ok"
        return f"{int(ms)} ms"

    rows.append(
        {
            "id": "backend",
            "label": "Backend",
            "mark": "🟢" if backend else "🔴",
            "detail": ms_label(backend, backend_ms),
        }
    )
    rows.append(
        {
            "id": "frontend",
            "label": "Frontend",
            "mark": "🟢" if frontend else "🔴",
            "detail": ms_label(frontend, frontend_ms),
        }
    )
    if vector_ready is True:
        rows.append(
            {"id": "vector", "label": "Vector", "mark": "🟢", "detail": "Ready"}
        )
    elif backend and vector_ready is False:
        rows.append(
            {"id": "vector", "label": "Vector", "mark": "🟡", "detail": "Warming"}
        )
    else:
        rows.append(
            {"id": "vector", "label": "Vector", "mark": "🟡", "detail": "—"}
        )

    rows.append(
        {"id": "factory", "label": "Factory", "mark": "🟢", "detail": "Idle"}
    )
    rows.append(
        {"id": "farm", "label": "Farm", "mark": "🟡", "detail": "Waiting"}
    )
    rows.append(
        {
            "id": "launcher",
            "label": "Launcher",
            "mark": "🟢" if (backend and frontend) else "🟡",
            "detail": "Stable" if (backend and frontend) else "Recovering",
        }
    )
    rows.append(last_crash_summary(root))
    return rows


# Internal Stability KPIs (RC1) — warn when exceeded
STABILITY_KPI = {
    "startup_sec": 20.0,
    "dashboard_first_paint_sec": 2.0,
    "farm_refresh_ms": 300.0,
    "ai_edit_sec": 5.0,
    "website_save_sec": 2.0,
}


def kpi_warnings(samples: dict[str, float]) -> list[str]:
    """Return human warnings when measured samples exceed KPI targets."""
    out: list[str] = []
    mapping = {
        "startup_sec": ("Startup", STABILITY_KPI["startup_sec"], "s"),
        "dashboard_first_paint_sec": (
            "Dashboard First Paint",
            STABILITY_KPI["dashboard_first_paint_sec"],
            "s",
        ),
        "farm_refresh_ms": ("Farm Refresh", STABILITY_KPI["farm_refresh_ms"], "ms"),
        "ai_edit_sec": ("AI Edit", STABILITY_KPI["ai_edit_sec"], "s"),
        "website_save_sec": ("Website Save", STABILITY_KPI["website_save_sec"], "s"),
    }
    for key, (label, limit, unit) in mapping.items():
        if key not in samples:
            continue
        val = float(samples[key])
        if val > limit:
            out.append(f"⚠ {label}: {val:.0f}{unit} > {limit:.0f}{unit} KPI")
    return out
