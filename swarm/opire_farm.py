"""Opire Farm — Semi-Auto bounty scanner via official Opire public API + GitHub.

Official flow only (docs.opire.dev):
  /try on issue → implement → PR with /claim #N → maintainer merge → Opire payout

REAL income only after payout confirmation (Reward Protection).
Never auto-submit without CEO Approve + CEO Submit PR.
"""

from __future__ import annotations

import json
import os
import re
import threading
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from swarm.farm_execution_engine import FarmExecutionEngine, STAGES as EXECUTION_STAGES
from swarm.farm_execution_engine import merge_execution_into_task

OPIRE_REWARDS_URL = "https://api.opire.dev/rewards"
STATE_FILE = "opire_farm_state.json"


def _normalize_stale_external_task(task: dict[str, Any]) -> dict[str, Any]:
    """Dead-end without patch → skipped (never ask CEO to open Cursor)."""
    out = dict(task)
    if not _is_auto_dead_end(out) and not (
        str(out.get("status") or "") in ("draft_pr", "ceo_review", "needs_external")
        and not _task_has_patch(out)
        and str(
            ((out.get("execution") or {}).get("stages") or {})
            .get("implementation", {})
            .get("mode")
            or ""
        )
        == "needs_external"
    ):
        return out
    if _task_has_patch(out):
        return out
    # Only convert known external/manual handoff corpses
    st = str(out.get("status") or "")
    mode = str(
        ((out.get("execution") or {}).get("stages") or {})
        .get("implementation", {})
        .get("mode")
        or ""
    )
    if st not in ("needs_external", "draft_pr", "ceo_review") and mode != "needs_external":
        return out
    out["status"] = "skipped"
    out["reward_status"] = "skipped"
    out["ceo_note"] = out.get("ceo_note") or "auto_skip_not_auto_executable"
    out["skip_reason"] = "not_auto_executable"
    out["updated_at"] = _now()
    ex = dict(out.get("execution") or {})
    ex["stage"] = "skipped_auto"
    ex["patch_ready"] = False
    ex["ready_for_ceo"] = {
        "message_ru": (
            "Impossible в авто-режиме: патч не получен. "
            "Задача снята с конвейера — берём следующую bounty."
        ),
        "actions": [],
        "route": "skipped_auto",
        "patch_ready": False,
    }
    out["execution"] = ex
    return out

# Virtus-capable languages for Opire Confidence (clone/plan; codegen expands later)
# Keep aligned with swarm.farm_virtus_capabilities.VIRTUS_FARM_CAPABILITIES
SUPPORTED_LANGS = frozenset(
    {
        "python",
        "fastapi",
        "typescript",
        "javascript",
        "react",
        "nextjs",
        "next.js",
        "html",
        "css",
        "tailwind",
        "go",
        "php",
        "java",
        "rust",
        "ruby",
        "c",
        "c++",
        "csharp",
        "c#",
        "kotlin",
        "mdx",
        "markdown",
        "shell",
        "bash",
        "docker",
        "pytest",
    }
)

HARD_REJECT_TITLE = re.compile(
    r"captcha|hcaptcha|recaptcha|anti.?bot|multi.?account|tos.?bypass|"
    r"auto.?solve\s+h?captcha",
    re.I,
)

HARD_REJECT_BODY = re.compile(
    r"hcaptcha|recaptcha|solve\s+captcha|anti.?bot\s+bypass",
    re.I,
)

REWARD_STATES: tuple[str, ...] = (
    "available",
    "ceo_approved",
    "executing",
    "tests_passed",
    "draft_pr",
    "ceo_review",
    "pr_submitted",
    "maintainer_review",
    "changes_requested",
    "merged",
    "reward_approved",
    "payment_available",
    "withdraw",
    "payout_confirmed",
    "completed",
    "skipped",
)

# Only these may feed REAL Profit Ledger
REAL_INCOME_STATES = frozenset({"payout_confirmed", "completed"})

DEFAULT_CONFIDENCE_THRESHOLD = 72.0
MONEY_MODE_THRESHOLD = 80.0
MONEY_MODE_HARD_BLOCKERS = frozenset(
    {
        "high_competition",
        "large_feature_risk",
        "unsupported_language",
        "repo_unreachable",
        "missing_repo",
        "repo_auth_required",
        "reward_implies_large_scope",
        "forbidden_captcha_or_tos_evasion",
    }
)


def farm_proof_of_work(tasks: list[dict[str, Any]], funnel: dict[str, Any]) -> dict[str, Any]:
    """First Proof of Work — VERIFIED only after real payout_confirmed (not Estimated)."""
    analyzed = int(funnel.get("analyzed") or funnel.get("found") or 0)
    approved = int(funnel.get("ceo_approved") or 0)
    executed = int(funnel.get("executed") or 0)
    draft_pr = int(funnel.get("execution_ready_for_submit") or 0)
    # Count historical drafts too (status progressed past draft)
    draft_or_beyond = sum(
        1
        for t in tasks
        if t.get("status")
        in (
            "draft_pr",
            "ceo_review",
            "pr_submitted",
            "maintainer_review",
            "changes_requested",
            "merged",
            "reward_approved",
            "payment_available",
            "withdraw",
            "payout_confirmed",
            "completed",
        )
    )
    submitted = int(funnel.get("pr_submitted") or 0)
    merged = int(funnel.get("pr_merged") or 0)
    reward_confirmed = sum(
        1
        for t in tasks
        if t.get("status")
        in ("reward_approved", "payment_available", "withdraw", "payout_confirmed", "completed")
    )
    payout_confirmed = int(funnel.get("paid") or 0)
    real_usd = float(funnel.get("total_confirmed_usd") or 0)

    verified = payout_confirmed >= 1 and real_usd > 0
    return {
        "tasks_analysed": analyzed,
        "approved": approved,
        "executed": executed,
        "draft_pr": max(draft_pr, draft_or_beyond),
        "submitted": submitted,
        "merged": merged,
        "reward_confirmed": reward_confirmed,
        "payout_confirmed": payout_confirmed,
        "real_confirmed_usd": round(real_usd, 2),
        "proof_status": "VERIFIED" if verified else "PENDING_FIRST_REAL",
        "proof_mark": "✅ VERIFIED" if verified else "⏳ PENDING_FIRST_REAL",
        "criterion_ru": (
            "Proof = один полный цикл: Approve → Execution → Draft PR → Merge → "
            "REAL Ledger > 0. Estimated не считается."
        ),
        "message_ru": (
            "Farm Engine доказал работоспособность на реальном bounty."
            if verified
            else (
                "Полный цикл Opire → Draft PR → Merge → REAL ещё не подтверждён "
                "на реальном bounty. Победа не объявляется заранее."
            )
        ),
    }


def farm_readiness_matrix() -> dict[str, Any]:
    """Locked honest status — architecture vs proven end-to-end Opire cycle."""
    from swarm.farm_env_bootstrap import ensure_farm_env
    from swarm.farm_github_live import _github_token

    ensure_farm_env()
    gh_ready = bool(_github_token())
    return {
        "summary_ru": (
            "Execution Engine технически способен анализировать задачу, генерировать "
            "изменения, запускать тесты и готовить результат к публикации. "
            "Полный цикл Opire → Draft PR → Merge → REAL ещё не подтверждён "
            "на реальном bounty."
        ),
        "rows": [
            {"component": "Поиск задач Opire", "status": "confirmed", "mark": "✅"},
            {"component": "Анализ GitHub Issue", "status": "confirmed", "mark": "✅"},
            {
                "component": "Execution routing (local_engineer)",
                "status": "confirmed",
                "mark": "✅",
            },
            {"component": "Генерация патча", "status": "confirmed", "mark": "✅"},
            {"component": "Локальные тесты", "status": "confirmed", "mark": "✅"},
            {"component": "Commit", "status": "confirmed", "mark": "✅"},
            {"component": "Draft PR package", "status": "confirmed", "mark": "✅"},
            {
                "component": "Автоматический Push + Draft PR",
                "status": "needs_token_and_live_check" if not gh_ready else "ready_for_live_check",
                "mark": "🟡",
                "detail_ru": (
                    "GITHUB_TOKEN задан — нужна проверка на реальной bounty."
                    if gh_ready
                    else "Требует GITHUB_TOKEN в .env.local и проверки на реальной bounty."
                ),
            },
            {
                "component": "Merge в чужой репозиторий",
                "status": "unproven",
                "mark": "⏳",
            },
            {
                "component": "Подтверждение REAL через платформу",
                "status": "unproven",
                "mark": "⏳",
            },
            {
                "component": "Получение реального вознаграждения",
                "status": "unproven",
                "mark": "⏳",
            },
        ],
        "next_proof_ru": (
            "Один полный цикл: Approve → Execution → Draft PR (auto) → Merge → "
            "Синхронизировать → REAL (auto). Без ручных ID."
        ),
        "github_token_ready": gh_ready,
    }


