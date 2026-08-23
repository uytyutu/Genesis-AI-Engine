"""Farm Stabilization — error taxonomy, workspace inventory, spider idle backoff.

No new Farm products. Idempotent lifecycle helpers for Bounty/Opire + Global Spider.
"""

from __future__ import annotations

import json
import os
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Error classes (CEO Farm Stabilization Pass) ---
TRANSIENT_ERROR = "TRANSIENT_ERROR"
WORKSPACE_CORRUPTION = "WORKSPACE_CORRUPTION"
PERMANENT_ERROR = "PERMANENT_ERROR"

# Workspace lifecycle labels (quarantine = rename, never destructive delete of ACTIVE)
WS_ACTIVE = "ACTIVE"
WS_STALE = "STALE"
WS_ORPHANED = "ORPHANED"
WS_QUARANTINED = "QUARANTINED"
WS_CLONING = "CLONING_TEMP"

# Spider idle backoff ladder (seconds)
IDLE_BACKOFF_LADDER = (8, 16, 32, 60)
DEFAULT_MAX_EXECUTION_ATTEMPTS = 3


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def max_execution_attempts() -> int:
    raw = (os.environ.get("FARM_MAX_EXECUTION_ATTEMPTS") or "").strip()
    if raw.isdigit():
        return max(1, min(10, int(raw)))
    return DEFAULT_MAX_EXECUTION_ATTEMPTS


def classify_execution_failure(
    *,
    error: str = "",
    error_code: str = "",
    detail: str = "",
) -> dict[str, Any]:
    """Map failure → error_class + retryable + next_action."""
    code = (error_code or "").strip().lower()
    text = f"{error}\n{detail}".lower()

    if code in (
        "workspace_dirty",
        "workspace_cleanup_failed",
        "workspace_not_empty",
        "workspace_promote_failed",
        "clone_missing_git_dir",
    ) or (
        "already exists" in text and "not an empty" in text
    ) or "workspace_promote_failed" in text or "cannot free clone dest" in text:
        return {
            "error_class": WORKSPACE_CORRUPTION,
            "retryable": True,
            "next_action": "QUARANTINE_AND_RETRY",
            "code": code or "WORKSPACE_EXISTS",
        }

    if code in ("concurrent_clone",) or "timeout" in text or "timed out" in text:
        return {
            "error_class": TRANSIENT_ERROR,
            "retryable": True,
            "next_action": "RETRY_WITH_BACKOFF",
            "code": code or "TRANSIENT",
        }

    if code in (
        "repo_not_found",
        "missing_repository",
        "git_missing",
        "auth_required",
        "not_auto_executable",
    ) or "repository not found" in text or "git_not_found" in text:
        return {
            "error_class": PERMANENT_ERROR,
            "retryable": False,
            "next_action": "FAILED",
            "code": code or "PERMANENT",
        }

    # Default: treat unknown as retryable transient (bounded by attempt cap)
    return {
        "error_class": TRANSIENT_ERROR,
        "retryable": True,
        "next_action": "RETRY_WITH_BACKOFF",
        "code": code or "execution_failed",
    }


def is_valid_git_workspace(src: Path) -> bool:
    root = Path(src)
    if not root.is_dir() or not (root / ".git").exists():
        return False
    # Nested staging leftover = corrupt
    try:
        for child in root.iterdir():
            if child.name.startswith(".cloning-"):
                return False
    except OSError:
        return False
    return True


def classify_workspace_path(path: Path, *, active_ids: set[str] | None = None) -> str:
    p = Path(path)
    name = p.name
    if name.startswith(".trash-") or name.startswith(".quarantine-"):
        return WS_QUARANTINED
    if name.startswith(".cloning-"):
        return WS_CLONING
    active = active_ids or set()
    if name in active:
        return WS_ACTIVE
    if not p.is_dir():
        return WS_ORPHANED
    src = p / "src"
    age_s = 0.0
    try:
        age_s = max(0.0, time.time() - p.stat().st_mtime)
    except OSError:
        return WS_ORPHANED
    if is_valid_git_workspace(src):
        # Old unused clone with valid git → STALE (safe to quarantine, not delete)
        return WS_STALE if age_s > 3600 else WS_ACTIVE
    if age_s > 900:
        return WS_ORPHANED
    return WS_STALE


