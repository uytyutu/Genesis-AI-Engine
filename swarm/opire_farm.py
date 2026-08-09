"""Opire Farm — AUTO-RUN bounty orchestration via official Opire API + GitHub.

Official flow only (docs.opire.dev):
  /try on issue → implement → PR with /claim #N → maintainer merge → Opire payout

AUTO-RUN (FARM_AUTONOMOUS=1, default):
  Scanner → Pre-flight GO≥80 → Auto-Approve → Execution → Draft PR → Auto-Submit
  → wait Merge → Opire verify → REAL Ledger → next bounty

CEO gates only for REVIEW / ToS / large scope / budget / Stop / exhausted retries.
Estimated ≠ REAL. REAL only after confirmed payout (Reward Protection).
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
            "Один полный цикл AUTO-RUN: GO→Approve→Execution→Draft→Submit→Merge→REAL. "
            "Без ручных ID. Estimated ≠ REAL."
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
        return (
            "Узкое место: Auto-Approve / Pre-flight GO — кандидаты есть, "
            "в работу ещё никто не взят."
        )
    if executed < approved:
        return "Узкое место: Execution Engine — одобрено, выполнение ещё не доведена."
    if pr_submitted < executed:
        return "Узкое место: Draft→Submit PR (включите FARM_AUTO_SUBMIT_PR или CEO Submit)."
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
    elif n_comp <= 10:
        # Crowded but still often claimable — REVIEW, not hard SKIP
        conf -= 10
        acceptance -= 12
    else:
        conf -= 16
        acceptance -= 20
        blockers.append("high_competition")

    # Reward vs complexity heuristic
    if 20 <= reward <= 400:
        conf += 8
        est_hours = max(0.5, min(6.0, reward / 80.0))
    elif reward < 20:
        conf += 2
        est_hours = 0.75
    elif reward <= 2500:
        conf -= 6
        est_hours = min(24.0, reward / 60.0)
    elif reward <= 8000:
        # Large but plausible — do not hard-block Money Mode solely on price
        conf -= 12
        est_hours = min(40.0, reward / 50.0)
    else:
        # Absurd Opire pendingPrice outliers ($100k+) — treat as suspect scope
        conf -= 22
        est_hours = 48.0
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
    # Review All must honor the same forever/seen exclude — otherwise Skip reappears
    raw_review = list(out.get("all_preview") or out.get("review_all") or [])
    # Unfiltered live market snapshot (real Opire $) — Skip ledger must not hide that work exists
    market_live = [r for r in raw_review if isinstance(r, dict) and float(r.get("reward_usd") or 0) > 0]
    market_live.sort(
        key=lambda x: (
            0 if str(x.get("recommendation") or "") == "TAKE" else 1,
            -float(x.get("overall_confidence_pct") or x.get("confidence_pct") or 0),
            -float(x.get("reward_usd") or 0),
        )
    )
    out["market_live"] = market_live[:40]
    out["market_live_count"] = len(market_live)
    out["market_live_note_ru"] = (
        f"Живой рынок Opire: {len(market_live)} bounty с $ (не симуляция). "
        "Skip ledger скрывает их из Approve — это не «работы нет»."
    )
    review_fresh = [r for r in raw_review if isinstance(r, dict) and not _is_excluded(r)]
    out["review_all"] = review_fresh
    out["review_all_excluded"] = max(0, len(raw_review) - len(review_fresh))
    # If Skip ledger wiped TAKE, still surface best live market rows for CEO
    if not out["candidates"] and market_live:
        out["candidates"] = [
            r
            for r in market_live
            if str(r.get("recommendation") or "") != "SKIP"
        ][:12]
        out["candidates_from_market_live"] = True
    out.setdefault("confidence_bands", {})
    if not out.get("analytics"):
        from swarm.farm_scan_analytics import build_scan_analytics

        out["analytics"] = build_scan_analytics(
            list(out.get("market_live") or out.get("review_all") or []),
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


def _farm_bounty_advance_on_fail() -> bool:
    """Only take next bounty after execution_failed when explicitly allowed."""
    flag = (os.environ.get("FARM_BOUNTY_ADVANCE_ON_FAIL") or "0").strip().lower()
    return flag in ("1", "true", "yes", "on")


def _farm_auto_execute_on_approve() -> bool:
    """Approve must start Execution Engine automatically (default ON)."""
    flag = (os.environ.get("FARM_AUTO_EXECUTE_ON_APPROVE") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def _farm_autonomous_enabled() -> bool:
    from swarm.farm_autonomous import farm_autonomous_enabled

    return farm_autonomous_enabled()


def _farm_auto_submit_enabled() -> bool:
    from swarm.farm_autonomous import farm_auto_submit_enabled

    return farm_auto_submit_enabled()


def _farm_decide_async_execute() -> bool:
    """Approve returns instantly; Execution runs in background (default ON).

    Sync under pytest so unit tests can assert task status after decide().
    Force sync with FARM_DECIDE_ASYNC_EXECUTE=0.
    """
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    flag = (os.environ.get("FARM_DECIDE_ASYNC_EXECUTE") or "1").strip().lower()
    return flag not in ("0", "false", "no", "off")


def _task_age_seconds(task: dict[str, Any]) -> float:
    raw = str(task.get("updated_at") or task.get("approved_at") or "")
    if not raw:
        return 0.0
    try:
        from datetime import datetime, timezone

        ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (datetime.now(timezone.utc) - ts).total_seconds())
    except Exception:
        return 0.0


def _is_zombie_queued_execution(task: dict[str, Any], *, max_age_s: float = 90.0) -> bool:
    """True when Approve queued Execution but worker never progressed (restart/crash)."""
    if str(task.get("status") or "") != "executing":
        return False
    pipe = str(task.get("pipeline_state") or "")
    stage = str((task.get("execution") or {}).get("stage") or "")
    if pipe not in ("QUEUED", "") and stage not in ("queued", ""):
        return False
    if pipe == "QUEUED" or stage == "queued" or not (task.get("execution") or {}).get("stages"):
        return _task_age_seconds(task) >= max_age_s
    return False


def _is_recoverable_execution_error(error: Any) -> bool:
    """Healed queue / factory clear — not a hard Execution failure."""
    err = str(error or "").strip().lower()
    return err.startswith("zombie_queued") or err in {
        "factory_busy",
        "zombie_queued_healed",
        "zombie_queued_cleared_for_factory",
    }


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
    """Split TAKE pool into Money Mode (default Approve list) vs rest.

    If GO/Money Mode is empty, fall back to best TAKE so Farm never looks like
    «no paid work» when Opire still has live USD bounties.
    """
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
        else:
            # Keep enriched fields on non-money rows too
            pass
    # Re-attach enriched take list
    enriched_take: list[dict[str, Any]] = []
    money_ids = {str(c.get("id")) for c in money}
    for row in take:
        if str(row.get("id")) in money_ids:
            hit = next(c for c in money if str(c.get("id")) == str(row.get("id")))
            enriched_take.append(hit)
        else:
            c = dict(row)
            if "success_checklist" not in c:
                c["success_checklist"] = build_success_checklist(c)
            if "preflight" not in c:
                c["preflight"] = run_preflight(
                    c, deep=False, min_confidence=DEFAULT_CONFIDENCE_THRESHOLD
                )
            c.setdefault("money_mode_eligible", False)
            enriched_take.append(c)
    take = enriched_take
    money.sort(
        key=lambda x: (
            0 if (x.get("preflight") or {}).get("verdict") == "GO" else 1,
            -float(x.get("overall_confidence_pct") or 0),
        )
    )
    go_list = [c for c in money if (c.get("preflight") or {}).get("verdict") == "GO"]
    out["candidates_take_all"] = take
    fallback_note = ""
    if go_list:
        out["candidates"] = go_list
        mode = "money_go"
    elif money:
        out["candidates"] = money[:8]
        mode = "money_eligible"
    elif take:
        # Prefer TAKE, then fill from live market so CEO sees real $ work
        merged = list(take[:12])
        seen = {str(c.get("id")) for c in merged}
        for r in out.get("market_live") or []:
            if len(merged) >= 12:
                break
            rid = str(r.get("id") or "")
            if not rid or rid in seen:
                continue
            if str(r.get("recommendation") or "") == "SKIP":
                continue
            merged.append(r)
            seen.add(rid)
        out["candidates"] = merged
        mode = "take_fallback"
        fallback_note = (
            "Money Mode GO пуст — показаны TAKE + живой рынок Opire (реальные $). "
            "Approve всё ещё ручной."
        )
    else:
        # Last resort: live market preview (may include REVIEW)
        preview = [
            r
            for r in (
                out.get("market_live")
                or out.get("review_all")
                or out.get("all_preview")
                or []
            )
            if isinstance(r, dict)
            and float(r.get("reward_usd") or 0) > 0
            and str(r.get("recommendation") or "") != "SKIP"
        ]
        preview.sort(
            key=lambda x: -float(x.get("overall_confidence_pct") or x.get("confidence_pct") or 0)
        )
        out["candidates"] = preview[:12]
        mode = "market_fallback"
        fallback_note = (
            "Жёсткие фильтры / Skip ledger обнулили TAKE. "
            "Ниже — открытый рынок Opire (реальные $), не симуляция."
        )
    out["threshold"] = (
        MONEY_MODE_THRESHOLD if mode.startswith("money") else DEFAULT_CONFIDENCE_THRESHOLD
    )
    out["money_mode"] = {
        "enabled_default": True,
        "threshold": MONEY_MODE_THRESHOLD,
        "count": len(out["candidates"]),
        "hidden_count": max(0, len(take) - len(out["candidates"])),
        "go_count": len(go_list),
        "mode": mode,
        "note_ru": fallback_note
        or (
            "Money Mode + Pre-flight: GO (Confidence ≥80%, repo alive). "
            "Если пусто — Farm показывает TAKE/рынок с реальными $."
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
        # Zombie heal / factory_busy are recoverable — never auto-Skip forever
        if _is_recoverable_execution_error(task.get("execution_error")):
            return False
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
        # Also honor permanent skip registry + Seen Ledger
        for sid in state.get("skipped_forever") or []:
            exclude.add(str(sid))
        for lid, entry in (state.get("seen_ledger") or {}).items():
            if not lid:
                continue
            decision = ""
            if isinstance(entry, dict):
                decision = str(entry.get("decision") or "")
            if decision in (
                "SKIPPED_PERMANENT",
                "IMPOSSIBLE",
                "APPROVED",
                "PAID",
                "MERGED",
            ) or decision.startswith("SKIP"):
                exclude.add(str(lid))
                if isinstance(entry, dict):
                    for alias in entry.get("id_aliases") or []:
                        if alias:
                            exclude.add(str(alias))
        scan = (
            scan_opire(
                enrich_top=enrich_top,
                sniper_top=8,
                exclude_ids=exclude,
                # Pool for Money Mode filter (full TAKE band). Money Mode keeps ≥80%.
                threshold=max(55.0, DEFAULT_CONFIDENCE_THRESHOLD - 12.0),
            )
            if force_scan
            else None
        )
        if force_scan and isinstance(scan, dict):
            scan = apply_money_mode_to_scan(scan)
            # Persist last live scan so opening Farm is not empty
            try:
                state["last_scan"] = {
                    "at": scan.get("at"),
                    "scanned": scan.get("scanned"),
                    "candidates": scan.get("candidates") or [],
                    "candidates_take_all": scan.get("candidates_take_all") or [],
                    "review_all": (scan.get("review_all") or [])[:60],
                    "market_live": (scan.get("market_live") or [])[:40],
                    "market_live_count": scan.get("market_live_count"),
                    "market_live_note_ru": scan.get("market_live_note_ru"),
                    "money_mode": scan.get("money_mode"),
                    "threshold": scan.get("threshold"),
                    "confidence_bands": scan.get("confidence_bands"),
                    "analytics": scan.get("analytics"),
                    "sniper_probed": scan.get("sniper_probed"),
                    "sniper_skipped": scan.get("sniper_skipped"),
                    "excluded_already_active": scan.get("excluded_already_active"),
                    "ok": scan.get("ok", True),
                    "source": scan.get("source"),
                    "catalog": scan.get("catalog") or scan.get("connectors"),
                }
                self._save(state)
            except Exception:
                pass
            touched = False
            for row in list(scan.get("candidates") or []) + list(scan.get("review_all") or []):
                if isinstance(row, dict) and row.get("id"):
                    if self._touch_seen_ledger_analyzed(state, row):
                        touched = True
            if touched:
                self._save(state)
        else:
            cached = state.get("last_scan") if isinstance(state.get("last_scan"), dict) else {}
            scan = {
                "ok": True,
                "candidates": list(cached.get("candidates") or []),
                "candidates_take_all": list(cached.get("candidates_take_all") or []),
                "scanned": int(cached.get("scanned") or 0),
                "filtered_out": 0,
                "threshold": cached.get("threshold") or MONEY_MODE_THRESHOLD,
                "review_all": list(cached.get("review_all") or []),
                "market_live": list(cached.get("market_live") or []),
                "market_live_count": cached.get("market_live_count"),
                "market_live_note_ru": cached.get("market_live_note_ru")
                or (
                    "Нет кэша скана — нажмите «Обновить Scanner» для живого api.opire.dev."
                ),
                "money_mode": cached.get("money_mode")
                or {
                    "note_ru": "Кэш. 🔍 Researching… Scanner обновит live Opire сам.",
                },
                "confidence_bands": cached.get("confidence_bands") or {},
                "analytics": cached.get("analytics"),
                "from_cache": True,
                "at": cached.get("at"),
                "source": cached.get("source") or "cache",
                "catalog": cached.get("catalog") or [],
            }
        tasks = [_normalize_stale_external_task(t) for t in tasks_map.values()]
        # Persist healed statuses so Retry button / Timeline stay consistent
        healed = False
        # Clear legacy hard-error labels left by older zombie heal
        for t in list(tasks_map.values()):
            tid = str(t.get("id") or "")
            if not tid:
                continue
            if _is_recoverable_execution_error(t.get("execution_error")):
                t = dict(t)
                t["execution_heal"] = str(t.get("execution_error") or "zombie_queued_healed")
                t["execution_error"] = None
                if str(t.get("status") or "") in ("ceo_approved", "executing", "queued"):
                    t["auto_retry_execution"] = True
                    t["status"] = "ceo_approved"
                tasks_map[tid] = t
                healed = True
        # Unlock factory: zombie QUEUED after process restart blocks all Approves
        for t in list(tasks):
            if not _is_zombie_queued_execution(t, max_age_s=60.0):
                continue
            tid = str(t.get("id") or "")
            if not tid:
                continue
            t = dict(tasks_map.get(tid) or t)
            t["status"] = "ceo_approved"
            t["pipeline_state"] = "QUEUED"
            t["execution"] = {
                "ok": False,
                "stage": "queued",
                "message_ru": (
                    "Очередь сброшена после перезапуска. "
                    "🧠 Thinking… агент перезапустит Execution сам."
                ),
            }
            # Soft note — Timeline must not treat this as hard fail / auto-Skip
            t["execution_error"] = None
            t["execution_heal"] = "zombie_queued_healed"
            t["auto_retry_execution"] = True
            t["updated_at"] = _now()
            tasks_map[tid] = t
            healed = True
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
            # Never block status poll with Clone/Execution — resume in background
            def _bg_retry() -> None:
                try:
                    self._maybe_auto_retry_healed(self._load())
                except Exception:
                    pass

            threading.Thread(
                target=_bg_retry, name="farm-auto-retry-heal", daemon=True
            ).start()
        tasks = [_normalize_stale_external_task(t) for t in (state.get("tasks") or {}).values()]
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
                if str(t.get("status") or "") == "execution_failed"
                or (t.get("execution") or {}).get("stage") == "failed"
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

        from swarm.farm_pipeline_state import (
            attach_pipeline_state,
            count_execution_success,
            pipeline_kpi,
        )

        exec_stats = count_execution_success(tasks)
        tasks = exec_stats.pop("tasks")
        # Keep funnel.executed aligned with pipeline Started
        funnel["executed"] = int(exec_stats["started"])
        funnel["execution_in_flight"] = int(exec_stats["execution"])
        funnel["pipeline_draft_pr"] = int(exec_stats["draft_pr"])

        lifetime = state.get("pipeline_lifetime") if isinstance(state.get("pipeline_lifetime"), dict) else {}
        pipeline = pipeline_kpi(
            found=scanned,
            lifetime=lifetime,
            live=exec_stats,
        )
        # Prefer lifetime for CEO-facing Approved/Started so Impossible→Skip doesn't wipe the funnel
        funnel["ceo_approved"] = max(int(funnel["ceo_approved"] or 0), int(pipeline["approved"]))
        funnel["executed"] = max(int(funnel["executed"] or 0), int(pipeline["started"]))
        funnel["pipeline_lifetime"] = lifetime

        execution_success = {
            **exec_stats,
            "avg_execution_s": avg_exec_s,
            "avg_execution_samples": len(elapsed_vals),
            "approved": int(pipeline["approved"]),
            "started": int(pipeline["started"]),
            "draft_pr": int(pipeline["draft_pr"]),
            "merged": int(pipeline["merged"]),
            "paid": int(pipeline["paid"]),
            "note_ru": (
                "Pipeline KPI (lifetime). Started > 0 = Execution реально стартовал. "
                + str(exec_stats.get("note_ru") or "")
            ),
        }
        if execution_success["approved"]:
            execution_success["start_rate"] = round(
                execution_success["started"] / execution_success["approved"], 3
            )
            execution_success["complete_rate"] = round(
                execution_success["completed"] / max(execution_success["approved"], 1), 3
            )

        # Durable AUTO-RUN pulse on every panel poll (non-blocking outside tests)
        autonomous: dict[str, Any]
        if os.environ.get("PYTEST_CURRENT_TEST"):
            autonomous = {"ok": True, "skipped": "pytest_panel", "actions": []}
        else:

            def _bg_tick() -> None:
                try:
                    self.autonomous_tick(max_actions=3)
                except Exception:
                    pass

            threading.Thread(
                target=_bg_tick, name="farm-autonomous-tick", daemon=True
            ).start()
            autonomous = {
                "ok": True,
                "queued": True,
                "autonomous": _farm_autonomous_enabled(),
                "auto_submit": _farm_auto_submit_enabled(),
            }

        return {
            "ok": True,
            "mode": "opire_primary",
            "engine": "farm_engine",
            "autonomous": autonomous,
            "separate_from": "commercial_engine",
            "pipeline": pipeline,
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
                "approved": int(pipeline["approved"]),
                "executed": int(pipeline["started"]),
                "draft_pr": int(pipeline["draft_pr"]),
                "merged": int(pipeline["merged"]),
                "paid": int(pipeline["paid"]),
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
                        "role_ru": "Paper research рынков (не live scraping)",
                        "href": "/alpha-hunter",
                        "primary_kpi": "Paper ROI · не реальные $",
                        "mode": "paper",
                        "honesty_ru": (
                            "Сейчас это симуляция / paper model. Живой поиск Upwork/Fiverr "
                            "не подключён. Approve только для adapter_backed действий."
                        ),
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
                "Pre-flight GO≥80 → Auto-Approve (REVIEW → CEO)",
                "AUTO-RUN Execution (Clone → … → Draft PR)",
                "Auto-Submit PR (/claim) when policy allows",
                "Merge → Opire verify → REAL Ledger → next bounty",
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
            "folders": {
                "new": {
                    "label_ru": "Новые",
                    "count": len(scan.get("candidates") or [])
                    + len(
                        [
                            r
                            for r in (scan.get("review_all") or [])
                            if isinstance(r, dict)
                            and str(r.get("id") or "")
                            not in {
                                str(c.get("id") or "")
                                for c in (scan.get("candidates") or [])
                                if isinstance(c, dict)
                            }
                        ]
                    ),
                    "hint_ru": "Только bounty без постоянного решения (Skip/Approve).",
                },
                "active": {
                    "label_ru": "В работе",
                    "count": sum(
                        1
                        for t in tasks
                        if t.get("status") not in ("completed", "skipped", None, "available")
                    ),
                    "hint_ru": "EXECUTING · DRAFT_PR · WAITING MERGE",
                },
                "archive": {
                    "label_ru": "Архив",
                    "count": sum(1 for t in tasks if t.get("status") in ("completed", "skipped"))
                    + len(
                        [
                            e
                            for e in (state.get("seen_ledger") or {}).values()
                            if isinstance(e, dict)
                            and str(e.get("decision") or "") == "SKIPPED_PERMANENT"
                            and not e.get("canonical_id")
                        ]
                    ),
                    "hint_ru": "PAID · MERGED · SKIPPED · IMPOSSIBLE",
                },
            },
            "seen_ledger_count": len(
                [
                    e
                    for e in (state.get("seen_ledger") or {}).values()
                    if isinstance(e, dict) and not e.get("canonical_id")
                ]
            ),
            "skipped_forever_count": len(state.get("skipped_forever") or []),
            "active_tasks": [
                attach_pipeline_state(t)
                for t in tasks
                if t.get("status") not in ("completed", "skipped")
            ],
            "archive_tasks": [
                attach_pipeline_state(t)
                for t in tasks
                if t.get("status") in ("completed", "skipped")
            ][:40],
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
        """Permanent skip + Seen Ledger — Scanner must never re-offer this bounty."""
        forever = state.setdefault("skipped_forever", [])
        keys: list[str] = []
        for key in (
            str(task.get("id") or ""),
            str(task.get("native_id") or ""),
            f"opire:{task.get('native_id')}" if task.get("native_id") else "",
        ):
            if key and key not in forever:
                forever.append(key)
            if key:
                keys.append(key)
        ledger = state.setdefault("seen_ledger", {})
        if not isinstance(ledger, dict):
            ledger = {}
            state["seen_ledger"] = ledger
        primary = str(task.get("id") or "") or (keys[0] if keys else "")
        if not primary:
            return
        prev = ledger.get(primary) if isinstance(ledger.get(primary), dict) else {}
        times = int(prev.get("times_shown") or 0) + 1
        entry = {
            "issue_id": primary,
            "native_id": str(task.get("native_id") or "") or None,
            "repo": str(task.get("repository") or task.get("repo") or "") or None,
            "title": str(task.get("title") or "")[:160] or None,
            "first_seen": prev.get("first_seen") or _now(),
            "last_seen": _now(),
            "times_shown": times,
            "decision": "SKIPPED_PERMANENT",
            "reason": str(task.get("skip_reason") or task.get("ceo_note") or "ceo_skip")[:120],
            "id_aliases": sorted(set(keys)),
        }
        ledger[primary] = entry
        for alias in keys:
            if alias != primary and alias not in ledger:
                ledger[alias] = {**entry, "issue_id": alias, "canonical_id": primary}

    def _touch_seen_ledger_analyzed(
        self, state: dict[str, Any], row: dict[str, Any]
    ) -> bool:
        """First-seen ANALYZED only. Decisions (Skip/Approve) overwrite later."""
        rid = str(row.get("id") or "")
        if not rid:
            return False
        ledger = state.setdefault("seen_ledger", {})
        if not isinstance(ledger, dict):
            return False
        if rid in ledger:
            return False
        native = str(row.get("native_id") or "")
        if native and native in (state.get("skipped_forever") or []):
            return False
        if native and f"opire:{native}" in (state.get("skipped_forever") or []):
            return False
        ledger[rid] = {
            "issue_id": rid,
            "native_id": native or None,
            "repo": str(row.get("repository") or "") or None,
            "title": str(row.get("title") or "")[:160] or None,
            "first_seen": _now(),
            "last_seen": _now(),
            "times_shown": 1,
            "decision": "ANALYZED",
            "reason": None,
            "id_aliases": [rid],
        }
        return True

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

    def _mark_execution_failed(
        self,
        task: dict[str, Any],
        *,
        detail: str,
        reason: str = "execution_failed",
        stage: str = "failed",
        error_code: str = "",
    ) -> dict[str, Any]:
        """Persist failed bounty — not completed, not masked as Impossible."""
        from swarm.farm_stabilization import (
            WORKSPACE_CORRUPTION,
            build_failure_visibility,
            max_execution_attempts,
            quarantine_workspace_safe,
        )

        out = dict(task)
        attempts = int(out.get("execution_attempts") or 0)
        if attempts <= 0:
            attempts = 1
            out["execution_attempts"] = attempts
        max_a = max_execution_attempts()
        code = (error_code or reason or "").strip()
        ws_path = ""
        try:
            eng = FarmExecutionEngine(self._memory)
            ws_path = str(eng.workspace_for(str(out.get("id") or "")))
        except Exception:
            ws_path = ""
        vis = build_failure_visibility(
            job_id=str(out.get("id") or ""),
            queue="BOUNTY_EXECUTION_QUEUE",
            stage=stage,
            attempt=attempts,
            error=str(detail),
            error_code=code,
            workspace=ws_path,
        )
        out["status"] = "execution_failed"
        out["reward_status"] = "execution_failed"
        out["skip_reason"] = reason
        out["ceo_note"] = (
            f"execution_failed:{vis['error_class']}:{vis['next_action']}:{detail}"
        )[:240]
        out["execution_error"] = str(detail)[:800]
        out["pending_execution"] = False
        out["auto_retry_execution"] = bool(vis["retryable"]) and attempts < max_a
        out["queue_id"] = "BOUNTY_EXECUTION_QUEUE"
        out["error_class"] = vis["error_class"]
        out["retryable"] = vis["retryable"]
        out["next_action"] = vis["next_action"]
        out["failure"] = vis
        out["updated_at"] = _now()
        if vis["error_class"] == WORKSPACE_CORRUPTION and ws_path:
            q = quarantine_workspace_safe(Path(ws_path))
            out["workspace_quarantine"] = q
            out["force_fresh_workspace"] = True
        if out.get("auto_retry_execution"):
            from swarm.farm_autonomous import _set_retry_backoff

            _set_retry_backoff(out)
        else:
            out["next_retry_at"] = None
        ex = dict(out.get("execution") or {})
        ex["ok"] = False
        ex["stage"] = stage
        ex["error"] = str(detail)[:800]
        ex["error_class"] = vis["error_class"]
        ex["retryable"] = vis["retryable"]
        ex["next_action"] = vis["next_action"]
        ex["patch_ready"] = False
        ex["message_ru"] = (
            f"EXECUTION_FAILED · {vis['error_class']} · attempt={attempts}/{max_a} · "
            f"{vis['next_action']} · {str(detail)[:160]}"
        )
        out["execution"] = ex
        return out

    def _mark_task_skipped_and_count(
        self,
        state: dict[str, Any],
        task: dict[str, Any],
        *,
        note: str,
        reason: str = "skipped",
    ) -> dict[str, Any]:
        """Skip + lifetime Impossible when execution already started."""
        from swarm.farm_pipeline_state import bump_pipeline_lifetime

        out = self._mark_task_skipped(task, note=note, reason=reason)
        if reason.startswith("not_auto") or str(note).startswith("auto_skip"):
            bump_pipeline_lifetime(state, "impossible")
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

    def _mark_pending_execution(self, task_id: str, *, reason: str = "factory_busy") -> None:
        state = self._load()
        task = dict((state.get("tasks") or {}).get(task_id) or {})
        if not task:
            return
        task["pending_execution"] = True
        task["auto_retry_execution"] = True
        task["status"] = "ceo_approved"
        task["pipeline_state"] = "QUEUED"
        task["execution_error"] = None
        task["execution_heal"] = reason
        task["execution"] = {
            "ok": False,
            "stage": "queued",
            "message_ru": (
                "В очереди AUTO-RUN — Clone стартует без кнопки "
                "«Запустить Execution», когда линия свободна."
            ),
        }
        task["updated_at"] = _now()
        state.setdefault("tasks", {})[task_id] = task
        self._save(state)

    def _queue_auto_execution(self, task_id: str) -> None:
        def _run() -> None:
            try:
                out = self.start_execution(task_id, clone=True)
                if isinstance(out, dict) and out.get("error") == "factory_busy":
                    self._mark_pending_execution(task_id, reason="factory_busy")
            except Exception as exc:  # noqa: BLE001
                try:
                    state = self._load()
                    task = (state.get("tasks") or {}).get(task_id)
                    if isinstance(task, dict):
                        task["execution_error"] = f"queue_crash:{exc}"[:240]
                        task["pending_execution"] = True
                        task["auto_retry_execution"] = True
                        task["status"] = "ceo_approved"
                        task["execution"] = {
                            "ok": False,
                            "stage": "queued",
                            "message_ru": (
                                f"Execution thread crash — watchdog retry: {exc}"
                            )[:200],
                        }
                        task["updated_at"] = _now()
                        state["tasks"][task_id] = task
                        self._save(state)
                except Exception:  # noqa: BLE001
                    pass

        threading.Thread(
            target=_run,
            name=f"opire-exec-{task_id[:24]}",
            daemon=True,
        ).start()

    def autonomous_tick(self, *, max_actions: int = 3) -> dict[str, Any]:
        """Durable AUTO-RUN pulse — drain queue, auto-approve GO, auto-submit."""
        from swarm.farm_autonomous import run_autonomous_tick

        return run_autonomous_tick(self, max_actions=max_actions)

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
            # Auto-Skip dead repo so Approve always advances the conveyor
            detail = cand.get("sniper_detail_ru") or "repo_unreachable"
            state = self._load()
            tasks = state.setdefault("tasks", {})
            task_id = str(cand.get("id") or reward_id)
            stub = {
                **cand,
                "id": task_id,
                "native_id": cand.get("native_id")
                or _resolve_native_opire_id(reward_id),
                "estimated_reward_usd": float(cand.get("reward_usd") or 0),
            }
            skipped = self._mark_task_skipped(
                stub,
                note=f"auto_skip_on_approve:{detail}"[:240],
                reason="repo_unreachable",
            )
            tasks[task_id] = skipped
            self._register_skipped_forever(state, skipped)
            self._save(state)
            self._record_bounty_outcome(skipped, outcome="skip")
            return {
                "ok": True,
                "auto_skipped": True,
                "error": cand.get("repo_probe", {}).get("error_code") or "repo_unreachable",
                "message_ru": (
                    f"Approve → Impossible (repo мёртв): {detail[:180]}. "
                    "Задача снята. 🔍 Researching… берём следующую карточку."
                ),
                "task": skipped,
                "next_action": "scan_next",
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
        # Soft gate: warn but still Approve → Execution (Impossible→Skip if truly blocked later).
        # Hard-block only for unreachable/missing repo (already handled above).
        if not preflight.get("approve_allowed"):
            cand["preflight_soft_warn"] = True
            cand["ceo_note"] = (
                note
                or f"preflight_soft:{preflight.get('action') or 'warn'}"
            )[:240]

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
                {"id": "approve", "title": "Approve (auto GO / CEO REVIEW)", "done": True},
                {"id": "repo_intel", "title": "Stage 1 — Repository Intelligence", "done": False},
                {"id": "planning", "title": "Stage 2 — Planning", "done": False},
                {"id": "research", "title": "Research Agent (needs_external fork)", "done": False},
                {"id": "implementation", "title": "Stage 3 — Implementation", "done": False},
                {"id": "validation", "title": "Stage 4 — Validation", "done": False},
                {"id": "pr_intelligence", "title": "Stage 5 — Draft PR package", "done": False},
                {
                    "id": "ceo_submit",
                    "title": "Submit PR (/claim) — auto when policy allows",
                    "done": False,
                },
                {"id": "review_loop", "title": "Stage 6 — Review Loop", "done": False},
            ],
            "opire_commands": {
                "try": "/try",
                "claim": f"/claim #{cand.get('issue_id') or 'N'}",
            },
        }
        self._save(state)
        approved_task = tasks[task_id]

        from swarm.farm_pipeline_state import bump_pipeline_lifetime

        # Lifetime KPI: Approve always counts; Started counts when auto-exec queues.
        bump_pipeline_lifetime(state, "approved")
        if auto_exec:
            bump_pipeline_lifetime(state, "started")
        self._save(state)
        approved_task = (self._load().get("tasks") or {}).get(task_id) or approved_task

        if not auto_exec:
            return {
                "ok": True,
                "task": approved_task,
                "next_action": "start_execution",
                "auto_started_execution": False,
                "message_ru": (
                    "Approve принят (FARM_AUTO_EXECUTE_ON_APPROVE=0). "
                    "Требуется ваше подтверждение: запустить Execution."
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
            self._mark_pending_execution(task_id, reason="factory_busy")
            task_after = (self._load().get("tasks") or {}).get(task_id) or task_after
            return {
                "ok": True,
                "task": task_after,
                "execution": exec_out,
                "next_action": "monitor_execution",
                "auto_started_execution": False,
                "execution_queued": True,
                "message_ru": (
                    "Approve принят. Линия занята — задача в AUTO-RUN очереди. "
                    "Watchdog сам запустит Clone без кнопки «Запустить Execution»."
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

    def _maybe_auto_retry_healed(self, state: dict[str, Any]) -> None:
        """After zombie heal — resume one approved task without CEO button spam."""
        tasks_map = state.get("tasks") or {}
        if any(str(t.get("status") or "") == "executing" for t in tasks_map.values()):
            return
        for tid, raw in list(tasks_map.items()):
            t = dict(raw or {})
            if not t.get("auto_retry_execution"):
                continue
            if str(t.get("status") or "") not in ("ceo_approved", "executing"):
                continue
            if t.get("execution_error") and not _is_recoverable_execution_error(
                t.get("execution_error")
            ):
                continue
            t["auto_retry_execution"] = False
            t["execution_heal"] = t.get("execution_heal") or "zombie_queued_healed"
            tasks_map[tid] = t
            state["tasks"] = tasks_map
            self._save(state)
            try:
                self.start_execution(str(tid), clone=True)
            except Exception:
                # Keep heal flag so next status tick can try again
                t2 = dict((self._load().get("tasks") or {}).get(tid) or t)
                t2["auto_retry_execution"] = True
                st = self._load()
                st.setdefault("tasks", {})[tid] = t2
                self._save(st)
            return

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
            ost = str(other.get("status") or "")
            # Waiting CEO Submit (patch ready) must NOT block the factory line
            if ost in ("draft_pr", "ceo_review") and _task_has_patch(other):
                continue
            if ost in (
                "executing",
                "draft_pr",
                "ceo_review",
                "pr_submitted",
                "maintainer_review",
                "changes_requested",
            ):
                # Ignore zombies — they only block the factory after backend restart
                if _is_zombie_queued_execution(other, max_age_s=45.0):
                    healed = dict(other)
                    healed["status"] = "ceo_approved"
                    healed["execution_error"] = None
                    healed["execution_heal"] = "zombie_queued_cleared_for_factory"
                    healed["execution"] = {
                        "ok": False,
                        "stage": "queued",
                        "message_ru": "Старая очередь снята — линия свободна.",
                    }
                    healed["updated_at"] = _now()
                    state["tasks"][tid] = healed
                    continue
                self._save(state)
                # Keep THIS task in durable queue (no CEO Start button)
                self._mark_pending_execution(reward_id, reason="factory_busy")
                return {
                    "ok": False,
                    "error": "factory_busy",
                    "message_ru": (
                        f"Уже в работе: {other.get('title') or tid}. "
                        "Текущая задача остаётся в AUTO-RUN очереди "
                        "(pending_execution) — watchdog продолжит без кнопки."
                    ),
                    "blocking_task_id": tid,
                }
        self._save(state)

        # Official Opire /try via GitHub API when token present (no CEO typing)
        try_res = maybe_post_try(task)
        task["try_post"] = try_res

        task["status"] = "executing"
        task["execution_error"] = None
        task["pending_execution"] = False
        task.pop("execution_heal", None)
        # Ensure attempt counter visible even when Approve → start skips drain bump
        if int(task.get("execution_attempts") or 0) <= 0:
            task["execution_attempts"] = 1
        task["updated_at"] = _now()
        # Heartbeat BEFORE blocking clone — UI must not stay on "waiting Clone"
        task["pipeline_state"] = "CLONING"
        task["execution"] = {
            "ok": True,
            "stage": "repo_intelligence",
            "message_ru": "Clone репозитория…",
            "heartbeat_at": _now(),
        }
        state["tasks"][reward_id] = task
        self._save(state)

        engine = FarmExecutionEngine(self._memory)
        report = engine.run_pipeline(task, clone=clone, run_impl=True)
        task = merge_execution_into_task(task, report)
        # Clear one-shot force-fresh after pipeline used it
        task.pop("force_fresh_workspace", None)

        auto_skipped = False
        next_execution: dict[str, Any] | None = None
        auto_submit_result: dict[str, Any] | None = None

        if report.get("ok") and report.get("stage") == "awaiting_ceo_submit" and _task_has_patch(task):
            task["status"] = "draft_pr"
            task["reward_status"] = "draft_pr"
            from swarm.farm_pipeline_state import bump_pipeline_lifetime

            bump_pipeline_lifetime(state, "draft_pr")
            if _farm_auto_submit_enabled():
                msg = (
                    report.get("ready_for_ceo", {}).get("message_ru")
                    or "Draft PR Ready — AUTO-RUN отправляет PR (/claim)."
                )
            else:
                msg = (
                    report.get("ready_for_ceo", {}).get("message_ru")
                    or (
                        "Draft PR Ready — патч есть. "
                        "FARM_AUTO_SUBMIT_PR=0: нужно CEO Submit."
                    )
                )
        else:
            # Keep failed bounty durable — do not mask as "Impossible" / completed
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
            task = self._mark_execution_failed(
                task,
                detail=str(detail),
                reason=reason,
                stage=str(report.get("stage") or "failed"),
                error_code=str(report.get("error") or reason),
            )
            auto_skipped = False  # not skipped_forever — stays EXECUTION_FAILED
            msg = (
                f"EXECUTION_FAILED · task={reward_id} · stage={task.get('execution', {}).get('stage')} · "
                f"error={str(detail)[:180]} · retry={task.get('execution_attempts')}/3 · "
                f"next_retry={task.get('next_retry_at') or '—'} · "
                f"blocker={reason}. "
                "Не считается выполненной. API Farm / Revenue Farm не затрагиваются."
            )
            next_execution = None
            if _farm_bounty_advance_on_fail():
                next_execution = self._auto_advance_to_next(depth=_auto_depth)
                if next_execution and next_execution.get("message_ru"):
                    msg = (
                        f"{msg} → FARM_BOUNTY_ADVANCE_ON_FAIL=1: "
                        f"{next_execution['message_ru']}"
                    )
            else:
                msg = (
                    f"{msg} Следующая bounty НЕ взята "
                    "(FARM_BOUNTY_ADVANCE_ON_FAIL=0)."
                )

        state = self._load()
        state.setdefault("tasks", {})[reward_id] = task
        self._register_skipped_forever(state, task) if auto_skipped else None
        self._save(state)

        # AUTO-RUN: Submit PR without CEO button when policy allows
        if (
            not auto_skipped
            and _farm_auto_submit_enabled()
            and str(task.get("status") or "") == "draft_pr"
            and _task_has_patch(task)
            and not task.get("auto_submit_done")
        ):
            try:
                auto_submit_result = self.ceo_submit_pr(
                    reward_id,
                    note="auto_submit_after_draft",
                    live=not bool(os.environ.get("PYTEST_CURRENT_TEST")),
                )
                if auto_submit_result.get("ok"):
                    task = (
                        (self._load().get("tasks") or {}).get(reward_id) or task
                    )
                    msg = f"{msg} → Auto-Submit PR выполнен."
                else:
                    msg = (
                        f"{msg} → Auto-Submit отложен: "
                        f"{auto_submit_result.get('error') or 'retry'}"
                    )
            except Exception as exc:  # noqa: BLE001
                auto_submit_result = {"ok": False, "error": str(exc)[:160]}
                msg = f"{msg} → Auto-Submit error (watchdog retry)."

        return {
            "ok": bool(report.get("ok") and _task_has_patch(task)),
            "task": (self._load().get("tasks") or {}).get(reward_id) or task,
            "execution": report,
            "stages": list(EXECUTION_STAGES),
            "message_ru": msg,
            "auto_skipped": auto_skipped,
            "next_execution": next_execution,
            "auto_submit": auto_submit_result,
            "ceo_submit_required": bool(
                _task_has_patch(task) and not _farm_auto_submit_enabled()
            ),
            "auto_submit_forbidden": not _farm_auto_submit_enabled(),
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
                        "👀 Waiting for maintainer… после merge — Sync (ID не вводить)."
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