def _bottleneck_hint(
    found: int,
    high: int,
    approved: int,
    executed: int,
    pr_submitted: int,
    pr_merged: int,
    paid: int,
) -> str:
    if found == 0:
        return "Узкое место: Scanner не видит bounty (сеть / API)."
    if high == 0:
        return "Узкое место: Confidence — мало задач с высоким шансом."
    if approved == 0:
        return "Узкое место: CEO Approve — кандидаты есть, одобрений нет."
    if executed < approved:
        return "Узкое место: Execution Engine — одобрено, выполнение ещё не доведена."
    if pr_submitted < executed:
        return "Узкое место: Draft→Submit PR (нужен CEO Submit)."
    if pr_merged < pr_submitted:
        return "Узкое место: Maintainer review / принятие PR."
    if paid < pr_merged:
        return "Узкое место: Opire payout / вывод после merge."
    return "Воронка живая — смотрите Confirmed $."


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _price_usd(raw: dict[str, Any]) -> float:
    pp = raw.get("pendingPrice") or {}
    cents = float(pp.get("value") or 0)
    unit = str(pp.get("unit") or "USD_CENT").upper()
    if unit == "USD_CENT":
        return round(cents / 100.0, 2)
    return round(cents, 2)


def _issue_meta(url: str) -> dict[str, str]:
    m = re.search(r"github\.com/([^/]+)/([^/]+)/issues/(\d+)", url or "", re.I)
    if not m:
        return {"owner": "", "repo": "", "issue_id": "", "repo_full": ""}
    owner, repo, issue = m.group(1), m.group(2), m.group(3)
    return {
        "owner": owner,
        "repo": repo,
        "issue_id": issue,
        "repo_full": f"{owner}/{repo}",
    }


