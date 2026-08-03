"""Opire Farm — Semi-Auto bounty scanner via official Opire public API + GitHub.

Official flow only (docs.opire.dev):
  /try on issue → implement → PR with /claim #N → maintainer merge → Opire payout

REAL income only after payout confirmation (Reward Protection).
Never auto-submit without CEO Approve + CEO Submit PR.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

OPIRE_REWARDS_URL = "https://api.opire.dev/rewards"
STATE_FILE = "opire_farm_state.json"

# Virtus-capable stack for first Semi-Auto slice
SUPPORTED_LANGS = frozenset(
    {
        "python",
        "typescript",
        "javascript",
        "html",
        "css",
        "go",
        "php",
    }
)

HARD_REJECT_TITLE = re.compile(
    r"captcha|hcaptcha|recaptcha|anti.?bot|multi.?account|tos.?bypass",
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


def fetch_opire_rewards(*, timeout: float = 25.0) -> list[dict[str, Any]]:
    req = urllib.request.Request(
        OPIRE_REWARDS_URL,
        headers={"Accept": "application/json", "User-Agent": "VirtusCore-FarmEngine/1.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, list):
        return []
    return [x for x in data if isinstance(x, dict)]


def score_reward(raw: dict[str, Any]) -> dict[str, Any]:
    """Confidence Engine — heuristic only (no auto-execution)."""
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

    blockers: list[str] = []
    if HARD_REJECT_TITLE.search(title):
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
        if "python" in supported_hit or "typescript" in supported_hit:
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

    low = title.lower()
    if re.search(r"\bfix\b|bug|race|pagination|leak|stale|error|typo", low):
        conf += 8
        acceptance += 6
        est_hours *= 0.85
    if re.search(r"rewrite|migrate|wayland|rcs support|web platform export", low):
        conf -= 18
        acceptance -= 12
        est_hours *= 1.8
        blockers.append("large_feature_risk")

    conf = max(5.0, min(97.0, round(conf, 1)))
    acceptance = max(5.0, min(95.0, round(acceptance, 1)))
    overall = round(0.55 * conf + 0.45 * acceptance, 1)

    recommendation = "TAKE" if overall >= DEFAULT_CONFIDENCE_THRESHOLD and not blockers else "SKIP"
    if blockers:
        recommendation = "SKIP"

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
        "reward_usd": reward,
        "reward_currency": "USD",
        "estimated_reward_usd": reward,  # never REAL
        "bot_installed": bot,
        "competitors": n_comp,
        "confidence_pct": conf,
        "acceptance_pct": acceptance,
        "overall_confidence_pct": overall,
        "estimated_hours": round(est_hours, 1),
        "required_capabilities": supported_hit or ["manual_review"],
        "tests_available": "unknown",
        "risk": "low" if overall >= 85 else ("medium" if overall >= 70 else "high"),
        "recommendation": recommendation,
        "blockers": blockers,
        "official_next_steps_ru": [
            "CEO Approve",
            "Комментарий /try на Issue (официальный Opire)",
            "Ветка + реализация + тесты",
            "Draft PR → CEO Submit PR с /claim #<issue>",
            "Ждать merge + Opire payout (не REAL до подтверждения)",
        ],
    }


def scan_opire(
    *,
    threshold: float = DEFAULT_CONFIDENCE_THRESHOLD,
    limit: int = 40,
    fetch_fn=None,
) -> dict[str, Any]:
    fetch = fetch_fn or fetch_opire_rewards
    try:
        raw_list = fetch()
        err = None
    except Exception as exc:  # noqa: BLE001 — surface to CEO panel
        return {
            "ok": False,
            "error": str(exc),
            "candidates": [],
            "filtered_out": 0,
            "scanned": 0,
            "threshold": threshold,
            "at": _now(),
        }

    scored = [score_reward(r) for r in raw_list]
    take = [
        s
        for s in scored
        if s["recommendation"] == "TAKE" and s["overall_confidence_pct"] >= threshold
    ]
    take.sort(key=lambda x: (-x["overall_confidence_pct"], -x["reward_usd"]))
    return {
        "ok": True,
        "error": err,
        "source": OPIRE_REWARDS_URL,
        "official_flow": "/try → PR /claim → merge → Opire payout",
        "scanned": len(scored),
        "filtered_out": len(scored) - len(take),
        "threshold": threshold,
        "candidates": take[:limit],
        "all_preview": scored[:12],
        "at": _now(),
        "finance_law_ru": (
            "Estimated ≠ REAL. В REAL Profit Ledger только после payout_confirmed."
        ),
    }


class OpireFarmEngine:
    def __init__(self, memory_dir: Path) -> None:
        self._memory = Path(memory_dir)
        self._memory.mkdir(parents=True, exist_ok=True)
        self._path = self._memory / STATE_FILE

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

    def panel(self, *, force_scan: bool = True) -> dict[str, Any]:
        state = self._load()
        scan = scan_opire() if force_scan else {
            "ok": True,
            "candidates": [],
            "scanned": 0,
            "filtered_out": 0,
            "threshold": DEFAULT_CONFIDENCE_THRESHOLD,
        }
        tasks = list((state.get("tasks") or {}).values())
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

        return {
            "ok": True,
            "mode": "semi_auto",
            "engine": "opire_farm",
            "separate_from": "commercial_engine",
            "workflow_ru": [
                "Scanner (api.opire.dev)",
                "Confidence Engine",
                "CEO Approve / Skip",
                "Official /try + work + Draft PR",
                "CEO Submit PR (/claim)",
                "Monitor review + reward",
                "REAL только после payout confirmed",
            ],
            "funnel": {
                "found": scanned,
                "analyzed": scanned,
                "high_confidence": high,
                "ceo_approved": approved,
                "executed": executed,
                "pr_submitted": pr_submitted,
                "pr_merged": pr_merged,
                "paid": paid,
                "total_confirmed_usd": round(real, 2),
                "bottleneck_hint_ru": _bottleneck_hint(
                    scanned, high, approved, executed, pr_submitted, pr_merged, paid
                ),
            },
            "scan": scan,
            "active_tasks": [t for t in tasks if t.get("status") not in ("completed", "skipped")],
            "history": tasks[:30],
            "ledger": {
                "estimated_usd": round(estimated, 2),
                "real_confirmed_usd": round(real, 2),
                "note_ru": "Estimated и REAL всегда разделены. REAL = только payout_confirmed.",
            },
            "reward_states": list(REWARD_STATES),
        }

    def decide(self, reward_id: str, decision: str, *, note: str = "") -> dict[str, Any]:
        decision = (decision or "").strip().lower()
        if decision not in ("approve", "skip", "go"):
            return {"ok": False, "error": "decision must be approve|skip"}
        if decision == "go":
            decision = "approve"

        scan = scan_opire(limit=80)
        cand = next(
            (c for c in (scan.get("candidates") or []) + (scan.get("all_preview") or []) if c.get("id") == reward_id),
            None,
        )
        if cand is None and decision == "approve":
            # Allow approve from full rescan without threshold filter
            try:
                raw = next((r for r in fetch_opire_rewards() if str(r.get("id")) == reward_id), None)
            except Exception as exc:  # noqa: BLE001
                return {"ok": False, "error": f"opire_fetch:{exc}"}
            if raw:
                cand = score_reward(raw)
        if cand is None:
            return {"ok": False, "error": "reward_not_found"}

        state = self._load()
        tasks = state.setdefault("tasks", {})
        if decision == "skip":
            tasks[reward_id] = {
                **cand,
                "status": "skipped",
                "ceo_note": note,
                "updated_at": _now(),
                "pr_id": None,
                "merge_status": None,
                "reward_status": "skipped",
                "withdrawal_status": None,
                "payment_confirmation_id": None,
                "real_income": False,
            }
            self._save(state)
            return {"ok": True, "task": tasks[reward_id], "message_ru": "Пропущено"}

        tasks[reward_id] = {
            **cand,
            "status": "ceo_approved",
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
            "execution_checklist": [
                {"id": "try", "title": "Оставить /try на Issue", "done": False},
                {"id": "branch", "title": "Создать ветку", "done": False},
                {"id": "implement", "title": "Реализация + тесты", "done": False},
                {"id": "draft_pr", "title": "Draft PR (ещё не submit)", "done": False},
                {"id": "ceo_submit", "title": "CEO Submit PR с /claim", "done": False},
            ],
            "opire_commands": {
                "try": "/try",
                "claim": f"/claim #{cand.get('issue_id') or 'N'}",
            },
        }
        self._save(state)
        return {
            "ok": True,
            "task": tasks[reward_id],
            "message_ru": (
                "Approve принят. Дальше официальный Opire: /try → работа → Draft PR. "
                "Submit PR — только после вашей кнопки. REAL — только после payout."
            ),
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

        state = self._load()
        task = (state.get("tasks") or {}).get(reward_id)
        if not task:
            return {"ok": False, "error": "task_not_found"}

        task["status"] = status
        task["updated_at"] = _now()
        if note:
            task["ceo_note"] = note
        if pr_id:
            task["pr_id"] = pr_id
        if pr_url:
            task["pr_url"] = pr_url
        if payment_confirmation_id:
            task["payment_confirmation_id"] = payment_confirmation_id

        # Reward Protection — never REAL without confirmation id + confirmed state
        if status in REAL_INCOME_STATES:
            if not task.get("payment_confirmation_id"):
                return {
                    "ok": False,
                    "error": "payout_confirmation_required",
                    "message_ru": (
                        "Нельзя отметить REAL без Payment Confirmation ID платформы."
                    ),
                }
            task["real_income"] = True
            task["payout_confirmed_usd"] = float(
                payout_usd if payout_usd is not None else task.get("estimated_reward_usd") or 0
            )
            task["reward_status"] = "payout_confirmed"
            task["withdrawal_status"] = "complete"
        else:
            task["real_income"] = False
            task["reward_status"] = status

        if status == "draft_pr":
            for step in task.get("execution_checklist") or []:
                if step.get("id") in ("try", "branch", "implement", "draft_pr"):
                    step["done"] = True
        if status == "pr_submitted":
            for step in task.get("execution_checklist") or []:
                step["done"] = True

        state["tasks"][reward_id] = task
        self._save(state)
        return {"ok": True, "task": task}