def inventory_workspaces(
    root: Path,
    *,
    active_reward_ids: set[str] | None = None,
) -> list[dict[str, Any]]:
    base = Path(root)
    if not base.is_dir():
        return []
    active: set[str] = set()
    for rid in active_reward_ids or ():
        safe = "".join(c if c.isalnum() or c in "_-" else "_" for c in rid)[:80]
        active.add(safe)
    rows: list[dict[str, Any]] = []
    for child in sorted(base.iterdir(), key=lambda p: p.name):
        label = classify_workspace_path(child, active_ids=active)
        rows.append(
            {
                "path": str(child),
                "name": child.name,
                "state": label,
                "has_src": (child / "src").is_dir() if child.is_dir() else False,
                "valid_git": is_valid_git_workspace(child / "src"),
            }
        )
    return rows


def cleanup_stale_workspaces(
    root: Path,
    *,
    active_reward_ids: set[str] | None = None,
    quarantine_fn: Any | None = None,
) -> dict[str, Any]:
    """Quarantine ORPHANED / CLONING_TEMP / old trash — never delete ACTIVE."""
    from swarm.farm_execution_engine import quarantine_path, remove_path_robust

    qfn = quarantine_fn or quarantine_path
    inventory = inventory_workspaces(root, active_reward_ids=active_reward_ids)
    actions: list[dict[str, Any]] = []
    for row in inventory:
        state = row["state"]
        path = Path(row["path"])
        if state == WS_ACTIVE:
            continue
        if state in (WS_CLONING, WS_QUARANTINED):
            # Safe: remove temp / already-quarantined leftovers best-effort
            res = remove_path_robust(path)
            actions.append({"name": row["name"], "action": "remove_temp", "result": res})
            continue
        if state in (WS_ORPHANED, WS_STALE):
            # Only quarantine orphaned; STALE without active job also quarantine
            if state == WS_STALE and row["name"] in (active_reward_ids or set()):
                continue
            res = qfn(path)
            actions.append(
                {
                    "name": row["name"],
                    "action": "quarantine",
                    "state": state,
                    "result": res,
                }
            )
    return {"ok": True, "scanned": len(inventory), "actions": actions, "inventory": inventory}


def assess_hunt_inputs(cfg: dict[str, Any], *, places_configured: bool) -> dict[str, Any]:
    """Return whether Global Spider has real work (no fake tasks)."""
    seeds = [str(x).strip() for x in (cfg.get("seed_targets") or []) if str(x).strip()]
    places_q = [str(x).strip() for x in (cfg.get("places_queries") or []) if str(x).strip()]
    niches = [str(x).strip() for x in (cfg.get("profitable_niches") or []) if str(x).strip()]
    toloka = [
        str(x).strip() for x in (cfg.get("toloka_task_categories") or []) if str(x).strip()
    ]
    url_seeds = [s for s in seeds if s.startswith(("http://", "https://"))]
    text_seeds = [s for s in seeds if s and not s.startswith(("http://", "https://"))]
    has_places_work = bool(places_configured) and bool(places_q or niches or text_seeds)
    has_work = bool(url_seeds) or has_places_work
    return {
        "has_work": has_work,
        "url_seeds": len(url_seeds),
        "text_seeds": len(text_seeds),
        "places_queries": len(places_q),
        "profitable_niches": len(niches),
        "toloka_categories": len(toloka),
        "places_configured": bool(places_configured),
        "reason": (
            "ok"
            if has_work
            else "no_seeds_places_or_places_key — IDLE / WAITING_FOR_INPUT"
        ),
    }


def idle_state_path(memory_dir: Path) -> Path:
    return Path(memory_dir) / "global_spider_idle.json"


