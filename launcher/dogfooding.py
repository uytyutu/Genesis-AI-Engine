"""Dogfooding telemetry — real launch stats during daily CEO use."""

from __future__ import annotations

import json
import time
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from launcher import paths

EVENTS_NAME = "dogfooding_events.jsonl"
DAILY_NAME = "dogfooding_daily.json"
BUDGET_NAME = "reliability_budget.json"

CRITICAL_BUDGET_30D = 2


def _memory_dir(root: Path | None = None) -> Path:
    d = paths.memory_dir(root)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _events_path(root: Path | None = None) -> Path:
    return _memory_dir(root) / EVENTS_NAME


def _daily_path(root: Path | None = None) -> Path:
    return _memory_dir(root) / DAILY_NAME


def _budget_path(root: Path | None = None) -> Path:
    return _memory_dir(root) / BUDGET_NAME


def _today_key(when: datetime | None = None) -> str:
    dt = when or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def _append_event(event: str, root: Path | None = None, **fields) -> None:
    row = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "day": _today_key(),
        "event": event,
        **fields,
    }
    path = _events_path(root)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    _rollup_day(_today_key(), root)


def _load_daily(root: Path | None = None) -> dict:
    path = _daily_path(root)
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_daily(data: dict, root: Path | None = None) -> None:
    _daily_path(root).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _empty_day() -> dict:
    return {
        "launch_attempts": 0,
        "launch_successes": 0,
        "launch_failures": 0,
        "browser_opens": 0,
        "auto_recoveries": 0,
        "warnings": 0,
        "critical_errors": 0,
        "launch_durations_sec": [],
        "browser_durations_sec": [],
    }


def _rollup_day(day: str, root: Path | None = None) -> None:
    path = _events_path(root)
    if not path.is_file():
        return
    bucket = _empty_day()
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("day") != day:
                continue
            event = row.get("event")
            if event == "launch_start":
                bucket["launch_attempts"] += 1
            elif event == "launch_success":
                bucket["launch_successes"] += 1
                if row.get("duration_sec") is not None:
                    bucket["launch_durations_sec"].append(float(row["duration_sec"]))
            elif event == "launch_failure":
                bucket["launch_failures"] += 1
                if row.get("critical"):
                    bucket["critical_errors"] += 1
            elif event == "browser_open":
                bucket["browser_opens"] += 1
                if row.get("duration_sec") is not None:
                    bucket["browser_durations_sec"].append(float(row["duration_sec"]))
            elif event == "auto_recovery":
                bucket["auto_recoveries"] += 1
            elif event == "warning":
                bucket["warnings"] += 1
            elif event == "critical_error":
                bucket["critical_errors"] += 1
    except (json.JSONDecodeError, OSError):
        return

    data = _load_daily(root)
    data[day] = bucket
    _save_daily(data, root)


def begin_launch_session(root: Path | None = None) -> tuple[str, float]:
    session_id = uuid.uuid4().hex[:12]
    started = time.monotonic()
    _append_event("launch_start", root, session_id=session_id)
    return session_id, started


def record_launch_success(
    session_id: str,
    started_monotonic: float,
    *,
    root: Path | None = None,
    browser_sec: float | None = None,
) -> None:
    duration = max(0.0, time.monotonic() - started_monotonic)
    fields: dict = {"session_id": session_id, "duration_sec": round(duration, 2)}
    if browser_sec is not None:
        fields["browser_sec"] = round(browser_sec, 2)
    _append_event("launch_success", root, **fields)


def record_launch_failure(
    session_id: str,
    started_monotonic: float,
    *,
    root: Path | None = None,
    error: str = "",
    critical: bool = False,
) -> None:
    duration = max(0.0, time.monotonic() - started_monotonic)
    _append_event(
        "launch_failure",
        root,
        session_id=session_id,
        duration_sec=round(duration, 2),
        error=(error or "")[:240],
        critical=critical,
    )


def record_browser_open(*, root: Path | None = None, duration_sec: float | None = None, ok: bool = True) -> None:
    _append_event(
        "browser_open",
        root,
        duration_sec=round(duration_sec, 2) if duration_sec is not None else None,
        ok=ok,
    )


def record_auto_recovery(message: str, *, root: Path | None = None) -> None:
    _append_event("auto_recovery", root, message=(message or "")[:240])


