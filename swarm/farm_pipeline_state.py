"""Single Execution State Machine for Opire Farm.

One pipeline_state drives Timeline, counters, KPI, and CEO views.
Never show both "in progress" and "paused" for the same task.
"""

from __future__ import annotations

from typing import Any

# Canonical ordered states (CEO-facing)
PIPELINE_STATES = (
    "QUEUED",
    "CLONING",
    "ANALYSING",
    "PATCHING",
    "TESTING",
    "COMMITTING",
    "DRAFT_PR",
    "WAITING_SUBMIT",
    "SUBMITTED",
    "MERGED",
    "PAID",
    "FAILED",
    "SKIPPED",
)

# Still counts as "Started" for Execution Success Rate
STARTED_STATES = frozenset(
    {
        "QUEUED",
        "CLONING",
        "ANALYSING",
        "PATCHING",
        "TESTING",
        "COMMITTING",
        "DRAFT_PR",
        "WAITING_SUBMIT",
        "SUBMITTED",
        "MERGED",
        "PAID",
        "FAILED",  # started then failed
    }
)

ACTIVE_ENGINE_STAGES = frozenset(
    {
        "queued",
        "running",
        "repo_intelligence",
        "planning",
        "routing",
        "implementation",
        "research",
        "validation",
        "commit",
        "pr_intelligence",
    }
)

_PAID = frozenset(
    {"payout_confirmed", "completed", "reward_approved", "payment_available", "withdraw"}
)
_MERGED = frozenset({"merged"}) | _PAID
_SUBMITTED = frozenset(
    {"pr_submitted", "maintainer_review", "changes_requested"}
) | _MERGED


def derive_pipeline_state(task: dict[str, Any]) -> str:
    """Single source of truth from task.status + execution report."""
    st = str(task.get("status") or "")
    ex = task.get("execution") if isinstance(task.get("execution"), dict) else {}
    stage = str(ex.get("stage") or "")
    stages = ex.get("stages") if isinstance(ex.get("stages"), dict) else {}
    impl = stages.get("implementation") if isinstance(stages.get("implementation"), dict) else {}
    patch_ready = bool(
        ex.get("patch_ready")
        or (impl.get("files_touched") or [])
        or (ex.get("ready_for_ceo") or {}).get("patch_ready")
    )
    route = str(
        (ex.get("ready_for_ceo") or {}).get("route")
        or (stages.get("routing") or {}).get("route")
        or impl.get("mode")
        or ""
    )

    if st == "skipped" or stage in ("skipped", "skipped_auto"):
        return "SKIPPED"
    if st in _PAID or task.get("real_income"):
        return "PAID"
    if st in _MERGED or task.get("merge_status") == "merged":
        return "MERGED"
    if st in _SUBMITTED or bool(task.get("pr_url")):
        return "SUBMITTED"
    if stage == "failed" or st in ("failed",) or (
        ex.get("ok") is False and stage not in ACTIVE_ENGINE_STAGES
    ):
        if task.get("execution_error") or stage == "failed":
            return "FAILED"

    # Terminal external pause only AFTER engine finished attempting
    needs_external = (
        st == "needs_external"
        or stage == "awaiting_external"
        or (route == "needs_external" and not patch_ready and stage not in ACTIVE_ENGINE_STAGES)
    )
    if needs_external and stage not in ACTIVE_ENGINE_STAGES | {"queued", "running"}:
        # Prefer SKIPPED path in auto factory; still expose honest pause if stuck
        if st == "skipped":
            return "SKIPPED"
        if st == "needs_external":
            return "SKIPPED"  # auto factory treats as dead-end
        return "FAILED"

    if st == "draft_pr" or stage == "awaiting_ceo_submit":
        return "WAITING_SUBMIT" if patch_ready else "DRAFT_PR"
    if patch_ready and stage in ("awaiting_ceo_submit", "draft_pr"):
        return "WAITING_SUBMIT"

    if stages.get("commit") and (stages.get("commit") or {}).get("ok"):
        if patch_ready:
            return "WAITING_SUBMIT" if st in ("draft_pr", "ceo_review") else "COMMITTING"
    if stages.get("validation") and not (stages.get("validation") or {}).get("skipped"):
        if not patch_ready and stage in ACTIVE_ENGINE_STAGES:
            return "TESTING"
        if (stages.get("validation") or {}).get("ok"):
            return "COMMITTING" if not patch_ready else "TESTING"
    if stages.get("implementation") or stages.get("research"):
        if stage in ACTIVE_ENGINE_STAGES or st == "executing":
            return "PATCHING"
        if patch_ready:
            return "DRAFT_PR"
    if stages.get("planning") or (stages.get("repo_intelligence") or {}).get("ok"):
        if (stages.get("planning") or {}).get("ok"):
            return "ANALYSING" if stage in ACTIVE_ENGINE_STAGES else "PATCHING"
        return "CLONING" if not (stages.get("repo_intelligence") or {}).get("ok") else "ANALYSING"
    if stages.get("repo_intelligence") or stage == "repo_intelligence":
        return "CLONING"

    if st == "executing" or stage in ("queued", "running") or st == "ceo_approved":
        # Approve + auto-execute: already Started from CEO POV
        if ex or st == "executing":
            return "QUEUED" if stage in ("", "queued", "running") or not stages else "CLONING"
        return "QUEUED"

    if st == "ceo_approved":
        return "QUEUED"

    return "QUEUED" if ex else "QUEUED"


