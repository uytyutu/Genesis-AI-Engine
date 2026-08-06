"""Bounty Learning Ledger — win/lose facts after each Opire cycle.

Separate from micro_farm adapter learning (FarmLearningLedger).
After ~20–30 closed bounties, Farm can prefer patterns that paid.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LEDGER_FILENAME = "farm_bounty_learning.jsonl"
MIN_CLOSED_FOR_STATS = 20


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _hours_between(start: str | None, end: str | None) -> float | None:
    if not start or not end:
        return None
    try:
        a = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        b = datetime.fromisoformat(str(end).replace("Z", "+00:00"))
        return round(max(0.0, (b - a).total_seconds() / 3600.0), 2)
    except (TypeError, ValueError):
        return None


def infer_why_won(task: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    langs = [str(x).lower() for x in (task.get("languages") or [])]
    if langs:
        reasons.append(f"langs:{','.join(langs[:4])}")
    if task.get("bot_installed"):
        reasons.append("opire_bot_installed")
    if int(task.get("competitors") or 0) == 0:
        reasons.append("no_competitors")
    if _f(task.get("overall_confidence_pct")) >= 70:
        reasons.append("high_confidence")
    if _f(task.get("estimated_hours"), 99) <= 2:
        reasons.append("small_scope")
    if not task.get("had_changes_requested"):
        reasons.append("first_pass_merge")
    else:
        reasons.append("survived_review_loop")
    return reasons or ["payout_confirmed"]


def infer_why_lost(task: dict[str, Any], *, outcome: str) -> list[str]:
    reasons: list[str] = []
    skip = str(task.get("skip_reason") or "")
    if skip:
        reasons.append(skip)
    note = str(task.get("ceo_note") or "")
    if note and note not in reasons:
        reasons.append(note[:120])
    blockers = [str(b) for b in (task.get("blockers") or [])]
    reasons.extend(blockers[:4])
    err = str(task.get("execution_error") or (task.get("execution") or {}).get("error") or "")
    if err:
        reasons.append(f"execution:{err[:80]}")
    if outcome == "skip" and not reasons:
        reasons.append("ceo_skip")
    if outcome == "lose" and not reasons:
        reasons.append("failed_before_payout")
    return reasons[:8]


class FarmBountyLearningLedger:
    def __init__(self, memory_dir: Path) -> None:
        self._path = Path(memory_dir) / LEDGER_FILENAME

    def append_from_task(
        self,
        task: dict[str, Any],
        *,
        outcome: str,
        extra: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        outcome = (outcome or "").strip().lower()
        if outcome not in ("win", "lose", "skip"):
            outcome = "lose"

        reviews = 0
        if task.get("had_changes_requested"):
            reviews = max(1, int(task.get("review_rounds") or 1))

        earned = _f(task.get("payout_confirmed_usd")) if outcome == "win" else 0.0
        est_h = _f(task.get("estimated_hours"), 1.0)
        actual_h = _hours_between(
            str(task.get("approved_at") or "") or None,
            str(task.get("updated_at") or "") or None,
        )

        from swarm.farm_roi_score import compute_roi

        roi = compute_roi(task)
        entry: dict[str, Any] = {
            "at": _now(),
            "outcome": outcome,
            "task_id": str(task.get("id") or ""),
            "platform": str(task.get("platform") or "opire"),
            "title": str(task.get("title") or "")[:160],
            "repository": str(task.get("repository") or ""),
            "languages": [str(x).lower() for x in (task.get("languages") or [])][:8],
            "reward_usd": _f(task.get("reward_usd") or task.get("estimated_reward_usd")),
            "earned_usd": earned,
            "estimated_hours": est_h,
            "actual_hours": actual_h,
            "reviews": reviews,
            "roi_stars": roi.get("roi_stars"),
            "why_won": infer_why_won(task) if outcome == "win" else [],
            "why_lost": infer_why_lost(task, outcome=outcome) if outcome != "win" else [],
            "status": str(task.get("status") or ""),
        }
        if extra:
            entry["extra"] = extra

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return entry

    def read_recent(self, *, limit: int = 40) -> list[dict[str, Any]]:
        if not self._path.is_file():
            return []
        lines = [ln for ln in self._path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        out: list[dict[str, Any]] = []
        for line in lines[-limit:]:
            try:
                row = json.loads(line)
                if isinstance(row, dict):
                    out.append(row)
            except json.JSONDecodeError:
                continue
        return out

    def summary(self) -> dict[str, Any]:
        rows = self.read_recent(limit=500)
        wins = [r for r in rows if r.get("outcome") == "win"]
        losses = [r for r in rows if r.get("outcome") in ("lose", "skip")]
        closed = len(wins) + len(losses)

        win_reasons: Counter[str] = Counter()
        lose_reasons: Counter[str] = Counter()
        lang_wins: Counter[str] = Counter()
        lang_demand: Counter[str] = Counter()

        earned_total = 0.0
        time_sum = 0.0
        time_n = 0
        review_sum = 0

        for r in wins:
            earned_total += _f(r.get("earned_usd"))
            for w in r.get("why_won") or []:
                win_reasons[str(w)] += 1
            for lg in r.get("languages") or []:
                lang_wins[str(lg)] += 1
                lang_demand[str(lg)] += 1
            ah = r.get("actual_hours")
            if ah is not None:
                time_sum += _f(ah)
                time_n += 1
            review_sum += int(r.get("reviews") or 0)

        for r in losses:
            for w in r.get("why_lost") or []:
                lose_reasons[str(w)] += 1
            for lg in r.get("languages") or []:
                lang_demand[str(lg)] += 1

        ready = closed >= MIN_CLOSED_FOR_STATS
        return {
            "ok": True,
            "closed": closed,
            "wins": len(wins),
            "losses": len(losses),
            "earned_usd": round(earned_total, 2),
            "avg_actual_hours_win": round(time_sum / time_n, 2) if time_n else None,
            "avg_reviews_win": round(review_sum / max(1, len(wins)), 2) if wins else None,
            "why_won": [{"reason": k, "count": v} for k, v in win_reasons.most_common(12)],
            "why_lost": [{"reason": k, "count": v} for k, v in lose_reasons.most_common(12)],
            "top_win_languages": [
                {"name": k, "wins": v} for k, v in lang_wins.most_common(8)
            ],
            "recent": rows[-12:][::-1],
            "min_closed_for_stats": MIN_CLOSED_FOR_STATS,
            "stats_ready": ready,
            "note_ru": (
                "Learning Ledger копит факты после каждого bounty. "
                f"После {MIN_CLOSED_FOR_STATS} закрытых задач приоритет будет на своей статистике."
                if not ready
                else "Достаточно данных — можно усиливать приоритет по win-паттернам."
            ),
            "north_star_ru": "Один confirmed payout важнее десятков новых фич.",
        }
