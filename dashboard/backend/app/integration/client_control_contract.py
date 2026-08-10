# -*- coding: utf-8 -*-
"""Client Control contract — same Workspace format for Basic / Business / Premium.

Capability depth differs by package tier. CMS never invents fake integrations.
"""

from __future__ import annotations

from typing import Any


TIER_ALIASES = {
    "basic": "basic",
    "standalone": "basic",
    "business": "business",
    "premium": "premium",
    "connected": "premium",
    "ecommerce_shop": "premium",
}


def normalize_tier(package_id: str | None, *, product_kind: str | None = None) -> str:
    raw = (package_id or "").strip().lower()
    if product_kind == "shop" or raw == "ecommerce_shop":
        # Shop inherits premium control surface when sold as Premium AI Store
        return "premium"
    return TIER_ALIASES.get(raw, "business" if raw else "basic")


def client_control_capabilities(
    package_id: str | None = None,
    *,
    product_kind: str | None = None,
    gift_unlimited: bool = False,
) -> dict[str, Any]:
    """Return honest capability map for Website + Shop admin UI."""
    tier = normalize_tier(package_id, product_kind=product_kind)
    if gift_unlimited:
        tier = "premium"

    cinematic_scenes = {"basic": 0, "business": 8, "premium": 18}[tier]
    return {
        "tier": tier,
        "workspace_format": "your_business_home",
        "forced_setup": False,
        "website": {
            "preview": True,
            "edit_content": True,
            "edit_design_tokens": tier != "basic",
            "edit_media": True,
            "cinematic_scenes": cinematic_scenes,
            "cinematic_replace": cinematic_scenes > 0,
            "version_history": True,
            "restore_original": True,
            "live_sync": True,
        },
        "shop": {
            "products_crud": True,
            "unlimited_products": True,
            "categories": tier != "basic",
            "theme_tokens": tier != "basic",
            "orders": True,
            "reviews": True,
            "live_sync": True,
            "version_history": True,
            "restore_original": True,
            "shipping": {"dhl": "not_connected", "connect": True},
            "payments": {"status": "not_connected", "connect": True},
        },
        "analytics": {"mode": "no_data_yet", "fake_numbers": False},
        "marketplace": {"show": True, "fake_activate": False},
        "mobile_bottom_nav": True,
    }
