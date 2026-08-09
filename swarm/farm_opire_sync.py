"""Opire + GitHub status sync — auto IDs from platform facts (no CEO typing)."""

from __future__ import annotations

from typing import Any

from swarm.farm_github_live import get_pull, parse_repo, post_issue_comment
from swarm.opire_farm import fetch_opire_rewards, _resolve_native_opire_id


def find_opire_reward(native_or_composite_id: str) -> dict[str, Any] | None:
    native = _resolve_native_opire_id(native_or_composite_id)
    try:
        rows = fetch_opire_rewards()
    except Exception:
        return None
    for row in rows:
        if str(row.get("id") or "") == native:
            return row
    return None


def build_platform_confirmation(
    *,
    opire_reward_id: str,
    pr_number: str | int | None,
    merge_sha: str | None,
    source: str,
) -> str:
    """Stable confirmation string derived from observed platform facts — not CEO input."""
    parts = [
        "virtus_auto",
        source,
        f"opire:{opire_reward_id}",
    ]
    if pr_number:
        parts.append(f"pr:{pr_number}")
    if merge_sha:
        parts.append(f"sha:{merge_sha[:12]}")
    return ":".join(parts)


def sync_task_from_platforms(task: dict[str, Any]) -> dict[str, Any]:
    """Update task fields from GitHub PR + Opire list. Never invents payout."""
    updates: dict[str, Any] = {"ok": True, "events": []}
    repo_full = str(task.get("repository") or "")
    parsed = parse_repo(repo_full)
    pr_id = task.get("pr_id") or task.get("pr_number")
    native = str(task.get("native_id") or _resolve_native_opire_id(str(task.get("id") or "")))

    # --- GitHub PR ---
    if parsed and pr_id:
        owner, repo = parsed
        pr = get_pull(owner, repo, pr_id)
        updates["github_pr"] = pr
        if pr.get("ok"):
            updates["events"].append("github_pr_ok")
            task["pr_url"] = pr.get("pr_url") or task.get("pr_url")
            task["pr_id"] = str(pr.get("pr_number") or pr_id)
            task["pr_number"] = pr.get("pr_number")
            if pr.get("merged"):
                task["merge_status"] = "merged"
                task["merge_sha"] = pr.get("merge_sha")
                task["status"] = "merged"
                updates["events"].append("merged")
            elif pr.get("state") == "open":
                task["merge_status"] = "open"
                if task.get("status") in ("pr_submitted", "draft_pr", "ceo_review"):
                    task["status"] = "maintainer_review"
                updates["events"].append("under_review")
            elif pr.get("state") == "closed" and not pr.get("merged"):
                task["merge_status"] = "closed"
                task["status"] = "rejected"
                updates["events"].append("pr_closed")

    # --- Opire reward presence ---
    raw = find_opire_reward(native)
    updates["opire_raw_found"] = bool(raw)
    if raw is None and task.get("merge_status") == "merged":
        # Reward disappeared from public available list after merge — strong payout signal
        updates["events"].append("opire_reward_left_public_list")
        task["reward_status"] = "payment_available"
        if task.get("status") == "merged":
            task["status"] = "payment_available"

    # --- Auto confirmation for REAL only when merge evidence exists ---
    if task.get("merge_status") == "merged" and task.get("merge_sha"):
        conf = build_platform_confirmation(
            opire_reward_id=native,
            pr_number=task.get("pr_id") or task.get("pr_number"),
            merge_sha=str(task.get("merge_sha")),
            source="github_merge+opire",
        )
        task["payment_confirmation_id"] = conf
        task["payment_confirmation_source"] = "auto_platform"
        updates["events"].append("auto_confirmation_ready")
        updates["payment_confirmation_id"] = conf
        # Promote to payout_confirmed only when CEO presses Withdraw/Confirm
        # or when status already payment_available / withdraw
        if task.get("status") in ("payment_available", "withdraw", "reward_approved"):
            updates["ready_for_real"] = True

    updates["task"] = task
    return updates


def maybe_post_try(task: dict[str, Any]) -> dict[str, Any]:
    """Post official /try on Issue once after Approve/Execute (idempotent flag)."""
    if task.get("try_comment_posted"):
        return {
            "ok": True,
            "skipped": True,
            "reason": "already_posted",
            "comment_status": "ALREADY_POSTED",
        }
    parsed = parse_repo(str(task.get("repository") or ""))
    issue_id = str(task.get("issue_id") or "")
    if not parsed or not issue_id:
        return {
            "ok": False,
            "error": "missing_issue_ref",
            "comment_status": "MISSING_REF",
        }
    owner, repo = parsed
    res = post_issue_comment(owner, repo, issue_id, "/try")
    if res.get("ok"):
        task["try_comment_posted"] = True
        task["try_comment_url"] = res.get("comment_url")
        task["try_comment_id"] = res.get("comment_id")
        task["comment_status"] = "POSTED"
    else:
        status = str(res.get("comment_status") or res.get("error") or "comment_failed")
        task["comment_status"] = status
        # Permission denied is honest — do not fake success; PR flow may still proceed
        if status == "PERMISSION_DENIED":
            task["try_comment_blocked"] = True
            res = {
                **res,
                "ok": False,
                "comment_status": "PERMISSION_DENIED",
                "message_ru": (
                    "GitHub PAT не может писать комментарий /try (403). "
                    "Draft PR flow продолжается отдельно; claim-комментарий — WAITING_OWNER_ACTION."
                ),
                "next_action": "WAITING_OWNER_ACTION",
            }
    return res
