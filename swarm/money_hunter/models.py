"""Money Hunter opportunity schema + lifecycle statuses."""

from __future__ import annotations

from typing import Any

STATUSES: tuple[str, ...] = (
    "DISCOVERED",
    "ANALYZING",
    "QUALIFIED",
    "REJECTED",
    "PENDING_APPROVAL",
    "APPROVED",
    "EXECUTING",
    "QA",
    "READY_TO_DELIVER",
    "DELIVERED",
    "PAYMENT_PENDING",
    "PAID",
    "FAILED",
    "CANCELLED",
)

# Manual adapters only at P0 — no CAPTCHA/scrape bypass.
SOURCE_ADAPTERS: dict[str, str] = {
    "manual": "UNIVERSAL_MANUAL_IMPORT",
    "upwork_manual": "UPWORK_MANUAL_IMPORT",
    "fiverr_manual": "FIVERR_MANUAL_IMPORT",
    "malt_manual": "MALT_MANUAL_IMPORT",
    "freelance_de_manual": "FREELANCE_DE_MANUAL_IMPORT",
}

TASK_TEMPLATES: tuple[str, ...] = (
    "WEB_RESEARCH",
    "DATA_VERIFICATION",
    "AI_RESPONSE_EVALUATION",
    "CONTENT_QA",
    "IMAGE_CLASSIFICATION",
    "DATA_CLEANING",
    "COMPETITOR_RESEARCH",
    "MARKET_RESEARCH",
    "HUMAN_AI_QA",
)

# Auto-spend policy (EUR) — never charge without approval.
SPEND_BANDS: tuple[tuple[float, float, str], ...] = (
    (0.0, 50.0, "pending_approval"),
    (50.0, 500.0, "manual_approval"),
    (500.0, float("inf"), "ceo_explicit"),
)

FIRST_MONEY_BUDGET_MIN = 30.0
FIRST_MONEY_BUDGET_MAX = 150.0


def empty_economics() -> dict[str, Any]:
    return {
        "budget_min": 0.0,
        "budget_max": 0.0,
        "currency": "EUR",
        "expected_revenue": 0.0,
        "toloka_cost": 0.0,
        "ai_cost": 0.0,
        "infrastructure_cost": 0.0,
        "estimated_internal_cost": 0.0,
        "platform_fee": 0.0,
        "risk_reserve": 0.0,
        "expected_cost": 0.0,
        "expected_profit": 0.0,
        "expected_margin_percent": 0.0,
        "estimated_hours": 0.0,
        "automation_percent": 0.0,
        "risk_score": 0.0,
        "success_probability": 0.0,
        "opportunity_score": 0.0,
        "spend_band": "pending_approval",
        "decision": "MAYBE",
        "reject_reasons": [],
        "human_summary": {},
    }
