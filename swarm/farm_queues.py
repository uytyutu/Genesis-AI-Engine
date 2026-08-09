"""Farm queue separation — Bounty ≠ API Farm ≠ Revenue Farm."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

# Canonical queue ids (orchestration SSOT)
BOUNTY_EXECUTION_QUEUE = "BOUNTY_EXECUTION_QUEUE"
REVENUE_FARM_QUEUE = "REVENUE_FARM_QUEUE"
API_FARM_QUEUE = "API_FARM_QUEUE"

QUEUE_IDS = (
    BOUNTY_EXECUTION_QUEUE,
    REVENUE_FARM_QUEUE,
    API_FARM_QUEUE,
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def bounty_queue_snapshot(opire_engine: Any | None) -> dict[str, Any]:
    """Bounty / Opire Execution Engine queue — independent of API Farm."""
    if opire_engine is None:
        return {
            "queue_id": BOUNTY_EXECUTION_QUEUE,
            "worker": "swarm.farm_autonomous + OpireFarm.start_execution",
            "independent_of_api_farm": True,
            "pending": 0,
            "running": 0,
            "failed": 0,
            "completed": 0,
            "pending_execution": [],
            "failed_jobs": [],
            "watchdog": {"alive": False},
        }
    try:
        state = opire_engine._load()
    except Exception as exc:  # noqa: BLE001
        return {
            "queue_id": BOUNTY_EXECUTION_QUEUE,
            "worker": "swarm.farm_autonomous + OpireFarm.start_execution",
            "error": str(exc)[:200],
            "pending": 0,
            "running": 0,
            "failed": 0,
            "completed": 0,
            "pending_execution": [],
            "failed_jobs": [],
            "watchdog": {"alive": False},
        }

    tasks = state.get("tasks") or {}
    pending_execution: list[dict[str, Any]] = []
    failed_jobs: list[dict[str, Any]] = []
    pending = running = failed = completed = 0

    for tid, raw in tasks.items():
        t = dict(raw or {})
        st = str(t.get("status") or "")
        ex = t.get("execution") or {}
        stage = str(ex.get("stage") or "")
        title = str(t.get("title") or t.get("issue_title") or tid)[:120]

        if t.get("pending_execution") or (
            st in ("ceo_approved", "executing") and stage in ("queued", "")
        ):
            pending += 1
            pending_execution.append(
                {
                    "task_id": tid,
                    "title": title,
                    "status": st,
                    "stage": stage or "queued",
                    "error": t.get("execution_error") or ex.get("error") or "",
                    "retry_count": int(t.get("execution_attempts") or 0),
                    "next_retry": t.get("next_retry_at"),
                    "blocker": t.get("skip_reason")
                    or t.get("execution_heal")
                    or ("pending_execution" if t.get("pending_execution") else ""),
                }
            )
        if st == "executing" and stage not in ("queued", "", "failed", "skipped"):
            running += 1
        if st in ("execution_failed",) or stage == "failed" or st == "failed":
            failed += 1
            failed_jobs.append(
                {
                    "task_id": tid,
                    "title": title,
                    "status": st,
                    "stage": stage or "failed",
                    "error": str(
                        t.get("execution_error")
                        or t.get("ceo_note")
                        or ex.get("error")
                        or ex.get("message_ru")
                        or ""
                    )[:400],
                    "retry_count": int(t.get("execution_attempts") or 0),
                    "next_retry": t.get("next_retry_at"),
                    "blocker": str(t.get("skip_reason") or "execution_failed"),
                    "error_class": t.get("error_class") or ex.get("error_class"),
                    "retryable": t.get("retryable", ex.get("retryable")),
                    "next_action": t.get("next_action") or ex.get("next_action"),
                    "queue": BOUNTY_EXECUTION_QUEUE,
                    "workspace": (t.get("failure") or {}).get("workspace")
                    or (ex.get("workspace") or ""),
                }
            )
        if st in (
            "merged",
            "reward_approved",
            "payment_available",
            "withdraw",
            "payout_confirmed",
            "completed",
            "draft_pr",
            "pr_submitted",
        ):
            completed += 1

    from swarm.farm_autonomous import farm_autonomous_enabled

    watchdog_mode = "IDLE"
    if running:
        watchdog_mode = "RUNNING"
    elif any(
        str((t.get("failure") or {}).get("next_action") or t.get("next_action") or "")
        == "RETRY_WITH_BACKOFF"
        or t.get("auto_retry_execution")
        for t in tasks.values()
        if isinstance(t, dict)
    ):
        watchdog_mode = "RETRYING"
    elif failed and not pending:
        watchdog_mode = "FAILED"
    elif pending:
        watchdog_mode = "WAITING_APPROVAL" if not farm_autonomous_enabled() else "ALIVE"
    elif farm_autonomous_enabled():
        watchdog_mode = "ALIVE"

    return {
        "queue_id": BOUNTY_EXECUTION_QUEUE,
        "worker": "swarm.farm_autonomous.run_autonomous_tick → OpireFarm.start_execution",
        "independent_of_api_farm": True,
        "pending": pending,
        "running": running,
        "failed": failed,
        "completed": completed,
        "pending_execution": pending_execution[:20],
        "failed_jobs": failed_jobs[:20],
        "watchdog": {
            "alive": farm_autonomous_enabled(),
            "mode": watchdog_mode,
            "module": "swarm.farm_autonomous",
            "heals_queued_zombies": True,
            "heals_executing_stall": True,
            "max_execution_attempts": 3,
        },
        "policy": {
            "advance_on_fail": _bounty_advance_on_fail(),
            "note_ru": (
                "execution_failed сохраняет job с точной причиной. "
                "Следующая bounty только если FARM_BOUNTY_ADVANCE_ON_FAIL=1."
            ),
        },
        "at": _now(),
    }


def _bounty_advance_on_fail() -> bool:
    import os

    flag = (os.environ.get("FARM_BOUNTY_ADVANCE_ON_FAIL") or "0").strip().lower()
    return flag in ("1", "true", "yes", "on")


def api_farm_queue_snapshot(api_farm_store: Any | None = None) -> dict[str, Any]:
    from swarm.farm_channels.rapidapi.monitor import portfolio_metrics
    from swarm.farm_channels.rapidapi.revenue import revenue_summary
    from swarm.farm_channels.rapidapi.store import ApiFarmStore
    from swarm.farm_channels.rapidapi.worker import status_payload

    store = api_farm_store or ApiFarmStore()
    port = portfolio_metrics(store)
    rev = revenue_summary(store)
    st = status_payload(store)
    jobs = store.list_jobs(limit=30)
    queued = [j for j in jobs if j.get("status") == "queued"]
    running = [j for j in jobs if j.get("status") == "running"]
    return {
        "queue_id": API_FARM_QUEUE,
        "worker": "swarm.farm_channels.rapidapi.worker.step (ApiFarmService)",
        "independent_of_bounty": True,
        "candidates": port.get("candidates"),
        "building": port.get("building"),
        "testing": port.get("testing"),
        "ready": port.get("ready"),
        "published": port.get("published"),
        "active": port.get("active"),
        "revenue": {
            "actual": rev.get("actual_revenue"),
            "pending": rev.get("pending_payout"),
            "gross": rev.get("gross_revenue"),
        },
        "jobs_queued": len(queued),
        "jobs_running": len(running),
        "ceo_action": st.get("ceo_action") or [],
        "best_candidate": st.get("best_candidate"),
        "at": _now(),
    }


def revenue_farm_queue_snapshot() -> dict[str, Any]:
    """Revenue Farm = monetization / PAID_OUT track (not bounty)."""
    from swarm.farm_channels.rapidapi.revenue import revenue_summary
    from swarm.farm_channels.rapidapi.store import ApiFarmStore
    from swarm.farm_channels.rapidapi.public_base import paypal_payout_confirmed

    store = ApiFarmStore()
    rev = revenue_summary(store)
    return {
        "queue_id": REVENUE_FARM_QUEUE,
        "worker": "swarm.farm_channels.rapidapi.revenue (ingest → Hard REAL ledger)",
        "independent_of_bounty": True,
        "actual_revenue": rev.get("actual_revenue"),
        "pending_payout": rev.get("pending_payout"),
        "paid_out": rev.get("paid_out"),
        "paypal_payout_confirmed": paypal_payout_confirmed(),
        "rule_ru": "Actual только PAID_OUT Hard REAL. Bounty Impossible сюда не пишет.",
        "at": _now(),
    }


def build_farm_queues_status(opire_engine: Any | None = None) -> dict[str, Any]:
    return {
        "ok": True,
        "queues": list(QUEUE_IDS),
        "bounty": bounty_queue_snapshot(opire_engine),
        "api_farm": api_farm_queue_snapshot(),
        "revenue_farm": revenue_farm_queue_snapshot(),
        "separation_ru": (
            "BOUNTY_EXECUTION_QUEUE ≠ API_FARM_QUEUE. "
            "AUTO-RUN bounty не кормит API Farm и наоборот."
        ),
        "at": _now(),
    }
