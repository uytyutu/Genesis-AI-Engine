"""Candidate scoring — no evidence ⇒ lower score (no fake demand)."""

from __future__ import annotations

from typing import Any


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, float(v)))


def score_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Compute demand / competition / implementation / monetization / total."""
    evidence = candidate.get("evidence") or []
    has_evidence = bool(evidence)
    evidence_penalty = 0.0 if has_evidence else 25.0

    demand = _clamp(float(candidate.get("demand_score") or 0))
    competition = _clamp(float(candidate.get("competition_score") or 0))
    implementation = _clamp(float(candidate.get("implementation_score") or 0))
    monetization = _clamp(float(candidate.get("monetization_score") or 0))

    # Competition is inverted: higher competition score means more crowded → lower weight.
    competition_fit = _clamp(100.0 - competition)

    if not has_evidence:
        demand = _clamp(demand - evidence_penalty)
        monetization = _clamp(monetization - evidence_penalty * 0.6)

    total = round(
        demand * 0.30
        + competition_fit * 0.15
        + implementation * 0.25
        + monetization * 0.30,
        2,
    )
    operating = float(candidate.get("operating_cost") or 0)
    price = candidate.get("suggested_price") or {}
    pro = float(price.get("PRO") or price.get("pro") or 0)
    expected_margin = round(max(0.0, pro * 0.75 - operating), 2) if pro else 0.0

    return {
        "demand_score": round(demand, 2),
        "competition_score": round(competition, 2),
        "implementation_score": round(implementation, 2),
        "monetization_score": round(monetization, 2),
        "total_score": total,
        "expected_margin": expected_margin,
        "evidence_count": len(evidence) if isinstance(evidence, list) else 0,
        "evidence_penalty_applied": evidence_penalty > 0,
    }


def rank_candidates(rows: list[dict[str, Any]], *, top_n: int = 5) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    for row in rows:
        s = score_candidate(row)
        scored.append({**row, **s})
    scored.sort(key=lambda r: float(r.get("total_score") or 0), reverse=True)
    return scored[: max(1, int(top_n))]
