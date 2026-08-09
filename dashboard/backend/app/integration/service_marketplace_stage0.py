"""Gen2 Stage 0 — Service Marketplace catalog (vitrine, not CRM)."""

from __future__ import annotations

from typing import Any, Literal

Badge = Literal["active", "activate", "coming_soon"]

# Mirrors dashboard/frontend/app/lib/clientServiceMarketplace.ts — keep in sync.
MARKETPLACE_LIVE: list[dict[str, Any]] = [
    {
        "id": "website",
        "icon": "🌐",
        "name": "Website",
        "badge": "activate",
        "activate_href": "/order?form=1",
        "open_href": "/client/products",
    },
    {
        "id": "ai_store",
        "icon": "🛒",
        "name": "AI Store",
        "badge": "activate",
        "activate_href": "/order/shop",
        "open_href": "/client/products",
    },
    {
        "id": "digital_employee",
        "icon": "🤖",
        "name": "AI Digital Employee",
        "badge": "activate",
        "activate_href": "/order/bot",
        "open_href": "/client/bots",
    },
    {
        "id": "website_auditor",
        "icon": "🔍",
        "name": "Website Auditor",
        "badge": "activate",
        "activate_href": "/site?service=analysis",
    },
    {
        "id": "seo",
        "icon": "📈",
        "name": "SEO Optimization",
        "badge": "activate",
        "activate_href": "/order/service/seo_audit?form=1",
    },
    {
        "id": "business_email",
        "icon": "📧",
        "name": "Business Email",
        "badge": "activate",
        "activate_href": "/order/shop",
    },
    {
        "id": "automation",
        "icon": "⚙️",
        "name": "Automation",
        "badge": "activate",
        "activate_href": "/order/service/business_automation?form=1",
    },
    {
        "id": "analytics",
        "icon": "📊",
        "name": "Analytics",
        "badge": "activate",
        "activate_href": "/order?form=1",
    },
    {
        "id": "domains_ssl",
        "icon": "☁️",
        "name": "Domains & SSL",
        "badge": "activate",
        "activate_href": "/order?form=1",
    },
    {
        "id": "backup",
        "icon": "💾",
        "name": "Cloud Backup",
        "badge": "activate",
        "activate_href": "/order/service/site_maintenance?form=1",
    },
    {
        "id": "security",
        "icon": "🔒",
        "name": "Security Monitoring",
        "badge": "activate",
        "activate_href": "/order/service/security_check?form=1",
    },
    {
        "id": "social",
        "icon": "📱",
        "name": "Social Media",
        "badge": "activate",
        "activate_href": "/order/service/ai_social_content?form=1",
    },
    {
        "id": "booking",
        "icon": "📅",
        "name": "Booking System",
        "badge": "activate",
        "activate_href": "/kontakt",
    },
]

MARKETPLACE_SOON: list[dict[str, Any]] = [
    {"id": "crm", "icon": "👥", "name": "CRM", "badge": "coming_soon"},
    {"id": "inventory", "icon": "📦", "name": "Inventory", "badge": "coming_soon"},
    {"id": "erp", "icon": "🏭", "name": "ERP", "badge": "coming_soon"},
    {"id": "marketplace_product", "icon": "🏪", "name": "Marketplace", "badge": "coming_soon"},
    {"id": "ai_marketing", "icon": "📣", "name": "AI Marketing", "badge": "coming_soon"},
    {"id": "ai_sales", "icon": "🤝", "name": "AI Sales", "badge": "coming_soon"},
]


def build_service_marketplace_catalog() -> dict[str, Any]:
    """Public catalog for Stage 0 vitrine — no ownership resolution here."""
    return {
        "ok": True,
        "stage": "gen2_stage_0",
        "title": "Service Marketplace",
        "subtitle": "Vitrine only — Activate existing delivery paths; Gen2 stays Coming Soon.",
        "services": MARKETPLACE_LIVE,
        "coming_soon": MARKETPLACE_SOON,
        "note": "CRM / Inventory / ERP / AI Marketing / AI Sales = Coming Soon until after first clients.",
    }