def load_idle_state(memory_dir: Path) -> dict[str, Any]:
    path = idle_state_path(memory_dir)
    if not path.is_file():
        return {
            "mode": "ACTIVE",
            "backoff_sec": IDLE_BACKOFF_LADDER[0],
            "consecutive_idle": 0,
            "next_hunt_at": None,
        }
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {
            "mode": "ACTIVE",
            "backoff_sec": IDLE_BACKOFF_LADDER[0],
            "consecutive_idle": 0,
            "next_hunt_at": None,
        }


def save_idle_state(memory_dir: Path, state: dict[str, Any]) -> None:
    path = idle_state_path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    state = dict(state)
    state["updated_at"] = _now()
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def mark_idle_no_work(memory_dir: Path) -> dict[str, Any]:
    st = load_idle_state(memory_dir)
    n = int(st.get("consecutive_idle") or 0) + 1
    idx = min(n - 1, len(IDLE_BACKOFF_LADDER) - 1)
    backoff = IDLE_BACKOFF_LADDER[max(0, idx)]
    next_at = datetime.now(timezone.utc).timestamp() + backoff
    out = {
        "mode": "IDLE",
        "status": "WAITING_FOR_INPUT",
        "consecutive_idle": n,
        "backoff_sec": backoff,
        "next_hunt_at": datetime.fromtimestamp(next_at, tz=timezone.utc).isoformat(),
        "next_hunt_ts": next_at,
        "note_ru": "IDLE — нет seeds/places для охоты; backoff без fake tasks.",
    }
    save_idle_state(memory_dir, out)
    return out


def mark_hunt_active(memory_dir: Path) -> dict[str, Any]:
    out = {
        "mode": "ACTIVE",
        "status": "HUNTING",
        "consecutive_idle": 0,
        "backoff_sec": IDLE_BACKOFF_LADDER[0],
        "next_hunt_at": None,
        "next_hunt_ts": None,
        "note_ru": "Есть входной поток — interval сброшен.",
    }
    save_idle_state(memory_dir, out)
    return out


def should_skip_hunt(memory_dir: Path) -> tuple[bool, dict[str, Any]]:
    """If idle backoff not elapsed → skip active hunt cycle."""
    st = load_idle_state(memory_dir)
    if str(st.get("mode") or "") != "IDLE":
        return False, st
    ts = st.get("next_hunt_ts")
    try:
        next_ts = float(ts) if ts is not None else 0.0
    except (TypeError, ValueError):
        next_ts = 0.0
    if next_ts and time.time() < next_ts:
        return True, st
    return False, st


def build_failure_visibility(
    *,
    job_id: str,
    queue: str,
    stage: str,
    attempt: int,
    error: str = "",
    error_code: str = "",
    workspace: str = "",
) -> dict[str, Any]:
    classified = classify_execution_failure(
        error=error, error_code=error_code, detail=error
    )
    max_a = max_execution_attempts()
    retryable = bool(classified["retryable"]) and attempt < max_a
    next_action = classified["next_action"]
    if not retryable:
        next_action = "FAILED"
        classified = {**classified, "retryable": False, "next_action": "FAILED"}
    return {
        "job_id": job_id,
        "queue": queue,
        "stage": stage,
        "attempt": attempt,
        "error_class": classified["error_class"],
        "error_code": classified.get("code") or error_code,
        "retryable": retryable,
        "workspace": workspace,
        "next_action": next_action,
        "error": str(error)[:800],
        "at": _now(),
    }


def quarantine_workspace_safe(ws: Path) -> dict[str, Any]:
    """Rename workspace aside (``.quarantine-*``) — not destructive delete."""
    from swarm.farm_execution_engine import quarantine_path

    target = Path(ws)
    if not target.exists():
        return {"ok": True, "quarantined": False, "path": str(target)}
    # Prefer explicit .quarantine- prefix for inventory
    trash = target.parent / f".quarantine-{target.name}-{uuid.uuid4().hex[:10]}"
    try:
        target.rename(trash)
        return {
            "ok": True,
            "quarantined": True,
            "path": str(target),
            "quarantine": str(trash),
        }
    except OSError:
        return quarantine_path(target)