def record_warning(message: str, *, root: Path | None = None) -> None:
    _append_event("warning", root, message=(message or "")[:240])


def record_critical_error(message: str, *, root: Path | None = None) -> None:
    _append_event("critical_error", root, message=(message or "")[:240])


def record_launcher_open(*, root: Path | None = None) -> None:
    _append_event("launcher_open", root)


def _avg(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 1)


def _day_reliability(day: dict) -> float:
    attempts = int(day.get("launch_attempts") or 0)
    successes = int(day.get("launch_successes") or 0)
    warnings = int(day.get("warnings") or 0)
    if attempts <= 0:
        return 100.0
    base = 100.0 * successes / attempts
    penalty = min(5.0, warnings * 0.8)
    return round(max(0.0, base - penalty), 1)


def today_summary(root: Path | None = None) -> dict:
    day = _today_key()
    _rollup_day(day, root)
    bucket = _load_daily(root).get(day) or _empty_day()
    return {
        "day": day,
        "launch_attempts": bucket.get("launch_attempts", 0),
        "launch_successes": bucket.get("launch_successes", 0),
        "launch_failures": bucket.get("launch_failures", 0),
        "avg_launch_sec": _avg(bucket.get("launch_durations_sec") or []),
        "avg_browser_sec": _avg(bucket.get("browser_durations_sec") or []),
        "auto_recoveries": bucket.get("auto_recoveries", 0),
        "warnings": bucket.get("warnings", 0),
        "reliability_pct": _day_reliability(bucket),
    }


def stability_trend(*, days: int = 7, root: Path | None = None) -> list[tuple[str, float]]:
    daily = _load_daily(root)
    out: list[tuple[str, float]] = []
    now = datetime.now(timezone.utc).date()
    for offset in range(days - 1, -1, -1):
        d = (now - timedelta(days=offset)).isoformat()
        bucket = daily.get(d) or _empty_day()
        out.append((d, _day_reliability(bucket)))
    return out


def reliability_budget(*, window_days: int = 30, root: Path | None = None) -> dict:
    daily = _load_daily(root)
    now = datetime.now(timezone.utc).date()
    critical = 0
    for offset in range(window_days):
        d = (now - timedelta(days=offset)).isoformat()
        bucket = daily.get(d) or _empty_day()
        critical += int(bucket.get("critical_errors") or 0)
    remaining = max(0, CRITICAL_BUDGET_30D - critical)
    return {
        "window_days": window_days,
        "critical_errors": critical,
        "budget": CRITICAL_BUDGET_30D,
        "remaining": remaining,
        "exceeded": critical > CRITICAL_BUDGET_30D,
    }


def format_dogfooding_report(*, root: Path | None = None) -> str:
    today = today_summary(root)
    trend = stability_trend(days=7, root=root)
    budget = reliability_budget(root=root)

    weekday = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")
    trend_lines = []
    for day_iso, pct in trend:
        dt = datetime.fromisoformat(day_iso).date()
        trend_lines.append(f"{weekday[dt.weekday()]} {pct:.0f}%")

    avg_launch = today["avg_launch_sec"]
    avg_browser = today["avg_browser_sec"]
    launch_avg = f"{avg_launch} сек" if avg_launch is not None else "—"
    browser_avg = f"{avg_browser} сек" if avg_browser is not None else "—"

    budget_line = (
        f"Лимит превышен ({budget['critical_errors']}/{budget['budget']})"
        if budget["exceeded"]
        else f"Осталось: {budget['remaining']} из {budget['budget']}"
    )

    return "\n".join(
        [
            "Dogfooding · сегодня",
            f"Запусков: {today['launch_attempts']}",
            f"Успешных: {today['launch_successes']}",
            f"Неудачных: {today['launch_failures']}",
            f"Среднее время запуска: {launch_avg}",
            f"Среднее открытие Mission Control: {browser_avg}",
            f"Auto Recovery: {today['auto_recoveries']}",
            f"Warnings: {today['warnings']}",
            f"Reliability: {today['reliability_pct']:.1f}%",
            "",
            "Stability Trend · 7 дней",
            *trend_lines,
            "",
            f"Reliability Budget · 30 дней: {budget_line}",
        ]
    )
