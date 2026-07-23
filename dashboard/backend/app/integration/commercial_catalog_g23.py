"""G2.3 — Commercial Readiness catalog (DE market · honest sellability).

Rule: never mark Buy/Order for something that cannot complete payment + delivery.
Landing Path A is the only one-click paid product today.
"""

from __future__ import annotations

from typing import Any, Literal

ENGINE_ID = "commercial_catalog_g23_v1"

Category = Literal["one_time", "monthly", "product"]
Availability = Literal["available", "coming_soon"]

# Landing — locked commercial strategy (do not change).
LANDING_PACKAGES_EUR: dict[str, int] = {
    "basic": 350,
    "business": 650,
    "premium": 1200,
}

# Vector AI Business Employee — DE SMB positioning (below full custom agency setup).
VECTOR_SETUP_FROM_EUR = 499
VECTOR_MONTHLY_EUR: dict[str, int] = {
    "starter": 99,
    "business": 199,
    "professional": 349,
}

CRM_MONTHLY_EUR: dict[str, int] = {
    "starter": 29,
    "business": 79,
    "pro": 149,
}

AUTOMATION_MONTHLY_EUR: dict[str, int] = {
    "starter": 49,
    "business": 99,
}


def commercial_catalog_rows() -> tuple[dict[str, Any], ...]:
    """Public commercial rows for /products and readiness checks."""
    return (
        {
            "id": "landing_website",
            "category": "product",
            "name": "Landing Website",
            "price_label": f"{LANDING_PACKAGES_EUR['basic']}–{LANDING_PACKAGES_EUR['premium']} €",
            "billing": "one_time",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order",
            "cta_label": "Order now",
            "includes": (
                f"Basic {LANDING_PACKAGES_EUR['basic']} € · "
                f"Business {LANDING_PACKAGES_EUR['business']} € · "
                f"Premium {LANDING_PACKAGES_EUR['premium']} €"
            ),
        },
        {
            "id": "vector_employee",
            "category": "product",
            "name": "AI Business Employee (Vector)",
            "price_label": (
                f"from {VECTOR_MONTHLY_EUR['starter']} €/mo · "
                f"Setup from {VECTOR_SETUP_FROM_EUR} €"
            ),
            "billing": "monthly",
            "availability": "available",  # Activate path exists; paid monthly = coming_soon SKUs below
            "cta": "activate",
            "cta_href": "/projects/chatbot/setup",
            "cta_label": "Activate",
            "includes": (
                f"Starter {VECTOR_MONTHLY_EUR['starter']} € · "
                f"Business {VECTOR_MONTHLY_EUR['business']} € · "
                f"Professional {VECTOR_MONTHLY_EUR['professional']} € / mo "
                "(subscription checkout Coming Soon)"
            ),
        },
        # --- One-time services (priced · not one-click until delivery path exists) ---
        _one_time("ai_website_analysis", "AI Website Analysis", 149),
        _one_time("website_repair", "Website Repair", 199, from_price=True),
        _one_time("seo_audit", "SEO Audit", 249),
        _one_time("speed_optimization", "Speed Optimization", 199),
        _one_time("security_check", "Security Check", 299),
        _one_time("google_business_setup", "Google Business Profile Setup", 149),
        _one_time("website_migration", "Website Migration", 299, from_price=True),
        # --- Monthly modules (priced · Coming Soon) ---
        _monthly(
            "vector_starter",
            "Vector Starter",
            VECTOR_MONTHLY_EUR["starter"],
            "Website widget · limited conversations · DE hosting",
        ),
        _monthly(
            "vector_business",
            "Vector Business",
            VECTOR_MONTHLY_EUR["business"],
            "More volume · knowledge base · channels",
        ),
        _monthly(
            "vector_professional",
            "Vector Professional",
            VECTOR_MONTHLY_EUR["professional"],
            "Priority ops · integrations · higher limits",
        ),
        _monthly("crm_starter", "CRM Starter", CRM_MONTHLY_EUR["starter"], "Contacts · pipeline basics"),
        _monthly("crm_business", "CRM Business", CRM_MONTHLY_EUR["business"], "Pipeline · tasks · reports"),
        _monthly("crm_pro", "CRM Pro", CRM_MONTHLY_EUR["pro"], "Team · automations · priorities"),
        _monthly(
            "automation_starter",
            "Automation Starter",
            AUTOMATION_MONTHLY_EUR["starter"],
            "Simple workflows",
        ),
        _monthly(
            "automation_business",
            "Automation Business",
            AUTOMATION_MONTHLY_EUR["business"],
            "Multi-step workflows",
        ),
        {
            "id": "automation_enterprise",
            "category": "monthly",
            "name": "Automation Enterprise",
            "price_label": "Individual",
            "billing": "monthly",
            "availability": "coming_soon",
            "cta": "coming_soon",
            "cta_href": None,
            "cta_label": "Coming Soon",
            "includes": "Custom scope · quote only",
        },
    )


def _one_time(
    id_: str, name: str, eur: int, *, from_price: bool = False
) -> dict[str, Any]:
    label = f"from {eur} €" if from_price else f"{eur} €"
    return {
        "id": id_,
        "category": "one_time",
        "name": name,
        "price_label": label,
        "billing": "one_time",
        "availability": "coming_soon",
        "cta": "coming_soon",
        "cta_href": None,
        "cta_label": "Coming Soon",
        "includes": "Priced for DE SMB · sold after delivery path is ready",
    }


def _monthly(id_: str, name: str, eur: int, includes: str) -> dict[str, Any]:
    return {
        "id": id_,
        "category": "monthly",
        "name": name,
        "price_label": f"{eur} €/mo",
        "billing": "monthly",
        "availability": "coming_soon",
        "cta": "coming_soon",
        "cta_href": None,
        "cta_label": "Coming Soon",
        "includes": includes,
    }


def sellable_online_ids() -> frozenset[str]:
    """IDs that may show Order now / paid checkout today."""
    return frozenset(
        row["id"]
        for row in commercial_catalog_rows()
        if row["cta"] == "order_now" and row["availability"] == "available"
    )


def assert_no_fake_buy_buttons() -> None:
    for row in commercial_catalog_rows():
        if row["cta"] in {"order_now", "buy"}:
            assert row["availability"] == "available"
            assert row["cta_href"], row["id"]
        if row["availability"] == "coming_soon":
            assert row["cta"] == "coming_soon", row["id"]
