"""Farm Opire AUTO-RUN orchestration (Owner).

After one Farm start, the engine progresses without CEO buttons on every stage.
CEO intervenes only for REVIEW / risk / budget / Stop / exhausted retries.

Estimated ≠ REAL. No automatic spend. Infinite retry forbidden.
"""

from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from typing import Any, Callable

MONEY_MODE_THRESHOLD = 80.0
MAX_EXECUTION_ATTEMPTS = 3
QUEUED_WATCHDOG_S = 45.0
EXECUTING_STALL_S = 600.0
RETRY_BACKOFF_S = (15, 45, 120)

_TICK_LOCK = threading.Lock()


def _env_flag(name: str, default: str = "1") -> bool:
    flag = (os.environ.get(name) or default).strip().lower()
    return flag not in ("0", "false", "no", "off")


def farm_autonomous_enabled() -> bool:
    """Master AUTO-RUN switch (default ON)."""
    return _env_flag("FARM_AUTONOMOUS", "1")


def farm_auto_approve_enabled() -> bool:
    if not farm_autonomous_enabled():
        return _env_flag("FARM_AUTO_APPROVE", "0")
    return _env_flag("FARM_AUTO_APPROVE", "1")


def farm_auto_submit_enabled() -> bool:
    """Auto Submit PR after Draft when patch ready (default ON under autonomous)."""
    if not farm_autonomous_enabled():
        return _env_flag("FARM_AUTO_SUBMIT_PR", "0")
    return _env_flag("FARM_AUTO_SUBMIT_PR", "1")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _task_age_seconds(task: dict[str, Any]) -> float:
    raw = str(task.get("updated_at") or task.get("approved_at") or "")
    if not raw:
        return 0.0
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds())
    except Exception:
        return 0.0


def _is_active_factory_task(task: dict[str, Any]) -> bool:
    st = str(task.get("status") or "")
    if st == "executing":
        return True
    if st in ("draft_pr", "ceo_review") and not (
        (task.get("execution") or {}).get("patch_ready")
        or ((task.get("execution") or {}).get("stages") or {})
        .get("implementation", {})
        .get("files_touched")
    ):
        # draft without patch still occupies line in older semantics — treat as active
        return True
    return False


def _has_patch(task: dict[str, Any]) -> bool:
    ex = task.get("execution") or {}
    impl = (ex.get("stages") or {}).get("implementation") or {}
    return bool(ex.get("patch_ready") or (impl.get("files_touched") or []))


def _ready_for_retry(task: dict[str, Any]) -> bool:
    raw = str(task.get("next_retry_at") or "")
    if not raw:
        return True
    try:
        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= ts
    except Exception:
        return True


def _set_retry_backoff(task: dict[str, Any]) -> None:
    attempts = int(task.get("execution_attempts") or 0)
    delay = RETRY_BACKOFF_S[min(attempts, len(RETRY_BACKOFF_S) - 1)]
    from datetime import timedelta

    task["next_retry_at"] = (
        datetime.now(timezone.utc) + timedelta(seconds=delay)
    ).isoformat()


