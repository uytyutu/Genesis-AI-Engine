"""G2.X — Commercial catalog (DE market · honest sellability).

Active: Landing, AI Digital Employee, full Website Services agency catalog.
Coming Soon: legacy CRM/automation module SKUs not yet deliverable as products.
"""

from __future__ import annotations

from typing import Any, Literal

ENGINE_ID = "commercial_catalog_g23_v1"

Category = Literal["one_time", "monthly", "product"]
Availability = Literal["available", "coming_soon"]

LANDING_PACKAGES_EUR: dict[str, int] = {
    "standalone": 499,
    "connected": 499,
    "basic": 499,
    "business": 499,
    "premium": 499,
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

# Website Services — agency catalog (EUR anchors, DE)
WEBSITE_SERVICE_PRICES_EUR: dict[str, int] = {
    "ai_website_analysis": 149,
    "website_repair": 199,
    "seo_audit": 249,
    "speed_optimization": 199,
    "security_check": 299,
    "google_business_setup": 149,
    "website_migration": 299,
    "reputation_audit": 149,
    "ecommerce_shop": 799,
    "ai_chatbot": 499,
    "business_automation": 399,
    "ai_social_content": 199,
    "site_maintenance": 49,
    "ai_seo_monitoring": 29,
}

_ADDON_LIVE = frozenset(WEBSITE_SERVICE_PRICES_EUR.keys())

_ADDON_INCLUDES: dict[str, str] = {
    "ai_website_analysis": (
        "HTTPS · mobile · SEO · Open Graph · Schema · PDF report · improvement plan"
    ),
    "website_repair": (
        "Bug fixes · WhatsApp button · Maps · forms · basic SEO · Open Graph · 2–5 days"
    ),
    "seo_audit": (
        "Title · Description · H1–H6 · robots · sitemap · Schema · CWV · fix plan"
    ),
    "speed_optimization": (
        "Core Web Vitals · images · CSS/JS · caching · lazy load · 2–5 days"
    ),
    "security_check": (
        "HTTPS/SSL · security headers · forms · main risks · remediation plan"
    ),
    "google_business_setup": (
        "Profile check · categories · hours · photos · links · growth plan"
    ),
    "website_migration": (
        "Content move · new design · domain · launch help · 3–10 days"
    ),
    "reputation_audit": (
        "Google Reviews · Maps · mentions · recommendations · 1–2 days"
    ),
    "ecommerce_shop": "Professional online shop for your business · catalog · cart · German legal pages · from 799 €",
    "ai_chatbot": "AI chat employee · channels · setup from 499 €",
    "business_automation": "Workflow automation for SMB · from 399 €",
    "ai_social_content": (
        "Reels · TikTok · Instagram · Facebook · AI voice · AI design · monthly"
    ),
    "site_maintenance": "Updates · backups · monitoring · support · monthly",
    "ai_seo_monitoring": "Rank tracking · improvement tips · monthly",
}

_ADDON_FROM_PRICE = frozenset(
    {
        "website_repair",
        "website_migration",
        "ecommerce_shop",
        "ai_chatbot",
        "business_automation",
        "ai_social_content",
        "site_maintenance",
        "ai_seo_monitoring",
    }
)

_ADDON_MONTHLY = frozenset(
    {"ai_social_content", "site_maintenance", "ai_seo_monitoring"}
)


def commercial_catalog_rows() -> tuple[dict[str, Any], ...]:
    """Public commercial rows for /products and readiness checks."""
    website_rows = tuple(
        _addon(
            sid,
            _addon_display_name(sid),
            WEBSITE_SERVICE_PRICES_EUR[sid],
            from_price=sid in _ADDON_FROM_PRICE,
            monthly=sid in _ADDON_MONTHLY,
        )
        for sid in (
            "website_repair",
            "ai_website_analysis",
            "seo_audit",
            "google_business_setup",
            "website_migration",
            "speed_optimization",
            "reputation_audit",
            "security_check",
            "ecommerce_shop",
            "ai_chatbot",
            "business_automation",
            "ai_social_content",
            "site_maintenance",
            "ai_seo_monitoring",
        )
    )
    return (
        {
            "id": "landing_website",
            "category": "product",
            "group": "websites",
            "name": "Business Website That Brings Leads",
            "price_label": f"{LANDING_PACKAGES_EUR['basic']}–{LANDING_PACKAGES_EUR['premium']} €",
            "billing": "one_time",
            "availability": "available",
            "cta": "order_now",
            "cta_href": "/order",
            "cta_label": "Order",
            "includes": (
                "Get more customers with a professional website · "
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
                "Answers 24/7 · Captures leads · Multi-language · "
                "Website · Telegram · WhatsApp · Instagram · Messenger"
            ),
        },
        *website_rows,
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


def _addon_display_name(id_: str) -> str:
    return {
        "ai_website_analysis": "AI Website Analysis",
        "website_repair": "Website Repair",
        "seo_audit": "SEO Audit",
        "speed_optimization": "Speed Optimization",
        "security_check": "Security Check",
        "google_business_setup": "Google Business Profile",
        "website_migration": "Website Migration",
        "reputation_audit": "Reputation Audit",
        "ecommerce_shop": "AI Store by Virtus Core",
        "ai_chatbot": "AI Chatbot",
        "business_automation": "Business Automation",
        "ai_social_content": "AI Social Content",
        "site_maintenance": "Website Maintenance",
        "ai_seo_monitoring": "AI SEO Monitoring",
    }.get(id_, id_.replace("_", " ").title())


def _addon(
    id_: str,
    name: str,
    eur: int,
    *,
    from_price: bool = False,
    available: bool | None = None,
    monthly: bool = False,
) -> dict[str, Any]:
    if monthly:
        label = f"from {eur} €/mo" if from_price else f"{eur} €/mo"
    else:
        label = f"from {eur} €" if from_price else f"{eur} €"
    live = id_ in _ADDON_LIVE if available is None else available
    includes = _ADDON_INCLUDES.get(id_) or (
        "Opening soon — ask Vector or open the interest form"
        if not live
        else "Order form first, then payment"
    )
    return {
        "id": id_,
        "category": "monthly" if monthly else "one_time",
        "group": "website_services",
        "name": name,
        "price_label": label,
        "billing": "monthly" if monthly else "one_time",
        "availability": "available" if live else "coming_soon",
        "cta": "order_now" if live else "coming_soon",
        "cta_href": (
            "/order/shop" if id_ == "ecommerce_shop" else f"/order/service/{id_}"
        ),
        "cta_label": "Order" if live else "Coming Soon",
        "includes": includes,
        "price_eur": eur,
        "from_price": from_price,
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
