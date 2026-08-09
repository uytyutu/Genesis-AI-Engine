"""AI Health — which Virtus modules are live vs waiting (honest)."""

from __future__ import annotations

from typing import Any


def build_ai_health(
    *,
    has_website: bool = False,
    has_store: bool = False,
    vector_active: bool = True,
    commerce_live: bool = False,
    analytics_live: bool = False,
    crm_live: bool = False,
) -> dict[str, Any]:
    modules = [
        {
            "id": "website",
            "label": "Website",
            "status": "live" if has_website else "waiting",
            "detail": "Landing / Factory package" if has_website else "Not purchased yet",
        },
        {
            "id": "store",
            "label": "Store",
            "status": "live" if has_store else "waiting",
            "detail": "AI Store + Store Admin" if has_store else "Not purchased yet",
        },
        {
            "id": "vector",
            "label": "Vector",
            "status": "live" if vector_active else "waiting",
            "detail": "One assistant · contextual surfaces",
        },
        {
            "id": "commerce",
            "label": "Commerce",
            "status": "live" if commerce_live else "coming",
            "coming": "R3.3",
            "detail": "Stripe · shipping · taxes",
        },
        {
            "id": "analytics",
            "label": "Analytics",
            "status": "live" if analytics_live else "coming",
            "coming": "R3.4",
            "detail": "Traffic · conversion · reports",
        },
        {
            "id": "crm",
            "label": "CRM",
            "status": "live" if crm_live else "coming",
            "coming": "R4",
            "detail": "Leads · pipeline · follow-ups",
        },
    ]
    live = sum(1 for m in modules if m["status"] == "live")
    return {
        "ok": True,
        "title": "AI Health",
        "modules": modules,
        "live_count": live,
        "total": len(modules),
        "note": "Waiting = not purchased. Coming = module not shipped yet.",
    }