def run_autonomous_tick(
    engine: Any,
    *,
    max_actions: int = 3,
    start_execution: Callable[..., dict[str, Any]] | None = None,
    decide: Callable[..., dict[str, Any]] | None = None,
    submit_pr: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    One durable orchestration pulse:
      watchdog heal → auto-submit drafts → drain QUEUED → auto-approve GO≥80
    Idempotent; never infinite retry; never invents REAL payout.
    """
    start_execution = start_execution or engine.start_execution
    decide = decide or engine.decide
    submit_pr = submit_pr or engine.ceo_submit_pr

    if not _TICK_LOCK.acquire(blocking=False):
        return {
            "ok": True,
            "skipped": "tick_busy",
            "actions": [],
            "autonomous": farm_autonomous_enabled(),
        }

    actions: list[dict[str, Any]] = []
    try:
        state = engine._load()
        tasks = state.setdefault("tasks", {})

        # --- Watchdog: QUEUED zombies → ceo_approved + pending ---
        for tid, raw in list(tasks.items()):
            t = dict(raw or {})
            st = str(t.get("status") or "")
            pipe = str(t.get("pipeline_state") or "")
            stage = str((t.get("execution") or {}).get("stage") or "")
            age = _task_age_seconds(t)
            if st == "executing" and (
                pipe in ("QUEUED", "") or stage in ("queued", "")
            ):
                if age >= QUEUED_WATCHDOG_S and not (
                    (t.get("execution") or {}).get("stages") or {}
                ):
                    attempts = int(t.get("execution_attempts") or 0)
                    if attempts >= MAX_EXECUTION_ATTEMPTS:
                        t["status"] = "skipped"
                        t["skip_reason"] = "queued_watchdog_exhausted"
                        t["ceo_note"] = "auto_skip:queued_timeout_max_attempts"
                        t["updated_at"] = _now()
                        tasks[tid] = t
                        actions.append(
                            {
                                "type": "watchdog_skip",
                                "task_id": tid,
                                "reason": "max_attempts",
                            }
                        )
                        continue
                    t["status"] = "ceo_approved"
                    t["pipeline_state"] = "QUEUED"
                    t["pending_execution"] = True
                    t["auto_retry_execution"] = True
                    t["execution_heal"] = "watchdog_queued"
                    t["execution_error"] = None
                    t["execution"] = {
                        "ok": False,
                        "stage": "queued",
                        "message_ru": (
                            "Watchdog: очередь не стартовала — "
                            "авто-повтор Clone без кнопки CEO."
                        ),
                    }
                    t["updated_at"] = _now()
                    t.pop("next_retry_at", None)  # allow drain in same tick
                    tasks[tid] = t
                    actions.append(
                        {"type": "watchdog_heal", "task_id": tid, "age_s": int(age)}
                    )

            # Stall while supposedly executing mid-pipeline too long
            if st == "executing" and age >= EXECUTING_STALL_S:
                attempts = int(t.get("execution_attempts") or 0) + 1
                t["execution_attempts"] = attempts
                if attempts >= MAX_EXECUTION_ATTEMPTS:
                    t["status"] = "skipped"
                    t["skip_reason"] = "executing_stall_exhausted"
                    t["updated_at"] = _now()
                    tasks[tid] = t
                    actions.append(
                        {
                            "type": "watchdog_skip",
                            "task_id": tid,
                            "reason": "executing_stall",
                        }
                    )
                else:
                    t["status"] = "ceo_approved"
                    t["pending_execution"] = True
                    t["auto_retry_execution"] = True
                    t["execution_error"] = None
                    t["execution_heal"] = "watchdog_stall"
                    t["updated_at"] = _now()
                    _set_retry_backoff(t)
                    tasks[tid] = t
                    actions.append(
                        {"type": "watchdog_stall_retry", "task_id": tid}
                    )

        if actions:
            state["tasks"] = tasks
            engine._save(state)

        if len(actions) >= max_actions:
            return _tick_result(actions)

        # --- Auto-submit Draft PR (policy) ---
        if farm_auto_submit_enabled():
            for tid, raw in list(tasks.items()):
                if len(actions) >= max_actions:
                    break
                t = dict(raw or {})
                if str(t.get("status") or "") not in ("draft_pr", "ceo_review"):
                    continue
                if not _has_patch(t):
                    continue
                if t.get("auto_submit_done") or t.get("pr_url") or t.get("pr_id"):
                    continue
                if t.get("auto_submit_in_flight"):
                    continue
                t["auto_submit_in_flight"] = True
                tasks[tid] = t
                state["tasks"] = tasks
                engine._save(state)
                try:
                    out = submit_pr(
                        tid,
                        note="auto_submit_pr",
                        live=not bool(os.environ.get("PYTEST_CURRENT_TEST")),
                    )
                except TypeError:
                    out = submit_pr(tid, note="auto_submit_pr")
                except Exception as exc:  # noqa: BLE001
                    out = {"ok": False, "error": str(exc)[:160]}
                state = engine._load()
                tasks = state.setdefault("tasks", {})
                t2 = dict(tasks.get(tid) or t)
                t2.pop("auto_submit_in_flight", None)
                if out.get("ok"):
                    t2["auto_submit_done"] = True
                    actions.append({"type": "auto_submit", "task_id": tid, "ok": True})
                else:
                    t2["auto_submit_error"] = str(out.get("error") or "submit_failed")[
                        :160
                    ]
                    actions.append(
                        {
                            "type": "auto_submit",
                            "task_id": tid,
                            "ok": False,
                            "error": t2["auto_submit_error"],
                        }
                    )
                tasks[tid] = t2
                state["tasks"] = tasks
                engine._save(state)

        if len(actions) >= max_actions:
            return _tick_result(actions)

        # --- Drain: pending / ceo_approved / zombie QUEUED ---
        factory_busy = any(_is_active_factory_task(t) for t in tasks.values())
        if not factory_busy:
            drain_id = _pick_drain_candidate(tasks)
            if drain_id:
                t = dict(tasks[drain_id])
                if _ready_for_retry(t):
                    attempts = int(t.get("execution_attempts") or 0) + 1
                    t["execution_attempts"] = attempts
                    t["pending_execution"] = False
                    t["auto_retry_execution"] = False
                    t["status"] = "executing"
                    t["pipeline_state"] = "QUEUED"
                    t["updated_at"] = _now()
                    tasks[drain_id] = t
                    state["tasks"] = tasks
                    engine._save(state)
                    if attempts > MAX_EXECUTION_ATTEMPTS:
                        t["status"] = "skipped"
                        t["skip_reason"] = "execution_attempts_exhausted"
                        tasks[drain_id] = t
                        engine._save(state)
                        actions.append(
                            {
                                "type": "hard_skip",
                                "task_id": drain_id,
                                "reason": "max_attempts",
                            }
                        )
                    else:
                        # Background start — tick must not block on Clone
                        def _bg(rid: str = drain_id) -> None:
                            try:
                                start_execution(rid, clone=True)
                            except Exception:
                                pass

                        if os.environ.get("PYTEST_CURRENT_TEST"):
                            out = start_execution(drain_id, clone=True)
                            actions.append(
                                {
                                    "type": "drain_start",
                                    "task_id": drain_id,
                                    "ok": bool(out.get("ok")),
                                    "error": out.get("error"),
                                }
                            )
                        else:
                            threading.Thread(
                                target=_bg,
                                name=f"farm-drain-{drain_id[:20]}",
                                daemon=True,
                            ).start()
                            actions.append(
                                {
                                    "type": "drain_start",
                                    "task_id": drain_id,
                                    "queued": True,
                                }
                            )

        if len(actions) >= max_actions:
            return _tick_result(actions)

        # --- Auto-approve GO ≥ 80 from last_scan ---
        if farm_auto_approve_enabled() and not any(
            str(t.get("status") or "")
            in ("executing", "ceo_approved", "draft_pr", "ceo_review")
            or t.get("pending_execution")
            for t in tasks.values()
        ):
            cand_id = _pick_auto_approve_id(engine)
            if cand_id:
                out = decide(cand_id, "approve", note="auto_approve_go")
                actions.append(
                    {
                        "type": "auto_approve",
                        "task_id": cand_id,
                        "ok": bool(out.get("ok")),
                        "error": out.get("error"),
                        "message_ru": out.get("message_ru"),
                    }
                )

        return _tick_result(actions)
    finally:
        _TICK_LOCK.release()


def _tick_result(actions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "ok": True,
        "queue_id": "BOUNTY_EXECUTION_QUEUE",
        "autonomous": farm_autonomous_enabled(),
        "auto_approve": farm_auto_approve_enabled(),
        "auto_submit": farm_auto_submit_enabled(),
        "actions": actions,
        "action_count": len(actions),
        "at": _now(),
        "ceo_gates_ru": (
            "CEO только: Stop / лимиты / REVIEW / ToS / large scope / "
            "исчерпанные retry. Approve/Start/Submit на GO не требуются. "
            "API Farm — отдельная очередь (API_FARM_QUEUE)."
        ),
    }


def _pick_drain_candidate(tasks: dict[str, Any]) -> str | None:
    """Prefer pending_execution, then failed retries, then ceo_approved, then QUEUED."""
    pending: list[tuple[str, dict[str, Any]]] = []
    failed_retry: list[tuple[str, dict[str, Any]]] = []
    approved: list[tuple[str, dict[str, Any]]] = []
    queued_exec: list[tuple[str, dict[str, Any]]] = []
    for tid, raw in tasks.items():
        t = dict(raw or {})
        st = str(t.get("status") or "")
        if t.get("pending_execution") and st in (
            "ceo_approved",
            "executing",
            "execution_failed",
        ):
            pending.append((tid, t))
        elif st == "execution_failed" and t.get("auto_retry_execution"):
            failed_retry.append((tid, t))
        elif st == "ceo_approved":
            approved.append((tid, t))
        elif st == "executing":
            stage = str((t.get("execution") or {}).get("stage") or "")
            pipe = str(t.get("pipeline_state") or "")
            if stage in ("queued", "") and pipe in ("QUEUED", ""):
                if not ((t.get("execution") or {}).get("stages") or {}):
                    queued_exec.append((tid, t))
    for bucket in (pending, failed_retry, approved, queued_exec):
        for tid, t in bucket:
            if int(t.get("execution_attempts") or 0) > MAX_EXECUTION_ATTEMPTS:
                continue
            if not _ready_for_retry(t):
                continue
            err = str(t.get("execution_error") or "")
            if err and not err.startswith("zombie") and err not in (
                "factory_busy",
                "zombie_queued_healed",
                "zombie_queued_cleared_for_factory",
            ):
                # Hard errors: only drain when pending_execution / auto_retry set
                if t.get("auto_retry_execution") or t.get("pending_execution"):
                    pass
                else:
                    continue
            return tid
    return None


def _pick_auto_approve_id(engine: Any) -> str | None:
    from swarm.farm_preflight import run_preflight

    state = engine._load()
    tasks = state.get("tasks") or {}
    skip_ids = set()
    for tid, t in tasks.items():
        skip_ids.add(str(tid))
        if t.get("native_id"):
            skip_ids.add(str(t["native_id"]))
            skip_ids.add(f"opire:{t['native_id']}")
    for sid in state.get("skipped_forever") or []:
        skip_ids.add(str(sid))

    cached = state.get("last_scan") if isinstance(state.get("last_scan"), dict) else {}
    rows = list(cached.get("candidates") or []) + list(
        cached.get("candidates_take_all") or []
    )
    for cand in rows:
        rid = str(cand.get("id") or "")
        if not rid or rid in skip_ids:
            continue
        native = str(cand.get("native_id") or "")
        if native and (native in skip_ids or f"opire:{native}" in skip_ids):
            continue
        conf = float(
            cand.get("overall_confidence_pct")
            or cand.get("success_probability_pct")
            or 0
        )
        if conf < MONEY_MODE_THRESHOLD:
            continue
        pf = cand.get("preflight") if isinstance(cand.get("preflight"), dict) else None
        if not pf:
            pf = run_preflight(cand, deep=False, min_confidence=MONEY_MODE_THRESHOLD)
        if not pf.get("go") or not pf.get("auto_execute_allowed"):
            continue
        # Soft risk → leave for CEO REVIEW (do not auto-approve)
        if pf.get("verdict") == "REVIEW":
            continue
        return rid
    return None
