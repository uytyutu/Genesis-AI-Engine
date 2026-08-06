"""ROI Score — worth doing, not only can we do it.

usd_per_hour = reward / estimated_hours
Stars map the CEO-facing “is this profitable?” signal.
"""

from __future__ import annotations

from typing import Any


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def estimate_minutes(row: dict[str, Any] | None = None, *, hours: float | None = None) -> float:
    if hours is not None:
        h = max(0.05, hours)
    else:
        h = max(0.05, _f((row or {}).get("estimated_hours"), 1.0))
    return round(h * 60.0, 1)


def usd_per_hour(*, reward_usd: float, estimated_hours: float) -> float:
    hours = max(0.05, float(estimated_hours or 0.05))
    return round(float(reward_usd or 0) / hours, 2)


def stars_from_usd_per_hour(rate: float) -> int:
    """5★ docs@$20/15m (~$80/h) · 4★ CI@$40/45m · 2★ React@$60/8h."""
    if rate >= 80:
        return 5
    if rate >= 40:
        return 4
    if rate >= 20:
        return 3
    if rate >= 10:
        return 2
    return 1


def stars_label(stars: int) -> str:
    n = max(1, min(5, int(stars)))
    return "⭐" * n


def compute_roi(row: dict[str, Any]) -> dict[str, Any]:
    reward = _f(row.get("reward_usd") or row.get("estimated_reward_usd"))
    hours = max(0.05, _f(row.get("estimated_hours"), 1.0))
    minutes = estimate_minutes(hours=hours)
    rate = usd_per_hour(reward_usd=reward, estimated_hours=hours)
    stars = stars_from_usd_per_hour(rate)
    # Soft confidence penalty: low confidence cuts effective ROI for ranking
    conf = _f(row.get("overall_confidence_pct") or row.get("confidence_pct"), 50.0)
    conf_factor = max(0.35, min(1.0, conf / 100.0))
    effective_rate = round(rate * conf_factor, 2)
    rank_score = round(effective_rate, 2)
    return {
        "roi_stars": stars,
        "roi_label": stars_label(stars),
        "roi_usd_per_hour": rate,
        "roi_effective_usd_per_hour": effective_rate,
        "roi_rank_score": rank_score,
        "estimated_minutes": minutes,
        "roi_note_ru": "ROI = reward ÷ время (с учётом confidence). Не REAL payout.",
    }


def apply_roi(row: dict[str, Any]) -> dict[str, Any]:
    out = dict(row)
    out.update(compute_roi(out))
    return out
