"""Farm scan analytics — diagnose funnel without new execution code."""

from __future__ import annotations

from collections import Counter
from typing import Any

from swarm.farm_virtus_capabilities import VIRTUS_FARM_CAPABILITIES


def _langs(row: dict[str, Any]) -> list[str]:
    raw = row.get("languages") or row.get("programmingLanguages") or []
    if isinstance(raw, str):
        raw = [raw]
    out: list[str] = []
    for x in raw:
        s = str(x or "").strip().lower()
        if s:
            out.append(s)
    return out


def _reward(row: dict[str, Any]) -> float:
    try:
        return float(row.get("reward_usd") or row.get("reward") or 0)
    except (TypeError, ValueError):
        return 0.0


def _conf(row: dict[str, Any]) -> float:
    try:
        return float(row.get("overall_confidence_pct") or row.get("confidence_pct") or 0)
    except (TypeError, ValueError):
        return 0.0


def build_scan_analytics(
    pool: list[dict[str, Any]],
    *,
    threshold: float = 60.0,
    supported_langs: frozenset[str] | None = None,
) -> dict[str, Any]:
    """Aggregate languages, reject reasons, potential reward, capability coverage."""
    supported = supported_langs or VIRTUS_FARM_CAPABILITIES
    lang_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()

    high_usd = 0.0
    mid_usd = 0.0
    low_usd = 0.0
    high_n = mid_n = low_n = 0

    demand_langs: Counter[str] = Counter()

    for row in pool:
        langs = _langs(row)
        for lg in langs or ["(unspecified)"]:
            lang_counter[lg] += 1
            demand_langs[lg] += 1

        conf = _conf(row)
        reward = _reward(row)
        blockers = [str(b) for b in (row.get("blockers") or [])]
        reasons = [str(r) for r in (row.get("reject_reasons") or [])]
        rec = str(row.get("recommendation") or "")

        tags = list(dict.fromkeys(blockers + reasons))
        if not tags:
            if conf < threshold and rec != "TAKE":
                tags.append("confidence_low")
            elif rec == "SKIP":
                tags.append("skipped")
            elif rec == "REVIEW":
                tags.append("review_band")
        for t in tags:
            # Normalize common labels for CEO readability
            key = t
            if t == "unsupported_language":
                key = "capability_missing"
            elif t.startswith("below_threshold"):
                key = "confidence_low"
            elif t in {"repo_unreachable", "missing_repo"}:
                key = "dead_repo"
            elif t == "repo_auth_required":
                key = "repo_auth"
            reason_counter[key] += 1

        if conf >= threshold and not blockers and rec != "SKIP":
            high_usd += reward
            high_n += 1
        elif conf >= 40:
            mid_usd += reward
            mid_n += 1
        else:
            low_usd += reward
            low_n += 1

    # Capability coverage: share of demanded langs we claim to support
    coverage_rows: list[dict[str, Any]] = []
    for lg, count in demand_langs.most_common(16):
        if lg == "(unspecified)":
            continue
        covered = lg in supported or any(
            lg in s or s in lg for s in supported if len(s) > 2
        )
        # Map aliases
        aliases = {
            "ts": "typescript",
            "js": "javascript",
            "next": "nextjs",
            "nodejs": "javascript",
        }
        canon = aliases.get(lg, lg)
        if canon in supported:
            covered = True
        pct = 100 if covered else 0
        lost = 0 if covered else count
        coverage_rows.append(
            {
                "capability": lg,
                "demand": count,
                "covered": covered,
                "coverage_pct": pct,
                "lost_bounties": lost,
            }
        )

    covered_demand = sum(r["demand"] for r in coverage_rows if r["covered"])
    total_demand = sum(r["demand"] for r in coverage_rows) or 1

    from swarm.farm_roi_score import apply_roi

    ranked = sorted(
        (apply_roi(dict(r)) for r in pool),
        key=lambda x: -float(x.get("roi_rank_score") or 0),
    )
    top_roi = [
        {
            "title": str(r.get("title") or r.get("id") or "")[:80],
            "reward_usd": float(r.get("reward_usd") or 0),
            "estimated_minutes": r.get("estimated_minutes"),
            "roi_stars": r.get("roi_stars"),
            "roi_label": r.get("roi_label"),
            "roi_usd_per_hour": r.get("roi_usd_per_hour"),
        }
        for r in ranked[:8]
        if float(r.get("reward_usd") or 0) > 0
    ]

    return {
        "ok": True,
        "pool_size": len(pool),
        "languages": [
            {"name": name, "count": count}
            for name, count in lang_counter.most_common(20)
        ],
        "reject_reasons": [
            {"reason": name, "count": count}
            for name, count in reason_counter.most_common(20)
        ],
        "potential_reward": {
            "high": {"label": "High confidence", "usd": round(high_usd, 2), "count": high_n},
            "medium": {"label": "Medium", "usd": round(mid_usd, 2), "count": mid_n},
            "low": {"label": "Low", "usd": round(low_usd, 2), "count": low_n},
            "total_usd": round(high_usd + mid_usd + low_usd, 2),
            "note_ru": "Potential ≠ REAL. Это рынок в скане, не подтверждённый доход.",
        },
        "capability_coverage": {
            "rows": coverage_rows,
            "coverage_pct": round(100.0 * covered_demand / total_demand),
            "supported": sorted(supported),
            "note_ru": "Какие bounty теряем из‑за пробелов в capability.",
        },
        "top_roi": top_roi,
        "north_star_ru": "Цель Farm: первый подтверждённый payout — не новые фичи.",
    }