def attach_pipeline_state(task: dict[str, Any]) -> dict[str, Any]:
    out = dict(task)
    state = derive_pipeline_state(out)
    out["pipeline_state"] = state
    out["pipeline_started"] = state in STARTED_STATES
    out["pipeline_label"] = state.replace("_", " ").title()
    return out


def count_execution_success(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """Counters derived only from pipeline_state (single SSOT)."""
    enriched = [attach_pipeline_state(t) for t in tasks]

    approved = sum(
        1
        for t in enriched
        if str(t.get("status") or "") not in ("skipped", "", "available")
    )
    started = sum(1 for t in enriched if t.get("pipeline_started"))
    draft_pr = sum(
        1
        for t in enriched
        if t.get("pipeline_state")
        in ("DRAFT_PR", "WAITING_SUBMIT", "SUBMITTED", "MERGED", "PAID")
    )
    completed = draft_pr  # reached Draft PR or beyond
    failed = sum(1 for t in enriched if t.get("pipeline_state") == "FAILED")
    skipped = sum(
        1
        for t in enriched
        if t.get("pipeline_state") == "SKIPPED" or t.get("status") == "skipped"
    )
    executing_now = sum(
        1
        for t in enriched
        if t.get("pipeline_state")
        in ("QUEUED", "CLONING", "ANALYSING", "PATCHING", "TESTING", "COMMITTING")
    )
    merged = sum(1 for t in enriched if t.get("pipeline_state") in ("MERGED", "PAID"))
    paid = sum(1 for t in enriched if t.get("pipeline_state") == "PAID")

    return {
        "approved": approved,
        "started": started,
        "execution": executing_now,
        "completed": completed,
        "failed": failed,
        "skipped": skipped,
        "draft_pr": draft_pr,
        "merged": merged,
        "paid": paid,
        "start_rate": round(started / approved, 3) if approved else None,
        "complete_rate": round(completed / approved, 3) if approved else None,
        "payout_success": {
            "found_note_ru": "Found — из Scanner (panel.scan.scanned)",
            "approved": approved,
            "executed": started,
            "draft_pr": draft_pr,
            "merged": merged,
            "paid": paid,
            "rates": {
                "approve_to_execute": round(started / approved, 3) if approved else None,
                "execute_to_draft_pr": round(draft_pr / started, 3) if started else None,
                "draft_pr_to_merge": round(merged / draft_pr, 3) if draft_pr else None,
                "merge_to_paid": round(paid / merged, 3) if merged else None,
            },
            "note_ru": (
                "Главная метрика Opire Farm: Paid / Merged. "
                "Пока Paid=0 — цикл не доказан. Смотри rates, где узкое место."
            ),
        },
        "tasks": enriched,
        "note_ru": (
            "Один pipeline_state на задачу. Started = Execution стартовал (QUEUED+). "
            "Execution = сейчас в работе. Draft PR = пакет готов / дальше."
        ),
    }
