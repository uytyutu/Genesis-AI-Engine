"""Profit + opportunity score — estimates only, never REAL revenue."""

from __future__ import annotations

from typing import Any

from swarm.money_hunter.models import (
    FIRST_MONEY_BUDGET_MAX,
    FIRST_MONEY_BUDGET_MIN,
    SPEND_BANDS,
    empty_economics,
)

# Rough EUR/USD for fee display only (not ledger truth).
_USD_TO_EUR = 0.92

PLATFORM_FEE_RATES: dict[str, float] = {
    "manual": 0.0,
    "upwork_manual": 0.10,
    "fiverr_manual": 0.20,
    "malt_manual": 0.10,
    "freelance_de_manual": 0.05,
}


def _f(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def spend_band_for_cost(max_cost_eur: float) -> str:
    c = max(0.0, _f(max_cost_eur))
    for lo, hi, label in SPEND_BANDS:
        if lo <= c < hi:
            return label
    return "ceo_explicit"


def to_eur(amount: float, currency: str) -> float:
    cur = (currency or "EUR").strip().upper()
    amt = _f(amount)
    if cur in ("EUR", "€"):
        return amt
    if cur in ("USD", "US$", "$"):
        return amt * _USD_TO_EUR
    if cur in ("GBP", "£"):
        return amt * 1.17
    return amt


def estimate_costs(
    *,
    expected_revenue_eur: float,
    estimated_hours: float,
    automation_percent: float,
    source: str,
) -> dict[str, float]:
    hours = max(0.2, _f(estimated_hours, 2.0))
    auto = min(100.0, max(0.0, _f(automation_percent, 50.0))) / 100.0
    human_hours = hours * (1.0 - auto)
    # Toloka as requester spend estimate (~€4/h microtasks) — SPEND not income.
    toloka = round(human_hours * 4.0, 2)
    ai = round(max(0.5, hours * 0.8 * auto), 2)
    infra = 0.5
    internal = round(max(0.0, human_hours * 12.0 * 0.25), 2)  # light oversight
    fee_rate = PLATFORM_FEE_RATES.get((source or "manual").strip().lower(), 0.05)
    platform_fee = round(expected_revenue_eur * fee_rate, 2)
    risk_reserve = round(expected_revenue_eur * 0.05, 2)
    return {
        "toloka_cost": toloka,
        "ai_cost": ai,
        "infrastructure_cost": infra,
        "estimated_internal_cost": internal,
        "platform_fee": platform_fee,
        "risk_reserve": risk_reserve,
    }


def compute_economics(payload: dict[str, Any]) -> dict[str, Any]:
    eco = empty_economics()
    currency = str(payload.get("currency") or "EUR").upper()
    bmin = to_eur(_f(payload.get("budget_min")), currency)
    bmax = to_eur(_f(payload.get("budget_max") or payload.get("budget_min")), currency)
    if bmax < bmin:
        bmax = bmin
    # Prefer mid-budget as expected revenue when range given.
    expected_revenue = round((bmin + bmax) / 2.0 if bmax > 0 else bmin, 2)
    if expected_revenue <= 0 and payload.get("expected_revenue") is not None:
        expected_revenue = to_eur(_f(payload.get("expected_revenue")), currency)

    hours = _f(payload.get("estimated_hours"), 0.0)
    auto = _f(payload.get("automation_percent"), 0.0)
    if hours <= 0:
        # Heuristic from description length / budget.
        desc = str(payload.get("description") or "")
        hours = max(1.0, min(40.0, 1.2 + len(desc) / 800.0 + expected_revenue / 80.0))
    if auto <= 0:
        auto = _guess_automation(str(payload.get("description") or ""), str(payload.get("title") or ""))

    source = str(payload.get("source") or "manual").strip().lower()
    costs = estimate_costs(
        expected_revenue_eur=expected_revenue,
        estimated_hours=hours,
        automation_percent=auto,
        source=source,
    )
    expected_cost = round(sum(costs.values()), 2)
    expected_profit = round(expected_revenue - expected_cost, 2)
    margin = (
        round(100.0 * expected_profit / expected_revenue, 1) if expected_revenue > 0 else 0.0
    )

    success = _success_probability(
        expected_revenue=expected_revenue,
        auto=auto,
        hours=hours,
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
    )
    risk = round(max(0.0, min(100.0, 100.0 - success * 100.0 + (10 if hours > 8 else 0))), 1)
    score = opportunity_score(
        expected_profit=expected_profit,
        expected_revenue=expected_revenue,
        success_probability=success,
        automation_percent=auto,
        risk_score=risk,
        hours=hours,
    )

    decision, rejects = qualify(
        expected_revenue=expected_revenue,
        expected_profit=expected_profit,
        margin=margin,
        success=success,
        hours=hours,
        title=str(payload.get("title") or ""),
        description=str(payload.get("description") or ""),
        first_money=bool(payload.get("first_money_mode", True)),
    )

    eco.update(
        {
            "budget_min": round(bmin, 2),
            "budget_max": round(bmax, 2),
            "currency": "EUR",
            "expected_revenue": expected_revenue,
            "estimated_hours": round(hours, 2),
            "automation_percent": round(auto, 1),
            **costs,
            "expected_cost": expected_cost,
            "expected_profit": expected_profit,
            "expected_margin_percent": margin,
            "risk_score": risk,
            "success_probability": round(success * 100.0, 1),
            "opportunity_score": score,
            "spend_band": spend_band_for_cost(expected_cost),
            "decision": decision,
            "reject_reasons": rejects,
            "human_summary": human_summary(
                expected_revenue=expected_revenue,
                auto=auto,
                toloka=costs["toloka_cost"],
                ai=costs["ai_cost"],
                hours=hours,
                profit=expected_profit,
                success_pct=round(success * 100.0, 1),
                score=score,
            ),
        }
    )
    return eco


def _guess_automation(description: str, title: str) -> float:
    text = f"{title}\n{description}".lower()
    if any(
        w in text
        for w in (
            "research",
            "recherche",
            "data clean",
            "classify",
            "verification",
            "qa",
            "scraping public",
            "csv",
            "spreadsheet",
            "market research",
            "competitor",
        )
    ):
        return 82.0
    if any(w in text for w in ("design", "video", "voice", "on-site", "vor ort", "meeting")):
        return 25.0
    if any(w in text for w in ("website", "wordpress", "shopify", "landing")):
        return 55.0
    return 60.0


def _success_probability(
    *,
    expected_revenue: float,
    auto: float,
    hours: float,
    title: str,
    description: str,
) -> float:
    text = f"{title}\n{description}".lower()
    p = 0.55
    if FIRST_MONEY_BUDGET_MIN <= expected_revenue <= FIRST_MONEY_BUDGET_MAX:
        p += 0.12
    if auto >= 70:
        p += 0.12
    if hours <= 3:
        p += 0.08
    elif hours > 12:
        p -= 0.15
    if any(w in text for w in ("asap", "urgent", "heute", "tomorrow", "1 hour")):
        p -= 0.1
    if any(
        w in text
        for w in (
            "captcha",
            "bypass",
            "fake review",
            "fake engagement",
            "spam",
            "multi-account",
            "credential",
        )
    ):
        p = 0.05
    return max(0.05, min(0.95, p))


def opportunity_score(
    *,
    expected_profit: float,
    expected_revenue: float,
    success_probability: float,
    automation_percent: float,
    risk_score: float,
    hours: float,
) -> float:
    """Score 0–100: profit × success × automation × fit × feasibility × risk_factor."""
    if expected_revenue <= 0:
        return 0.0
    profit_score = max(0.0, min(1.0, expected_profit / max(40.0, expected_revenue)))
    automation_score = min(1.0, max(0.0, automation_percent / 100.0))
    client_fit = 1.0 if FIRST_MONEY_BUDGET_MIN <= expected_revenue <= 300 else 0.7
    feasibility = 1.0 if hours <= 6 else (0.7 if hours <= 16 else 0.4)
    risk_factor = max(0.2, 1.0 - (risk_score / 120.0))
    raw = (
        profit_score
        * success_probability
        * (0.5 + 0.5 * automation_score)
        * client_fit
        * feasibility
        * risk_factor
    )
    return round(max(0.0, min(100.0, raw * 140.0)), 1)


def qualify(
    *,
    expected_revenue: float,
    expected_profit: float,
    margin: float,
    success: float,
    hours: float,
    title: str,
    description: str,
    first_money: bool,
) -> tuple[str, list[str]]:
    rejects: list[str] = []
    text = f"{title}\n{description}".lower()
    forbidden = (
        "captcha bypass",
        "fake review",
        "fake engagement",
        "spam blast",
        "credential",
        "stolen cookie",
        "illegal",
        "накрут",
    )
    for w in forbidden:
        if w in text:
            rejects.append(f"forbidden:{w}")
    if expected_revenue <= 0:
        rejects.append("unknown_budget")
    if expected_profit < 0:
        rejects.append("negative_margin")
    if margin < 15 and expected_revenue > 0:
        rejects.append("low_margin")
    if hours > 40:
        rejects.append("impossible_deadline_effort")
    if not (title.strip() or description.strip()):
        rejects.append("no_deliverable")
    if first_money and expected_revenue > 0 and expected_revenue < 15:
        rejects.append("too_low_pay")
    if rejects:
        return "REJECT", rejects
    if success >= 0.72 and expected_profit >= 20 and margin >= 25:
        return "GO", []
    return "MAYBE", []


def human_summary(
    *,
    expected_revenue: float,
    auto: float,
    toloka: float,
    ai: float,
    hours: float,
    profit: float,
    success_pct: float,
    score: float,
) -> dict[str, str]:
    return {
        "budget": f"€{expected_revenue:.0f}",
        "automation": f"{auto:.0f}%",
        "toloka": f"€{toloka:.0f}",
        "ai_api": f"€{ai:.0f}",
        "estimated": f"{hours:.1f} h",
        "expected_profit": f"€{profit:.0f}",
        "success_probability": f"{success_pct:.0f}%",
        "opportunity_score": f"{score:.0f}/100",
    }


def priority_key(opp: dict[str, Any]) -> tuple:
    """Sort: high profit, high probability, low cost, high automation, short deadline."""
    eco = opp.get("economics") or {}
    return (
        -_f(eco.get("expected_profit")),
        -_f(eco.get("success_probability")),
        _f(eco.get("expected_cost")),
        -_f(eco.get("automation_percent")),
        _f(eco.get("estimated_hours")),
        -_f(eco.get("opportunity_score")),
    )
