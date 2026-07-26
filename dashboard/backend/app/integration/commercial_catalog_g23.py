"""G2.X — Commercial catalog (DE market · honest sellability).

Active: Landing, AI bots (Telegram/Website chat), website services.
Coming Soon only for channels/modules that cannot deliver yet (WhatsApp, Instagram, CRM…).
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
            "id": "telegram_ai_bot",
            "category": "product",
            "group": "bots",
            "name": "Telegram AI Bot",
            "price_label": f"from {VECTOR_SETUP_FROM_EUR} € setup + {VECTOR_MONTHLY_EUR['starter']} €/mo",
            "billing": "monthly",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order/bot?package=bot_business",
            "cta_label": "Order",
            "includes": "Business bot for Telegram · multi-channel wizard",
        },
        {
            "id": "website_ai_chat",
            "category": "product",
            "group": "bots",
            "name": "Website AI Chat",
            "price_label": f"from {VECTOR_SETUP_FROM_EUR} € setup + {VECTOR_MONTHLY_EUR['starter']} €/mo",
            "billing": "monthly",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order/bot?package=bot_business",
            "cta_label": "Order",
            "includes": "Site chat widget · same packages as Telegram bot",
        },
        {
            "id": "whatsapp_ai_bot",
            "category": "product",
            "group": "bots",
            "name": "WhatsApp AI Bot",
            "price_label": "—",
            "billing": "monthly",
            "availability": "coming_soon",
            "cta": "coming_soon",
            "cta_href": None,
            "cta_label": "Coming Soon",
            "includes": "Channel in rollout — not sold until delivery works",
        },
        {
            "id": "instagram_ai_bot",
            "category": "product",
            "group": "bots",
            "name": "Instagram AI Bot",
            "price_label": "—",
            "billing": "monthly",
            "availability": "coming_soon",
            "cta": "coming_soon",
            "cta_href": None,
            "cta_label": "Coming Soon",
            "includes": "Channel in rollout — not sold until delivery works",
        },
        _addon("ai_website_analysis", "AI Website Analysis", 149),
        _addon("website_repair", "Website Repair", 199, from_price=True),
        _addon("seo_audit", "SEO Audit", 249),
        _addon("speed_optimization", "Speed Optimization", 199),
        _addon("security_check", "Security Check", 299),
        _addon("google_business_setup", "Google Business Profile Setup", 149),
        _addon("website_migration", "Website Migration", 299, from_price=True),
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


def _addon(
    id_: str, name: str, eur: int, *, from_price: bool = False
) -> dict[str, Any]:
    label = f"from {eur} €" if from_price else f"{eur} €"
    return {
        "id": id_,
        "category": "one_time",
        "group": "website_services",
        "name": name,
        "price_label": label,
        "billing": "one_time",
        "availability": "available",
        "cta": "order_now",
        "cta_href": f"/order?package={id_}",
        "cta_label": "Order",
        "includes": "Standalone service — no website purchase required",
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