def fetch_opire_rewards(*, timeout: float = 25.0, max_pages: int = 10) -> list[dict[str, Any]]:
    """Fetch public Opire rewards (paginate until empty page).

    Official list is finite (~50 on public API) — not the whole GitHub market.
    """
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for page in range(1, max_pages + 1):
        url = OPIRE_REWARDS_URL if page == 1 else f"{OPIRE_REWARDS_URL}?page={page}"
        req = urllib.request.Request(
            url,
            headers={"Accept": "application/json", "User-Agent": "VirtusCore-FarmEngine/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        if not isinstance(data, list) or not data:
            break
        added = 0
        for row in data:
            if not isinstance(row, dict):
                continue
            rid = str(row.get("id") or "")
            if rid and rid in seen:
                continue
            if rid:
                seen.add(rid)
            out.append(row)
            added += 1
        # Empty page or no new ids → stop
        if added == 0:
            break
    return out


def score_reward(
    raw: dict[str, Any],
    *,
    issue_intel: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Confidence Engine — heuristic only (no auto-execution)."""
    from swarm.opire_issue_intel import analyze_issue_text, build_ceo_action_links

    title = str(raw.get("title") or "")
    langs = [str(x).lower() for x in (raw.get("programmingLanguages") or []) if x]
    claimers = list(raw.get("claimerUsers") or [])
    trying = list(raw.get("tryingUsers") or [])
    project = raw.get("project") or {}
    bot = bool(project.get("isBotInstalled"))
    public = project.get("isPublic") is not False
    reward = _price_usd(raw)
    url = str(raw.get("url") or "")
    meta = _issue_meta(url)

    body = ""
    if issue_intel and issue_intel.get("ok"):
        body = str(issue_intel.get("body") or "")
        if issue_intel.get("title") and not title:
            title = str(issue_intel.get("title") or title)
    text_analysis = analyze_issue_text(title, body)

    blockers: list[str] = list(text_analysis.get("blockers") or [])
    if HARD_REJECT_TITLE.search(title):
        blockers.append("forbidden_captcha_or_tos_evasion")
    if body and HARD_REJECT_BODY.search(body):
        blockers.append("forbidden_captcha_or_tos_evasion")
    if not public:
        blockers.append("repo_not_public")
    if langs and not (SUPPORTED_LANGS & set(langs)):
        blockers.append("unsupported_language")
    if reward <= 0:
        blockers.append("no_reward")

    # Base scores
    conf = 55.0
    acceptance = 55.0

    supported_hit = sorted(SUPPORTED_LANGS & set(langs))
    if supported_hit:
        conf += 18
        acceptance += 10
        if "python" in supported_hit or "typescript" in supported_hit or "javascript" in supported_hit:
            conf += 6
    elif not langs:
        conf -= 8  # unknown stack
        acceptance -= 5

    if bot:
        conf += 6
        acceptance += 8

    n_comp = max(len(claimers), len(trying))
    if n_comp == 0:
        conf += 14
        acceptance += 12
    elif n_comp <= 2:
        conf += 6
        acceptance += 4
    elif n_comp <= 5:
        conf -= 4
        acceptance -= 8
    else:
        conf -= 14
        acceptance -= 18
        blockers.append("high_competition")

    # Reward vs complexity heuristic
    if 20 <= reward <= 400:
        conf += 8
        est_hours = max(0.5, min(6.0, reward / 80.0))
    elif reward < 20:
        conf += 2
        est_hours = 0.75
    elif reward <= 1500:
        conf -= 6
        est_hours = min(24.0, reward / 60.0)
    else:
        conf -= 20
        est_hours = 40.0
        blockers.append("reward_implies_large_scope")

    signals = set(text_analysis.get("signals") or [])
    low = title.lower()
    if "bugfix" in signals or re.search(r"\bfix\b|bug|race|pagination|leak|stale|error|typo", low):
        conf += 8
        acceptance += 6
        est_hours *= 0.85
    if "large_feature" in signals or re.search(
        r"rewrite|migrate|wayland|rcs support|web platform export", low
    ):
        conf -= 18
        acceptance -= 12
        est_hours *= 1.8
        blockers.append("large_feature_risk")
    if "detailed_description" in signals or "has_acceptance_criteria" in signals:
        conf += 5
        acceptance += 4
    if "thin_description" in signals:
        conf -= 6
        acceptance -= 4
    if "crypto_chain_params" in signals and not (
        SUPPORTED_LANGS & set(langs) & {"c", "c++", "python"}
    ):
        conf -= 10

    conf = max(5.0, min(97.0, round(conf, 1)))
    acceptance = max(5.0, min(95.0, round(acceptance, 1)))
    overall = round(0.55 * conf + 0.45 * acceptance, 1)

    # Deduplicate blockers
    blockers = sorted(set(blockers))

    if blockers:
        recommendation = "SKIP"
    elif overall >= DEFAULT_CONFIDENCE_THRESHOLD:
        recommendation = "TAKE"
    elif overall >= 55.0:
        recommendation = "REVIEW"
    else:
        recommendation = "SKIP"

    difficulty = (
        "low" if overall >= 85 and est_hours <= 2 else (
            "medium" if overall >= 70 else "high"
        )
    )

    from swarm.farm_roi_score import compute_roi
    from swarm.farm_virtus_capabilities import detect_task_type, task_type_auto_ok

    scored_base = {
        "reward_usd": reward,
        "estimated_hours": round(est_hours, 1),
        "overall_confidence_pct": overall,
    }
    roi = compute_roi(scored_base)
    task_type = detect_task_type(title, langs)
    cap = task_type_auto_ok(task_type)
    if cap.get("severity") == "❌":
        blockers.append("capability_forbidden")
        recommendation = "SKIP"
    elif cap.get("severity") == "⚠️" and recommendation == "TAKE":
        recommendation = "REVIEW"

    return {
        "id": str(raw.get("id") or ""),
        "title": title,
        "url": url,
        "platform": "opire",
        "repository": meta["repo_full"],
        "issue_id": meta["issue_id"],
        "issue_url": url,
        "languages": langs,
        "supported_languages": supported_hit,
        "task_type": task_type,
        "capability_auto": cap.get("severity"),
        "reward_usd": reward,
        "reward_currency": "USD",
        "estimated_reward_usd": reward,  # never REAL
        "bot_installed": bot,
        "competitors": n_comp,
        "team_available": bool(raw.get("isTeamAvailable") or project.get("isTeamAvailable")),
        "confidence_pct": conf,
        "acceptance_pct": acceptance,
        "overall_confidence_pct": overall,
        "estimated_hours": round(est_hours, 1),
        **roi,
        "estimated_cost_note_ru": "Внутреннее время Virtus; не путать с reward USD.",
        "difficulty": difficulty,
        "required_capabilities": supported_hit or ["manual_review"],
        "tests_available": (
            "likely" if "tests_mentioned" in signals else "unknown"
        ),
        "risk": "low" if overall >= 85 else ("medium" if overall >= 70 else "high"),
        "recommendation": recommendation,
        "blockers": blockers,
        "success_probability_pct": overall,
        "acceptance_probability_pct": acceptance,
        "issue_analysis": text_analysis,
        "issue_body_preview": (body[:600] if body else ""),
        "ceo_action_links": build_ceo_action_links(
            issue_url=url,
            repo_full=meta["repo_full"],
            issue_id=meta["issue_id"],
        ),
        "official_next_steps_ru": [
            "CEO Approve в Mission Control",
            "Официальный /try комментарием на Issue (GitHub)",
            "Execution Engine: clone → plan → code → tests → Draft PR",
            "CEO Submit PR с /claim #<issue>",
            "Monitor review → payout → REAL только после confirmation",
        ],
    }


def scan_opire(
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    limit: int = 40,
    fetch_fn=None,
    enrich_top: int = 8,
    sniper_top: int = 8,
    exclude_ids: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Scan Opire via Connector Manager (primary connector).

    fetch_fn — test seam.
    enrich_top — read GitHub Issue bodies for top TAKE candidates.
    sniper_top — target count of sniper-verified TAKE (backfills past dead repos).
    exclude_ids — already approved/skipped task ids (do not re-offer).
    """
    from swarm.farm_connectors.manager import ConnectorManager
    from swarm.farm_connectors.opire_connector import OpireConnector
    from swarm.opire_issue_intel import (
        analyze_issue_text,
        apply_sniper_to_candidate,
        fetch_issue_from_url,
    )

    if fetch_fn is not None:
        mgr = ConnectorManager(connectors=[OpireConnector(fetch_fn=fetch_fn)])
    else:
        # Opire-first: live Opire + catalog stubs (Polar/… planned, not scanned)
        mgr = ConnectorManager()
    # Pull a wider pool so Sniper can backfill after skipping dead repos
    pool_limit = max(limit * 3, 60)
    out = mgr.scan(threshold=threshold, limit=pool_limit)
    out.setdefault("source", "opire_primary")
    out["primary_connector"] = "opire"

    if fetch_fn is not None:
        return out

    excluded = {str(x) for x in (exclude_ids or set()) if x}
    sniper_target = max(0, int(sniper_top))
    enrich_n = max(0, int(enrich_top))
    raw_cands = list(out.get("candidates") or [])

    # Drop already-active / skipped before probing (CEO needs NEW options)
    def _is_excluded(row: dict[str, Any]) -> bool:
        rid = str(row.get("id") or "")
        native = str(row.get("native_id") or "")
        return bool(
            (rid and rid in excluded)
            or (native and native in excluded)
            or (native and f"opire:{native}" in excluded)
            or (rid and rid in excluded)
        )

    fresh = [c for c in raw_cands if not _is_excluded(c)]
    excluded_n = len(raw_cands) - len(fresh)

    take_verified: list[dict[str, Any]] = []
    sniper_skipped = 0
    sniper_probed = 0
    enrich_done = 0

    for cand in fresh:
        if len(take_verified) >= limit:
            break
        row = dict(cand)
        # Keep probing until we fill sniper_target TAKE (backfill past 404s)
        need_sniper = sniper_target <= 0 or sniper_probed < max(
            sniper_target * 4, sniper_target + sniper_skipped + 8
        )
        if sniper_target > 0 and need_sniper and len(take_verified) < sniper_target:
            row = apply_sniper_to_candidate(row, timeout=8.0)
            sniper_probed += 1
            hard_skip = row.get("recommendation") == "SKIP" and any(
                b in (row.get("blockers") or [])
                for b in (
                    "repo_unreachable",
                    "repo_auth_required",
                    "missing_repo",
                )
            )
            if hard_skip:
                sniper_skipped += 1
                continue
        elif sniper_target > 0 and len(take_verified) >= sniper_target:
            # Already have enough verified; still allow more TAKE without probe
            pass

        if enrich_done < enrich_n:
            intel = fetch_issue_from_url(str(row.get("url") or ""), timeout=10.0)
            enrich_done += 1
            if intel.get("ok"):
                analysis = analyze_issue_text(
                    str(row.get("title") or ""),
                    str(intel.get("body") or ""),
                )
                row["issue_analysis"] = analysis
                row["issue_body_preview"] = (intel.get("body") or "")[:800]
                if analysis.get("blockers"):
                    row["blockers"] = sorted(
                        set(list(row.get("blockers") or []) + list(analysis["blockers"]))
                    )
                    row["recommendation"] = "SKIP"
                    sniper_skipped += 1
                    continue
            elif str(intel.get("error") or "").startswith("http_404"):
                row["blockers"] = sorted(
                    set(list(row.get("blockers") or []) + ["repo_unreachable"])
                )
                row["recommendation"] = "SKIP"
                row["repo_status"] = "unreachable"
                sniper_skipped += 1
                continue

        if row.get("recommendation") == "TAKE" or (
            float(row.get("overall_confidence_pct") or 0) >= threshold
            and not any(
                b in (row.get("blockers") or [])
                for b in (
                    "repo_unreachable",
                    "repo_auth_required",
                    "missing_repo",
                )
            )
        ):
            if row.get("recommendation") != "SKIP":
                row["recommendation"] = "TAKE"
                take_verified.append(row)

    out["candidates"] = take_verified[:limit]
    out["enriched_issue_bodies"] = enrich_done
    out["sniper_skipped"] = sniper_skipped
    out["sniper_probed"] = sniper_probed
    out["excluded_already_active"] = excluded_n
    out["pool_before_sniper"] = len(fresh)
    # Preserve Review All from connector manager (full pool with reject reasons)
    out.setdefault("review_all", out.get("all_preview") or [])
    out.setdefault("confidence_bands", {})
    if not out.get("analytics"):
        from swarm.farm_scan_analytics import build_scan_analytics

        out["analytics"] = build_scan_analytics(
            list(out.get("review_all") or []),
            threshold=threshold,
            supported_langs=SUPPORTED_LANGS,
        )
    return out


def _resolve_native_opire_id(reward_id: str) -> str:
    from swarm.farm_connectors.manager import parse_opportunity_id

    platform, native = parse_opportunity_id(reward_id)
    if platform in (None, "opire"):
        return native
    return reward_id


def _cand_matches(cand: dict[str, Any], reward_id: str) -> bool:
    if not reward_id:
        return False
    if cand.get("id") == reward_id:
        return True
    if cand.get("native_id") == reward_id:
        return True
    native = _resolve_native_opire_id(reward_id)
    return cand.get("native_id") == native or cand.get("id") == f"opire:{native}"


# Skip and completed hide forever. needs_external without patch is healed → skipped.
_EXCLUDE_FROM_SCAN_STATUSES = frozenset(
    {
        "skipped",
        "needs_external",  # dead-end until healed/skipped — never re-offer as TAKE
        "ceo_approved",
        "executing",
        "tests_passed",
        "draft_pr",
        "ceo_review",
        "pr_submitted",
        "maintainer_review",
        "changes_requested",
        "merged",
        "reward_approved",
        "payment_available",
        "withdraw",
        "payout_confirmed",
        "completed",
    }
)

# How many auto-advance hops after Impossible (Approve+Run next TAKE)
_MAX_AUTO_ADVANCE = 5


def _farm_auto_advance_enabled() -> bool:
    flag = (os.environ.get("FARM_AUTO_ADVANCE") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def _farm_auto_execute_on_approve() -> bool:
    """CEO path: Approve must start Execution Engine automatically (default ON)."""
    flag = (os.environ.get("FARM_AUTO_EXECUTE_ON_APPROVE") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def _farm_decide_async_execute() -> bool:
    """Approve returns instantly; Execution runs in background (default ON).

    Sync under pytest so unit tests can assert task status after decide().
    Force sync with FARM_DECIDE_ASYNC_EXECUTE=0.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    flag = (os.environ.get("FARM_DECIDE_ASYNC_EXECUTE") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def build_success_checklist(cand: dict[str, Any]) -> list[dict[str, Any]]:
    """Overall Success Probability factors for Money Mode."""
    blockers = {str(b) for b in (cand.get("blockers") or [])}
    reasons = {str(r) for r in (cand.get("reject_reasons") or [])}
    langs = [str(x).lower() for x in (cand.get("supported_languages") or cand.get("languages") or [])]
    conf = float(cand.get("overall_confidence_pct") or cand.get("success_probability_pct") or 0)
    hours = float(cand.get("estimated_hours") or 99)
    comps = int(cand.get("competitors") or 0)
    repo_ok = str(cand.get("repo_status") or "") in ("", "ok", "unknown")
    tests = str(cand.get("tests_available") or "")
    roi = str(cand.get("roi_label") or "")
    items = [
        {
            "id": "repo_alive",
            "label": "Repository alive",
            "ok": repo_ok and "repo_unreachable" not in blockers and "missing_repo" not in blockers,
        },
        {
            "id": "language",
            "label": "Language supported",
            "ok": bool(langs) and "unsupported_language" not in blockers,
        },
        {
            "id": "tests",
            "label": "Tests available",
            "ok": tests in ("likely", "yes", "true") or "tests_mentioned" in (
                (cand.get("issue_analysis") or {}).get("signals") or []
            ),
        },
        {
            "id": "small_scope",
            "label": "Small scope",
            "ok": (
                hours <= 4
                and "large_feature_risk" not in blockers
                and "reward_implies_large_scope" not in blockers
            ),
        },
        {
            "id": "low_competition",
            "label": "Low competition",
            "ok": comps <= 2 and "high_competition" not in blockers,
        },
        {
            "id": "capability",
            "label": "High capability match",
            "ok": conf >= MONEY_MODE_THRESHOLD and "capability_missing" not in reasons,
        },
        {
            "id": "roi",
            "label": "Good ROI",
            "ok": roi in ("A", "B", "excellent", "good", "A+", "★★★★", "★★★★★")
            or float(cand.get("roi_usd_per_hour") or 0) >= 25
            or conf >= 85,
        },
    ]
    return items


def is_money_mode_candidate(cand: dict[str, Any]) -> bool:
    """Conservative filter: only bounty with real shot at Draft PR → Merge."""
    conf = float(
        cand.get("overall_confidence_pct")
        or cand.get("success_probability_pct")
        or 0
    )
    if conf < MONEY_MODE_THRESHOLD:
        return False
    blockers = {str(b) for b in (cand.get("blockers") or [])}
    if blockers & MONEY_MODE_HARD_BLOCKERS:
        return False
    if blockers:
        return False
    reasons = {str(r) for r in (cand.get("reject_reasons") or [])}
    if "review_band" in reasons or str(cand.get("recommendation") or "") == "REVIEW":
        return False
    if str(cand.get("recommendation") or "") == "SKIP":
        return False
    repo = str(cand.get("repo_status") or "")
    if repo in ("unreachable", "auth_required"):
        return False
    hours = float(cand.get("estimated_hours") or 0)
    if hours > 6:
        return False
    checklist = build_success_checklist(cand)
    ok_n = sum(1 for i in checklist if i.get("ok"))
    # Require most factors; tests can be unknown
    return ok_n >= 5 and conf >= MONEY_MODE_THRESHOLD


def apply_money_mode_to_scan(scan: dict[str, Any]) -> dict[str, Any]:
    """Split TAKE pool into Money Mode (default Approve list) vs rest."""
    from swarm.farm_preflight import run_preflight

    out = dict(scan)
    take = list(out.get("candidates") or [])
    money: list[dict[str, Any]] = []
    for row in take:
        c = dict(row)
        c["success_checklist"] = build_success_checklist(c)
        c["overall_success_probability_pct"] = float(
            c.get("overall_confidence_pct") or c.get("success_probability_pct") or 0
        )
        pf = run_preflight(c, deep=False, min_confidence=MONEY_MODE_THRESHOLD)
        c["preflight"] = pf
        eligible = is_money_mode_candidate(c) and pf.get("verdict") != "SKIP"
        c["money_mode_eligible"] = eligible
        if eligible:
            money.append(c)
    money.sort(
        key=lambda x: (
            0 if (x.get("preflight") or {}).get("verdict") == "GO" else 1,
            -float(x.get("overall_confidence_pct") or 0),
        )
    )
    go_list = [c for c in money if (c.get("preflight") or {}).get("verdict") == "GO"]
    out["candidates_take_all"] = take
    out["candidates"] = go_list if go_list else money[:8]
    out["threshold"] = MONEY_MODE_THRESHOLD
    out["money_mode"] = {
        "enabled_default": True,
        "threshold": MONEY_MODE_THRESHOLD,
        "count": len(out["candidates"]),
        "hidden_count": max(0, len(take) - len(out["candidates"])),
        "go_count": len(go_list),
        "note_ru": (
            "Money Mode + Pre-flight: только GO (Confidence ≥80%, repo alive, "
            "capability OK). SKIP скрыт. REVIEW — вручную через All TAKE."
        ),
    }
    return out


def _task_has_patch(task: dict[str, Any]) -> bool:
    ex = task.get("execution") or {}
    impl = (ex.get("stages") or {}).get("implementation") or {}
    return bool(ex.get("patch_ready") or (impl.get("files_touched") or []))


def _is_auto_dead_end(task: dict[str, Any]) -> bool:
    """True when Engine cannot finish without a human — must Skip, not Cursor."""
    st = str(task.get("status") or "")
    ex = task.get("execution") or {}
    impl = (ex.get("stages") or {}).get("implementation") or {}
    mode = str(impl.get("mode") or "")
    route = str(
        (ex.get("ready_for_ceo") or {}).get("route")
        or ((ex.get("stages") or {}).get("routing") or {}).get("route")
        or mode
    )
    if _task_has_patch(task):
        return False
    if st == "needs_external":
        return True
    if st == "draft_pr" and (mode == "needs_external" or route == "needs_external"):
        return True
    if ex.get("stage") == "awaiting_external":
        return True
    if st == "ceo_approved" and task.get("execution_error"):
        return True
    return False


class OpireFarmEngine:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._memory.mkdir(parents=True, exist_ok=True)
        self._path = self._memory / STATE_FILE

    def _bounty_ledger(self):
        from swarm.farm_bounty_ledger import FarmBountyLearningLedger

        return FarmBountyLearningLedger(self._memory)

    def _record_bounty_outcome(self, task: dict[str, Any], *, outcome: str) -> None:
        try:
            self._bounty_ledger().append_from_task(task, outcome=outcome)
        except Exception:  # noqa: BLE001
            pass

    def _load(self) -> dict[str, Any]:
        if not self._path.exists():
            return {"tasks": {}, "updated_at": None}
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except Exception:
            return {"tasks": {}, "updated_at": None}

    def _save(self, state: dict[str, Any]) -> None:
        state["updated_at"] = _now()
        self._path.write_text(
            json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def panel(
        self, *, force_scan: bool = True, enrich_top: int = 0
    ) -> dict[str, Any]:
        state = self._load()
        tasks_map = state.get("tasks") or {}
        exclude: set[str] = set()
        for tid, t in tasks_map.items():
            st = str(t.get("status") or "")
            # Skip / in-progress / completed — never re-offer as TAKE
            if st not in _EXCLUDE_FROM_SCAN_STATUSES:
                continue
            exclude.add(str(tid))
            native = str(t.get("native_id") or "")
            if native:
                exclude.add(native)
                exclude.add(f"opire:{native}")
        # Also honor permanent skip registry
        for sid in state.get("skipped_forever") or []:
            exclude.add(str(sid))
        scan = (
            scan_opire(
                enrich_top=enrich_top,
                sniper_top=12,
                exclude_ids=exclude,
                # Pool for Money Mode filter (full TAKE band). Money Mode keeps ≥80%.
                threshold=max(55.0, DEFAULT_CONFIDENCE_THRESHOLD - 12.0),
            )
            if force_scan
            else {
                "ok": True,
                "candidates": [],
                "scanned": 0,
                "filtered_out": 0,
                "threshold": MONEY_MODE_THRESHOLD,
                "review_all": [],
                "confidence_bands": {},
            }
        )
        if force_scan:
            scan = apply_money_mode_to_scan(scan)
        tasks = [_normalize_stale_external_task(t) for t in tasks_map.values()]
        # Persist healed statuses so Retry button / Timeline stay consistent
        healed = False
        for t in tasks:
            tid = str(t.get("id") or "")
            if not tid:
                continue
            prev = tasks_map.get(tid) or {}
            if str(prev.get("status")) != str(t.get("status")) or (
                (prev.get("execution") or {}).get("stage")
                != (t.get("execution") or {}).get("stage")
            ):
                tasks_map[tid] = t
                healed = True
                if str(t.get("status")) == "skipped":
                    self._register_skipped_forever(state, t)
        if healed:
            state["tasks"] = tasks_map
            self._save(state)
        tasks.sort(key=lambda t: str(t.get("updated_at") or ""), reverse=True)

        estimated = sum(float(t.get("estimated_reward_usd") or 0) for t in tasks if t.get("status") not in REAL_INCOME_STATES and t.get("status") != "skipped")
        real = sum(
            float(t.get("payout_confirmed_usd") or 0)
            for t in tasks
            if t.get("status") in REAL_INCOME_STATES
        )

        approved = sum(1 for t in tasks if t.get("status") not in ("skipped", None) and t.get("status") != "available")
        executed = sum(
            1
            for t in tasks
            if t.get("status")
            in (
                "executing",
                "tests_passed",
                "draft_pr",
                "ceo_review",
                "pr_submitted",
                "maintainer_review",
                "changes_requested",
                "merged",
                "reward_approved",
                "payment_available",
                "withdraw",
                "payout_confirmed",
                "completed",
            )
        )
        pr_submitted = sum(
            1
            for t in tasks
            if t.get("status")
            in (
                "pr_submitted",
                "maintainer_review",
                "changes_requested",
                "merged",
                "reward_approved",
                "payment_available",
                "withdraw",
                "payout_confirmed",
                "completed",
            )
        )
        pr_merged = sum(
            1
            for t in tasks
            if t.get("status")
            in (
                "merged",
                "reward_approved",
                "payment_available",
                "withdraw",
                "payout_confirmed",
                "completed",
            )
        )
        paid = sum(1 for t in tasks if t.get("status") in REAL_INCOME_STATES)

        scanned = int(scan.get("scanned") or 0)
        high = len(scan.get("candidates") or [])

        funnel = {
            "found": scanned,
            "analyzed": scanned,
            "high_confidence": high,
            "review_all_count": len(scan.get("review_all") or []),
            "confidence_bands": scan.get("confidence_bands") or {},
            "analytics": scan.get("analytics") or {},
            "ceo_approved": approved,
            "executed": executed,
            "execution_ready_for_submit": sum(
                1 for t in tasks if t.get("status") == "draft_pr"
            ),
            "execution_failed": sum(
                1
                for t in tasks
                if (t.get("execution") or {}).get("stage") == "failed"
            ),
            "pr_submitted": pr_submitted,
            "pr_merged_first_pass": sum(
                1
                for t in tasks
                if t.get("status")
                in (
                    "merged",
                    "reward_approved",
                    "payment_available",
                    "withdraw",
                    "payout_confirmed",
                    "completed",
                )
                and t.get("had_changes_requested") is not True
            ),
            "pr_changes_requested": sum(
                1 for t in tasks if t.get("status") == "changes_requested"
            ),
            "pr_merged": pr_merged,
            "paid": paid,
            "total_confirmed_usd": round(real, 2),
            "bottleneck_hint_ru": _bottleneck_hint(
                scanned, high, approved, executed, pr_submitted, pr_merged, paid
            ),
        }

        elapsed_vals: list[float] = []
        for t in tasks:
            ex = t.get("execution") if isinstance(t.get("execution"), dict) else {}
            raw = ex.get("elapsed_sec")
            try:
                sec = float(raw)
            except (TypeError, ValueError):
                continue
            if sec > 0:
                elapsed_vals.append(sec)
        avg_exec_s = (
            round(sum(elapsed_vals) / len(elapsed_vals), 1) if elapsed_vals else None
        )

        from swarm.farm_pipeline_state import attach_pipeline_state, count_execution_success

        exec_stats = count_execution_success(tasks)
        tasks = exec_stats.pop("tasks")
        # Keep funnel.executed aligned with pipeline Started
        funnel["executed"] = int(exec_stats["started"])
        funnel["execution_in_flight"] = int(exec_stats["execution"])
        funnel["pipeline_draft_pr"] = int(exec_stats["draft_pr"])

        execution_success = {
            **exec_stats,
            "avg_execution_s": avg_exec_s,
            "avg_execution_samples": len(elapsed_vals),
            "note_ru": exec_stats.get("note_ru")
            or (
                "Один pipeline_state. Started ≈ Approved после auto-execute."
            ),
        }
        # legacy aliases used by UI
        execution_success["approved"] = approved
        if execution_success["approved"] and execution_success["started"] is not None:
            execution_success["start_rate"] = round(
                execution_success["started"] / execution_success["approved"], 3
            )
            execution_success["complete_rate"] = round(
                execution_success["completed"] / execution_success["approved"], 3
            )

        return {
            "ok": True,
            "mode": "opire_primary",
            "engine": "farm_engine",
            "separate_from": "commercial_engine",
            "north_star_ru": (
                "Opire — первый полноценный коннектор. Mission Control = центр управления. "
                "Сайт Opire не нужен для поиска и решений — только официальный GitHub flow "
                "(/try, PR /claim) когда платформа требует действие владельца."
            ),
            "market_note_ru": (
                f"Публичный api.opire.dev сейчас отдаёт ~{int(scan.get('scanned') or 0)} "
                "открытых reward (не миллионы GitHub issues). "
                "Skip снимает bounty с Active навсегда (не предлагается снова). "
                "Если Engine не может закрыть задачу сам — Impossible → Skip → следующая. "
                "CEO не открывает Cursor. "
                "Блок «Live Connector / Confirmed €» на Maturity — про Stripe Micro / "
                "чужой Earn-рынок, это не Opire Scanner."
            ),
            "readiness": farm_readiness_matrix(),
            "proof": farm_proof_of_work(tasks, funnel),
            "execution_success": execution_success,
            "payout_success": {
                "found": int(scan.get("scanned") or 0),
                **(execution_success.get("payout_success") or {}),
                "approved": approved,
                "executed": int(execution_success.get("started") or 0),
                "draft_pr": int(execution_success.get("draft_pr") or 0),
                "merged": int(execution_success.get("merged") or 0),
                "paid": int(execution_success.get("paid") or 0),
            },
            "capability_matrix": __import__(
                "swarm.farm_virtus_capabilities", fromlist=["capability_snapshot"]
            ).capability_snapshot(),
            "income_contours": {
                "title_ru": "Три независимых контура дохода",
                "note_ru": (
                    "Не смешивать: Opire исполняет bounty; Alpha Hunter ищет рынки; "
                    "Sales Farm продаёт Virtus сайты. Все сходятся в REAL Ledger."
                ),
                "farms": [
                    {
                        "id": "opire_farm",
                        "label": "Opire Farm",
                        "role_ru": "Исполняет работу (bounty → Draft PR → Payout)",
                        "href": "/farm-engine",
                        "primary_kpi": "Paid / Merged",
                    },
                    {
                        "id": "alpha_hunter",
                        "label": "Alpha Hunter",
                        "role_ru": "Ищет новые рынки и площадки",
                        "href": "/alpha-hunter",
                        "primary_kpi": "New sources / ROI paper",
                    },
                    {
                        "id": "sales_farm",
                        "label": "Sales Farm",
                        "role_ru": "Country Desk → клиент → Stripe → Factory",
                        "href": "/acquisition",
                        "primary_kpi": "First Real Euro / Customers",
                    },
                ],
            },
            "workflow_ru": [
                "Opire Scanner",
                "CEO Approve",
                "Execution Engine (Research/Codex авто)",
                "Draft PR Ready → CEO Submit",
                "или Impossible → Skip → следующая bounty",
            ],
            "execution_stages": list(EXECUTION_STAGES),
            "pipeline_states": [
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
            ],
            "connectors": scan.get("catalog") or scan.get("connectors") or [],
            "funnel": funnel,
            "scan": scan,
            "active_tasks": [
                attach_pipeline_state(t)
                for t in tasks
                if t.get("status") not in ("completed", "skipped")
            ],
            "history": [attach_pipeline_state(t) for t in tasks[:30]],
            "ledger": {
                "estimated_usd": round(estimated, 2),
                "real_confirmed_usd": round(real, 2),
                "note_ru": "Estimated и REAL всегда разделены. REAL = только payout_confirmed.",
            },
            "learning_ledger": self._bounty_ledger().summary(),
            "reward_states": list(REWARD_STATES),
        }

    def _register_skipped_forever(self, state: dict[str, Any], task: dict[str, Any]) -> None:
        forever = state.setdefault("skipped_forever", [])
        for key in (
            str(task.get("id") or ""),
            str(task.get("native_id") or ""),
            f"opire:{task.get('native_id')}" if task.get("native_id") else "",
        ):
            if key and key not in forever:
                forever.append(key)

    def _mark_task_skipped(
        self,
        task: dict[str, Any],
        *,
        note: str,
        reason: str = "skipped",
    ) -> dict[str, Any]:
        out = dict(task)
        out["status"] = "skipped"
        out["reward_status"] = "skipped"
        out["ceo_note"] = note
        out["skip_reason"] = reason
        out["updated_at"] = _now()
        out["execution_error"] = None
        ex = dict(out.get("execution") or {})
        ex["stage"] = "skipped_auto" if reason.startswith("not_auto") else "skipped"
        ex["patch_ready"] = False
        out["execution"] = ex
        return out

    def _pick_next_take_id(self, *, exclude_extra: set[str] | None = None) -> str | None:
        state = self._load()
        exclude: set[str] = set(exclude_extra or ())
        for tid, t in (state.get("tasks") or {}).items():
            if str(t.get("status") or "") in _EXCLUDE_FROM_SCAN_STATUSES:
                exclude.add(str(tid))
                native = str(t.get("native_id") or "")
                if native:
                    exclude.add(native)
                    exclude.add(f"opire:{native}")
        for sid in state.get("skipped_forever") or []:
            exclude.add(str(sid))
        scan = scan_opire(
            limit=30,
            enrich_top=0,
            sniper_top=8,
            exclude_ids=exclude,
            threshold=max(55.0, DEFAULT_CONFIDENCE_THRESHOLD - 12.0),
        )
        for cand in scan.get("candidates") or []:
            rid = str(cand.get("id") or "")
            if not rid:
                continue
            if cand.get("recommendation") == "SKIP":
                continue
            if any(
                b in (cand.get("blockers") or [])
                for b in ("repo_unreachable", "repo_auth_required", "missing_repo")
            ):
                continue
            return rid
        return None

    def _auto_advance_to_next(self, *, depth: int) -> dict[str, Any] | None:
        """Approve + Run next TAKE. Returns nested start_execution result or None."""
        if not _farm_auto_advance_enabled() or depth >= _MAX_AUTO_ADVANCE:
            return None
        nxt = self._pick_next_take_id()
        if not nxt:
            return {
                "ok": False,
                "error": "no_next_bounty",
                "message_ru": (
                    "Авто-конвейер: подходящих TAKE больше нет в Scanner. "
                    "Обновите панель позже."
                ),
            }
        decided = self.decide(nxt, "approve", note="auto_advance_factory")
        if not decided.get("ok"):
            # Skip poisoned candidate and try again
            self.decide(
                nxt,
                "skip",
                note=f"auto_skip_approve_failed:{decided.get('error')}",
            )
            return self._auto_advance_to_next(depth=depth + 1)
        task_id = str((decided.get("task") or {}).get("id") or nxt)
        # decide(auto_advance) already ran start_execution synchronously
        if decided.get("auto_started_execution") or decided.get("execution_queued"):
            return decided.get("execution") or {
                "ok": True,
                "task": decided.get("task"),
                "message_ru": decided.get("message_ru"),
                "auto_from_decide": True,
            }
        return self.start_execution(
            task_id, clone=True, _auto_depth=depth + 1
        )

    def _task_key(self, reward_id: str) -> str | None:
        state = self._load()
        tasks = state.get("tasks") or {}
        if reward_id in tasks:
            return reward_id
        native = _resolve_native_opire_id(reward_id)
        alt = f"opire:{native}"
        if alt in tasks:
            return alt
        if native in tasks:
            return native
        return None

    def _resolve_candidate_for_decide(self, reward_id: str) -> dict[str, Any] | None:
        """Resolve one bounty without full Scanner rescan (keeps Approve/Skip snappy)."""
        key = self._task_key(reward_id)
        if key:
            existing = (self._load().get("tasks") or {}).get(key)
            if existing and existing.get("title"):
                return dict(existing)

        native = _resolve_native_opire_id(reward_id)
        try:
            raw = next(
                (r for r in fetch_opire_rewards() if str(r.get("id")) == native),
                None,
            )
        except Exception:  # noqa: BLE001
            raw = None
        if not raw:
            return None
        from swarm.farm_connectors.opire_connector import OpireConnector

        return OpireConnector().normalize(raw)

    def _queue_auto_execution(self, task_id: str) -> None:
        def _run() -> None:
            try:
                self.start_execution(task_id, clone=True)
            except Exception:  # noqa: BLE001
                pass

        threading.Thread(
            target=_run,
            name=f"opire-exec-{task_id[:24]}",
            daemon=True,
        ).start()

    def decide(self, reward_id: str, decision: str, *, note: str = "") -> dict[str, Any]:
        decision = (decision or "").strip().lower()
        if decision not in ("approve", "skip", "go"):
            return {"ok": False, "error": "decision must be approve|skip"}
        if decision == "go":
            decision = "approve"

        # ——— Skip: always instant, never full Scanner rescan ———
        if decision == "skip":
            state = self._load()
            tasks = state.setdefault("tasks", {})
            key = self._task_key(reward_id)
            if key and key in tasks:
                prev = self._mark_task_skipped(
                    dict(tasks[key]),
                    note=note or "skipped_from_active",
                    reason="ceo_skip",
                )
                tasks[key] = prev
            else:
                native = _resolve_native_opire_id(reward_id)
                task_id = (
                    reward_id
                    if str(reward_id).startswith("opire:")
                    else f"opire:{native}"
                )
                stub = {
                    "id": task_id,
                    "native_id": native,
                    "title": note or f"Skipped {native}",
                    "platform": "opire",
                    "estimated_reward_usd": 0,
                }
                prev = self._mark_task_skipped(
                    stub,
                    note=note or "skipped_from_scan",
                    reason="ceo_skip",
                )
                tasks[task_id] = prev
                # Also forever-register the raw reward_id CEO clicked
                if reward_id and reward_id not in (state.get("skipped_forever") or []):
                    state.setdefault("skipped_forever", []).append(str(reward_id))
            self._register_skipped_forever(state, prev)
            self._save(state)
            self._record_bounty_outcome(prev, outcome="skip")
            return {
                "ok": True,
                "task": prev,
                "message_ru": (
                    "Skip: снято навсегда. Scanner больше не покажет эту bounty."
                ),
            }

        # ——— Approve: resolve one reward (no full scan) ———
        cand = self._resolve_candidate_for_decide(reward_id)
        if cand is None:
            return {"ok": False, "error": "reward_not_found"}

        from swarm.opire_issue_intel import (
            analyze_issue_text,
            apply_sniper_to_candidate,
            build_ceo_action_links,
            fetch_issue_from_url,
        )

        cand = apply_sniper_to_candidate(dict(cand), timeout=8.0)
        if cand.get("recommendation") == "SKIP" and any(
            b in (cand.get("blockers") or [])
            for b in ("repo_unreachable", "repo_auth_required", "missing_repo")
        ):
            return {
                "ok": False,
                "error": cand.get("repo_probe", {}).get("error_code") or "repo_unreachable",
                "message_ru": cand.get("sniper_detail_ru")
                or (
                    "Sniper: репозиторий недоступен на GitHub. "
                    "Approve отклонён — выберите другой bounty."
                ),
                "task": cand,
            }

        intel = fetch_issue_from_url(str(cand.get("url") or ""), timeout=8.0)
        if intel.get("ok"):
            cand = dict(cand)
            cand["issue_body_preview"] = (intel.get("body") or "")[:2000]
            cand["issue_analysis"] = analyze_issue_text(
                str(cand.get("title") or ""),
                str(intel.get("body") or ""),
            )
            if cand["issue_analysis"].get("blockers"):
                return {
                    "ok": False,
                    "error": "blocked_by_issue_body",
                    "message_ru": (
                        "В описании Issue найден запрещённый паттерн "
                        f"({', '.join(cand['issue_analysis']['blockers'])}). Approve отклонён."
                    ),
                    "task": cand,
                }
        cand = dict(cand)
        cand["ceo_action_links"] = build_ceo_action_links(
            issue_url=str(cand.get("url") or ""),
            repo_full=str(cand.get("repository") or ""),
            issue_id=str(cand.get("issue_id") or ""),
        )
        cand["success_checklist"] = build_success_checklist(cand)
        cand["money_mode_eligible"] = is_money_mode_candidate(cand)

        from swarm.farm_preflight import run_preflight

        preflight = run_preflight(cand, deep=True, min_confidence=MONEY_MODE_THRESHOLD)
        cand["preflight"] = preflight
        if not preflight.get("approve_allowed"):
            return {
                "ok": False,
                "error": "preflight_skip",
                "preflight": preflight,
                "message_ru": (
                    f"Pre-flight SKIP: {preflight.get('action')}. "
                    "Approve запрещён — выберите другую bounty."
                ),
                "task": cand,
            }

        task_id = str(cand.get("id") or reward_id)
        state = self._load()
        tasks = state.setdefault("tasks", {})
        auto_exec = _farm_auto_execute_on_approve()
        tasks[task_id] = {
            **cand,
            # Auto-execute: status=executing immediately so Started/Execution counters move
            "status": "executing" if auto_exec else "ceo_approved",
            "pipeline_state": "QUEUED",
            "ceo_note": note,
            "approved_at": _now(),
            "updated_at": _now(),
            "pr_id": None,
            "pr_url": None,
            "merge_status": "not_started",
            "reward_status": "estimated",
            "withdrawal_status": "not_started",
            "payment_confirmation_id": None,
            "real_income": False,
            "payout_confirmed_usd": 0,
            "execution": {
                "ok": True,
                "stage": "queued",
                "message_ru": "Очередь Execution Engine…",
            }
            if auto_exec
            else None,
            "execution_checklist": [
                {"id": "approve", "title": "CEO Approve", "done": True},
                {"id": "repo_intel", "title": "Stage 1 — Repository Intelligence", "done": False},
                {"id": "planning", "title": "Stage 2 — Planning", "done": False},
                {"id": "research", "title": "Research Agent (needs_external fork)", "done": False},
                {"id": "implementation", "title": "Stage 3 — Implementation", "done": False},
                {"id": "validation", "title": "Stage 4 — Validation", "done": False},
                {"id": "pr_intelligence", "title": "Stage 5 — Draft PR package", "done": False},
                {"id": "ceo_submit", "title": "CEO Submit PR (/claim)", "done": False},
                {"id": "review_loop", "title": "Stage 6 — Review Loop", "done": False},
            ],
            "opire_commands": {
                "try": "/try",
                "claim": f"/claim #{cand.get('issue_id') or 'N'}",
            },
        }
        self._save(state)
        approved_task = tasks[task_id]

        if not auto_exec:
            return {
                "ok": True,
                "task": approved_task,
                "next_action": "start_execution",
                "auto_started_execution": False,
                "message_ru": (
                    "Approve принят (FARM_AUTO_EXECUTE_ON_APPROVE=0). "
                    "Нажмите «Запустить Execution Engine»."
                ),
            }

        # Auto-advance path manages start_execution itself after decide
        force_sync = str(note or "").startswith("auto_advance")
        use_async = _farm_decide_async_execute() and not force_sync

        if use_async:
            self._queue_auto_execution(task_id)
            return {
                "ok": True,
                "task": approved_task,
                "next_action": "monitor_execution",
                "auto_started_execution": True,
                "execution_queued": True,
                "message_ru": (
                    "Approve принят — карточка снята. "
                    "Execution Engine запущен в фоне (Clone → … → Draft PR)."
                ),
            }

        exec_out = self.start_execution(task_id, clone=True)
        task_after = (self._load().get("tasks") or {}).get(task_id) or approved_task
        st = str(task_after.get("status") or "")

        if exec_out.get("error") == "factory_busy":
            return {
                "ok": True,
                "task": task_after,
                "execution": exec_out,
                "next_action": "start_execution",
                "auto_started_execution": False,
                "message_ru": (
                    "Approve принят. Execution занят другой задачей — "
                    "когда линия свободна, нажмите «Запустить Execution Engine» "
                    "или Skip блокирующей."
                ),
            }

        if exec_out.get("ok") and st == "draft_pr":
            next_action = "ceo_submit"
        elif exec_out.get("ok") and st == "executing":
            next_action = "monitor_execution"
        elif exec_out.get("auto_skipped"):
            next_action = "scan_next"
        elif exec_out.get("ok"):
            next_action = "monitor_execution"
        else:
            next_action = "start_execution"

        msg = str(exec_out.get("message_ru") or "").strip()
        if not msg:
            msg = (
                "Approve → Execution Engine запущен (Clone → Analysis → "
                "Implementation → Draft PR)."
            )
        elif not msg.lower().startswith("approve"):
            msg = f"Approve → Execution: {msg}"

        return {
            "ok": True,
            "task": task_after,
            "execution": exec_out,
            "next_action": next_action,
            "auto_started_execution": True,
            "auto_skipped": bool(exec_out.get("auto_skipped")),
            "next_execution": exec_out.get("next_execution"),
            "message_ru": msg,
        }

    def start_execution(
        self, reward_id: str, *, clone: bool = True, _auto_depth: int = 0
    ) -> dict[str, Any]:
        """Run Execution Engine (Clone → … → Draft PR).

        Called automatically after CEO Approve (FARM_AUTO_EXECUTE_ON_APPROVE=1).
        Manual UI button remains for retry / factory_busy resume.
        Never asks CEO to open Cursor. Impossible → Skip forever → next TAKE.
        """
        from swarm.farm_env_bootstrap import ensure_farm_env
        from swarm.farm_opire_sync import maybe_post_try

        ensure_farm_env()
        state = self._load()
        task = (state.get("tasks") or {}).get(reward_id)
        if task is None:
            key = self._task_key(reward_id)
            if key:
                reward_id = key
                task = (state.get("tasks") or {}).get(reward_id)
        if not task:
            return {"ok": False, "error": "task_not_found"}
        if task.get("status") not in (
            "ceo_approved",
            "executing",
            "needs_external",
        ):
            return {
                "ok": False,
                "error": "approve_required",
                "message_ru": (
                    "Сначала CEO Approve. Execution Engine без Approve не стартует."
                ),
            }

        # Free the line: auto-skip other dead-ends (never block factory on Cursor waits)
        changed = False
        for tid, other in list((state.get("tasks") or {}).items()):
            if tid == reward_id:
                continue
            if _is_auto_dead_end(other) or (
                other.get("status") == "draft_pr" and not _task_has_patch(other)
            ):
                skipped = self._mark_task_skipped(
                    other,
                    note="auto_skip_clear_factory_line",
                    reason="not_auto_executable",
                )
                state["tasks"][tid] = skipped
                self._register_skipped_forever(state, skipped)
                changed = True
        if changed:
            self._save(state)
            state = self._load()
            task = (state.get("tasks") or {}).get(reward_id) or task

        # Sniper hard gate before clone — avoid long git failure on dead repos
        from swarm.opire_issue_intel import apply_sniper_to_candidate

        probed = apply_sniper_to_candidate(dict(task), timeout=12.0)
        task["repo_status"] = probed.get("repo_status")
        task["repo_probe"] = probed.get("repo_probe")
        task["blockers"] = probed.get("blockers") or task.get("blockers")
        # Clear stale false-positive auth errors after successful re-probe
        if probed.get("repo_status") == "ok":
            task["execution_error"] = None
            task["blockers"] = [
                b
                for b in (task.get("blockers") or [])
                if b
                not in (
                    "repo_auth_required",
                    "repo_unreachable",
                    "repo_rate_limited",
                    "missing_repo",
                )
            ]
        hard_block = probed.get("recommendation") == "SKIP" and any(
            b in (probed.get("blockers") or [])
            for b in ("repo_unreachable", "missing_repo")
        )
        # auth_required only blocks when probe still says so after token+git fallback
        if hard_block or (
            probed.get("repo_status") == "auth_required"
            and "repo_auth_required" in (probed.get("blockers") or [])
        ):
            detail = probed.get("sniper_detail_ru") or "repo_unreachable"
            task = self._mark_task_skipped(
                task,
                note=f"auto_skip_sniper:{detail}"[:240],
                reason="not_auto_executable",
            )
            state["tasks"][reward_id] = task
            self._register_skipped_forever(state, task)
            self._save(state)
            nxt = self._auto_advance_to_next(depth=_auto_depth)
            return {
                "ok": False,
                "error": probed.get("repo_probe", {}).get("error_code")
                or "repo_unreachable",
                "message_ru": (
                    f"Impossible (repo): {detail}. Задача снята. "
                    + ((nxt or {}).get("message_ru") or "")
                ),
                "task": task,
                "auto_skipped": True,
                "next_execution": nxt,
                "execution": {
                    "ok": False,
                    "error": probed.get("repo_probe", {}).get("error_code")
                    or "repo_not_found",
                    "error_detail": detail,
                    "stage": "skipped_auto",
                },
                "ceo_submit_required": False,
                "auto_submit_forbidden": True,
            }

        # One active factory line — auto-clear dead-ends first
        for tid, other in list((state.get("tasks") or {}).items()):
            if tid == reward_id:
                continue
            if _is_auto_dead_end(other):
                cleared = self._mark_task_skipped(
                    dict(other),
                    note="auto_skip_blocking_dead_end",
                    reason="not_auto_executable",
                )
                state["tasks"][tid] = cleared
                self._register_skipped_forever(state, cleared)
                continue
            if other.get("status") in (
                "executing",
                "draft_pr",
                "ceo_review",
                "pr_submitted",
                "maintainer_review",
                "changes_requested",
            ):
                self._save(state)
                return {
                    "ok": False,
                    "error": "factory_busy",
                    "message_ru": (
                        f"Уже в работе: {other.get('title') or tid}. "
                        "Дождитесь Draft PR Ready → Submit, либо Skip."
                    ),
                    "blocking_task_id": tid,
                }
        self._save(state)

        # Official Opire /try via GitHub API when token present (no CEO typing)
        try_res = maybe_post_try(task)
        task["try_post"] = try_res

        task["status"] = "executing"
        task["updated_at"] = _now()
        state["tasks"][reward_id] = task
        self._save(state)

        engine = FarmExecutionEngine(self._memory)
        report = engine.run_pipeline(task, clone=clone, run_impl=True)
        task = merge_execution_into_task(task, report)

        auto_skipped = False
        next_execution: dict[str, Any] | None = None

        if report.get("ok") and report.get("stage") == "awaiting_ceo_submit" and _task_has_patch(task):
            task["status"] = "draft_pr"
            task["reward_status"] = "draft_pr"
            msg = (
                report.get("ready_for_ceo", {}).get("message_ru")
                or (
                    "Draft PR Ready — патч есть. Нажмите «Отправить» "
                    "(единственное ручное действие CEO)."
                )
            )
        else:
            # Impossible for auto factory — never hand off to Cursor
            reason = (
                "not_auto_executable"
                if report.get("stage") == "awaiting_external"
                or (
                    (report.get("stages") or {})
                    .get("implementation", {})
                    .get("mode")
                    == "needs_external"
                )
                else "execution_failed"
            )
            detail = (
                report.get("error_detail")
                or report.get("error")
                or report.get("ready_for_ceo", {}).get("message_ru")
                or "Engine не получил безопасный патч"
            )
            task = self._mark_task_skipped(
                task,
                note=f"auto_skip:{reason}:{detail}"[:240],
                reason=reason,
            )
            auto_skipped = True
            msg = (
                f"Impossible — задача снята с конвейера ({reason}). "
                "CEO не пишет код вручную. Берём следующую bounty…"
            )
            next_execution = self._auto_advance_to_next(depth=_auto_depth)
            if next_execution and next_execution.get("message_ru"):
                msg = f"{msg} → {next_execution['message_ru']}"

        state = self._load()
        state.setdefault("tasks", {})[reward_id] = task
        self._register_skipped_forever(state, task) if auto_skipped else None
        self._save(state)
        return {
            "ok": bool(report.get("ok") and _task_has_patch(task)),
            "task": task,
            "execution": report,
            "stages": list(EXECUTION_STAGES),
            "message_ru": msg,
            "auto_skipped": auto_skipped,
            "next_execution": next_execution,
            "ceo_submit_required": bool(_task_has_patch(task)),
            "auto_submit_forbidden": True,
        }

    def ceo_submit_pr(
        self,
        reward_id: str,
        *,
        pr_id: str | None = None,
        pr_url: str | None = None,
        note: str = "",
        live: bool = True,
    ) -> dict[str, Any]:
        """CEO gate: live push + Draft PR via GitHub API. No manual PR URL/ID."""
        from pathlib import Path

        from swarm.farm_env_bootstrap import ensure_farm_env
        from swarm.farm_github_live import live_submit_draft_pr

        ensure_farm_env()
        state = self._load()
        key = self._task_key(reward_id)
        if not key:
            return {"ok": False, "error": "task_not_found"}
        task = (state.get("tasks") or {}).get(key)
        if not task:
            return {"ok": False, "error": "task_not_found"}
        if task.get("status") not in ("draft_pr", "ceo_review"):
            return {
                "ok": False,
                "error": "draft_required",
                "message_ru": (
                    "Сначала Execution Engine должен подготовить Draft PR "
                    "(статус draft_pr)."
                ),
            }

        exec_rep = task.get("execution") or {}
        impl = (exec_rep.get("stages") or {}).get("implementation") or {}
        patch_ready = bool(
            exec_rep.get("patch_ready")
            or (impl.get("files_touched") or [])
            or (exec_rep.get("ready_for_ceo") or {}).get("patch_ready")
        )
        if not patch_ready:
            return {
                "ok": False,
                "error": "no_patch",
                "message_ru": (
                    "Патч не создан (needs_external / Research Agent без diff). "
                    "Отправка на GitHub заблокирована — сначала «Повторить Research / Codex» "
                    "или Cursor brief."
                ),
            }

        if live and not pr_id and not pr_url:
            ws = Path(str((task.get("execution") or {}).get("workspace") or ""))
            if not ws.is_dir():
                ws = self._memory / "opire_workspaces" / re.sub(
                    r"[^a-zA-Z0-9_-]+", "_", str(task.get("id") or key)
                )[:80]
            created = live_submit_draft_pr(task, ws)
            if not created.get("ok"):
                return {
                    "ok": False,
                    "error": created.get("error") or "live_pr_failed",
                    "message_ru": created.get("message_ru")
                    or created.get("detail")
                    or "Не удалось создать PR через GitHub API",
                    "detail": created,
                }
            pr_id = str(created.get("pr_id") or created.get("pr_number") or "")
            pr_url = str(created.get("pr_url") or "")
            task["pr_number"] = created.get("pr_number")
            task["pr_node_id"] = created.get("pr_node_id")
            task["live_pr"] = created
            state["tasks"][key] = task
            self._save(state)

        return self.advance(
            key,
            "pr_submitted",
            pr_id=pr_id,
            pr_url=pr_url,
            note=note or "CEO Submit — live Draft PR via GitHub API (/claim in body)",
        )

    def sync_status(self, reward_id: str, *, confirm_real: bool = False) -> dict[str, Any]:
        """Pull PR/merge/Opire state automatically. Optional promote to REAL."""
        from swarm.farm_env_bootstrap import ensure_farm_env
        from swarm.farm_opire_sync import sync_task_from_platforms

        ensure_farm_env()
        state = self._load()
        key = self._task_key(reward_id)
        if not key:
            return {"ok": False, "error": "task_not_found"}
        task = dict((state.get("tasks") or {}).get(key) or {})
        if not task:
            return {"ok": False, "error": "task_not_found"}

        synced = sync_task_from_platforms(task)
        task = synced.get("task") or task
        msg = "Статус синхронизирован с GitHub/Opire."

        if confirm_real or task.get("status") in ("withdraw", "payment_available"):
            if task.get("merge_status") == "merged" and task.get("payment_confirmation_id"):
                task["status"] = "payout_confirmed"
                task["real_income"] = True
                task["reward_status"] = "payout_confirmed"
                task["withdrawal_status"] = "complete"
                if not task.get("payout_confirmed_usd"):
                    task["payout_confirmed_usd"] = float(
                        task.get("estimated_reward_usd") or task.get("reward_usd") or 0
                    )
                msg = (
                    "REAL: выплата подтверждена автоматически "
                    f"({task.get('payment_confirmation_id')})."
                )
                if not task.get("learning_recorded"):
                    self._record_bounty_outcome(task, outcome="win")
                    task["learning_recorded"] = True
            else:
                return {
                    "ok": False,
                    "error": "not_ready_for_real",
                    "message_ru": (
                        "REAL ещё нельзя: нужен merge PR (GitHub). "
                        "Нажмите «Синхронизировать» после merge — ID вводить не нужно."
                    ),
                    "sync": synced,
                    "task": task,
                }

        state["tasks"][key] = task
        self._save(state)
        return {
            "ok": True,
            "task": task,
            "sync": synced,
            "message_ru": msg,
            "events": synced.get("events") or [],
        }

    def advance(
        self,
        reward_id: str,
        status: str,
        *,
        pr_id: str | None = None,
        pr_url: str | None = None,
        payment_confirmation_id: str | None = None,
        payout_usd: float | None = None,
        note: str = "",
    ) -> dict[str, Any]:
        status = (status or "").strip().lower()
        if status not in REWARD_STATES:
            return {"ok": False, "error": "invalid_status", "allowed": list(REWARD_STATES)}

        # REAL path: never ask CEO for opaque IDs — sync platform facts first
        if status in REAL_INCOME_STATES and not payment_confirmation_id:
            synced = self.sync_status(reward_id, confirm_real=True)
            if synced.get("ok") and (synced.get("task") or {}).get("real_income"):
                return synced
            return {
                "ok": False,
                "error": "auto_confirmation_pending",
                "message_ru": synced.get("message_ru")
                or (
                    "Нет ручного Payment ID. Дождитесь merge и нажмите "
                    "«Синхронизировать / REAL» — Farm соберёт confirmation сам."
                ),
                "detail": synced,
            }

        state = self._load()
        key = self._task_key(reward_id)
        if not key:
            return {"ok": False, "error": "task_not_found"}
        task = (state.get("tasks") or {}).get(key)
        if not task:
            return {"ok": False, "error": "task_not_found"}
        reward_id = key

        task["status"] = status
        task["updated_at"] = _now()
        if note:
            task["ceo_note"] = note
        if pr_id:
            task["pr_id"] = pr_id
            task["pr_number"] = pr_id
        if pr_url:
            task["pr_url"] = pr_url
        if payment_confirmation_id:
            task["payment_confirmation_id"] = payment_confirmation_id

        # Reward Protection — REAL only with platform-derived or synced confirmation
        if status in REAL_INCOME_STATES:
            if not task.get("payment_confirmation_id"):
                return {
                    "ok": False,
                    "error": "payout_confirmation_required",
                    "message_ru": (
                        "REAL только после auto-confirmation (merge SHA + Opire id). "
                        "Ручной ввод ID отключён."
                    ),
                }
            task["real_income"] = True
            task["payout_confirmed_usd"] = float(
                payout_usd if payout_usd is not None else task.get("estimated_reward_usd") or 0
            )
            task["reward_status"] = "payout_confirmed"
            task["withdrawal_status"] = "complete"
            if not task.get("learning_recorded"):
                self._record_bounty_outcome(task, outcome="win")
                task["learning_recorded"] = True
        else:
            task["real_income"] = False
            task["reward_status"] = status

        if status == "draft_pr":
            for step in task.get("execution_checklist") or []:
                if step.get("id") in (
                    "repo_intel",
                    "planning",
                    "implementation",
                    "validation",
                    "pr_intelligence",
                ):
                    step["done"] = True
        if status == "pr_submitted":
            for step in task.get("execution_checklist") or []:
                if step.get("id") == "ceo_submit":
                    step["done"] = True
        if status == "changes_requested":
            task["had_changes_requested"] = True
            for step in task.get("execution_checklist") or []:
                if step.get("id") == "review_loop":
                    step["done"] = False

        state["tasks"][reward_id] = task
        self._save(state)
        return {"ok": True, "task": task}
