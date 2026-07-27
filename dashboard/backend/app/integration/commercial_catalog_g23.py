"""G2.X — Commercial catalog (DE market · honest sellability).

Active: Landing, AI Digital Employee (one product), live website services + interest forms.
Coming Soon: CRM/automation modules not yet deliverable.
"""

from __future__ import annotations

from typing import Any, Literal

ENGINE_ID = "commercial_catalog_g23_v1"

Category = Literal["one_time", "monthly", "product"]
Availability = Literal["available", "coming_soon"]

LANDING_PACKAGES_EUR: dict[str, int] = {
    "basic": 350,
    "business": 650,
    "premium": 1200,
}

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
            "group": "websites",
            "name": "Landing Websites",
            "price_label": f"{LANDING_PACKAGES_EUR['basic']}–{LANDING_PACKAGES_EUR['premium']} €",
            "billing": "one_time",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order",
            "cta_label": "Order",
            "includes": (
                f"Basic {LANDING_PACKAGES_EUR['basic']} € · "
                f"Business {LANDING_PACKAGES_EUR['business']} € · "
                f"Premium {LANDING_PACKAGES_EUR['premium']} €"
            ),
        },
        {
            "id": "ai_business_bot",
            "category": "product",
            "group": "bots",
            "name": "AI Digital Employee",
            "price_label": f"499–1499 € setup + {VECTOR_MONTHLY_EUR['starter']}–349 €/mo",
            "billing": "monthly",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order/bot",
            "cta_label": "Order",
            "includes": (
                "AI Sales Assistant · Website · Telegram · WhatsApp · "
                "Instagram · Messenger"
            ),
        },
        _addon("ai_website_analysis", "AI Website Analysis", 149),
        _addon("website_repair", "Website Repair", 199, from_price=True),
        _addon("seo_audit", "SEO Audit", 249, available=False),
        _addon("speed_optimization", "Speed Optimization", 199, available=False),
        _addon("security_check", "Security Check", 299, available=False),
        _addon(
            "google_business_setup",
            "Google Business Profile Setup",
            149,
            available=False,
        ),
        _addon(
            "website_migration",
            "Website Migration",
            299,
            from_price=True,
            available=False,
        ),
        _monthly(
            "crm_starter",
            "CRM Starter",
            CRM_MONTHLY_EUR["starter"],
            "Contacts · pipeline basics",
        ),
        _monthly(
            "automation_starter",
            "Automation Starter",
            AUTOMATION_MONTHLY_EUR["starter"],
            "Simple workflows",
        ),
    )


# Honest sellability: only analysis + repair have intake → pay today.
_ADDON_LIVE = frozenset({"ai_website_analysis", "website_repair"})


def _addon(
    id_: str,
    name: str,
    eur: int,
    *,
    from_price: bool = False,
    available: bool | None = None,
) -> dict[str, Any]:
    label = f"from {eur} €" if from_price else f"{eur} €"
    live = id_ in _ADDON_LIVE if available is None else available
    return {
        "id": id_,
        "category": "one_time",
        "group": "website_services",
        "name": name,
        "price_label": label,
        "billing": "one_time",
        "availability": "available" if live else "coming_soon",
        "cta": "order_now" if live else "coming_soon",
        "cta_href": f"/order/service/{id_}",
        "cta_label": "Order form" if live else "Coming Soon",
        "includes": (
            "Order form first, then payment"
            if live
            else "Opening soon — ask Vector or open the interest form"
        ),
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
