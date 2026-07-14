"""Compact developer stats for Vector turns — debug mode only (P0)."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.vector_intelligence.pipeline import VectorTurnPlan

_PLANNER_LABELS = {
    "open_dialog": "Open dialog",
    "accept_responsibility": "Accept responsibility",
    "understand_goal": "Understand goal",
    "requirements": "Requirements",
    "materials": "Materials",
    "creation": "Creation",
    "show_progress": "Show progress",
    "revisions": "Revisions",
    "ready": "Ready",
    "verification": "Verification",
    "gate": "Gate",
    "launch": "Launch",
}

_HTTP_CODE = re.compile(r"'(\d{3})")


def _short_reason(employee_id: str, error: str = "", skip_code: str = "") -> str:
    text = f"{error} {skip_code}".strip()
    m = _HTTP_CODE.search(text)
    if m:
        return f"{employee_id} {m.group(1)}"
    if "rate" in text.lower() or "429" in text:
        return f"{employee_id} 429"
    if "402" in text or "payment" in text.lower():
        return f"{employee_id} 402"
    if skip_code == "health":
        return f"{employee_id} health"
    if skip_code == "quota" or "quota" in text.lower():
        return f"{employee_id} quota"
    if skip_code == "offline" or "offline" in text.lower():
        return f"{employee_id} offline"
    if skip_code == "no_key":
        return f"{employee_id} no_key"
    if error:
        return f"{employee_id} {error[:48]}"
    if skip_code:
        return f"{employee_id} {skip_code}"
    return employee_id


def build_dev_stats(
    *,
    turn_plan: VectorTurnPlan,
    provider_id: str,
    elapsed_sec: float,
    route: dict[str, Any] | None = None,
    health_excluded: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Human-readable last-turn summary for developer mode."""
    route = route or {}
    planner = _PLANNER_LABELS.get(turn_plan.journey_phase, str(turn_plan.journey_phase))
    worker = provider_id or route.get("chosen_employee") or "unknown"
    cloud_llm_used = bool(route.get("cloud_llm_used"))
    used_brief = bool(route.get("used_brief_speech_fallback"))
    fallback = worker in ("genesis-local", "genesis-identity", "cloud-proof-failed") or (
        not cloud_llm_used and worker != "execution"
    )

    reasons: list[str] = []
    for attempt in route.get("attempts") or []:
        if not isinstance(attempt, dict):
            continue
        outcome = attempt.get("outcome") or ""
        if outcome in ("error", "skipped", "escalated"):
            emp = str(attempt.get("employee_id") or "?")
            if outcome == "selected":
                continue
            if outcome == "escalated" and attempt.get("calibration", {}).get("needs_rewrite"):
                reasons.append(f"{emp} calibration")
                continue
            reasons.append(
                _short_reason(
                    emp,
                    str(attempt.get("error") or ""),
                    str(attempt.get("skip_code") or ""),
                )
            )

    if fallback and not reasons and health_excluded:
        for row in health_excluded:
            eid = str(row.get("employee_id") or "?")
            code = str(row.get("reason") or row.get("detail") or "excluded")
            reasons.append(_short_reason(eid, code))

    # Deduplicate while preserving order
    seen: set[str] = set()
    unique_reasons: list[str] = []
    for r in reasons:
        if r not in seen:
            seen.add(r)
            unique_reasons.append(r)

    return {
        "planner": planner,
        "journey_phase": turn_plan.journey_phase,
        "planner_need": turn_plan.need,
        "planner_intent": turn_plan.intent,
        "planner_task": turn_plan.workforce_task,
        "llm_capability": route.get("llm_capability"),
        "proof_pin": route.get("proof_pin"),
        "worker": worker,
        "worker_model": route.get("chosen_model"),
        "elapsed_sec": round(elapsed_sec, 2),
        "fallback": fallback,
        "fallback_label": "да" if fallback else "нет",
        "cloud_llm_used": cloud_llm_used,
        "used_brief_speech": used_brief,
        "reasons": unique_reasons or None,
        "why_chosen": route.get("why_chosen"),
    }


def format_dev_stats_lines(stats: dict[str, Any]) -> str:
    """Plain-text block for logs / clipboard."""
    lines = [
        "Последний ответ:",
        f"Planner: {stats.get('planner')}",
    ]
    if stats.get("llm_capability"):
        lines.append(f"Capability: {stats['llm_capability']}")
    lines.extend([
        f"Worker: {stats.get('worker')}",
        f"Время: {stats.get('elapsed_sec')} s",
        f"Fallback: {stats.get('fallback_label')}",
    ])
    if stats.get("proof_pin"):
        lines.append(f"Proof pin: {stats['proof_pin']}")
    if stats.get("reasons"):
        lines.append("Причина:")
        for r in stats["reasons"]:
            lines.append(f"  {r}")
    return "\n".join(lines)


def save_last_dev_stats(memory_dir: Path, visitor_id: str, stats: dict[str, Any]) -> None:
    path = memory_dir / "workforce" / "last_dev_stats.json"
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "visitor_id": visitor_id[:64],
            "at": datetime.now(timezone.utc).isoformat(),
            "stats": stats,
            "text": format_dev_stats_lines(stats),
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def load_last_dev_stats(memory_dir: Path, visitor_id: str = "") -> dict[str, Any] | None:
    path = memory_dir / "workforce" / "last_dev_stats.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if visitor_id and data.get("visitor_id") != visitor_id[:64]:
            return None
        return data
    except (json.JSONDecodeError, OSError):
        return None
