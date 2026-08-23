"""Store Director — e-commerce experience decisions (not a site with a cart).

Decides first-screen merchandising, banners, search, recommendations, reviews,
product cards, and customer auth placement by package tier.
"""

from __future__ import annotations

from typing import Any

ENGINE_ID = "store_director_v1"


def decide_store_experience(
    *,
    package_id: str = "business",
    category: str | None = None,
    catalog_size: int | None = None,
) -> dict[str, Any]:
    pid = (package_id or "business").strip().lower()
    if pid not in ("basic", "business", "premium", "starter"):
        pid = "business"
    if pid == "starter":
        pid = "basic"

    size = int(catalog_size or 24)
    first_screen_products = 8 if size >= 24 else max(4, min(8, size))

    base = {
        "engine": ENGINE_ID,
        "role": "Store Director",
        "mission_ru": "Полноценный современный e-commerce, не сайт с корзиной.",
        "package_id": pid,
        "category": (category or "general").lower(),
        "customer_auth": {
            "login": True,
            "register": True,
            "guest_checkout": True,
            "customer_dashboard": True,
        },
        "chrome": ["search", "wishlist", "cart", "account"],
    }

    if pid == "basic":
        base["decisions"] = {
            "first_screen_products": first_screen_products,
            "hero_banner": "simple_image",
            "search_placement": "header",
            "recommendations": False,
            "recently_viewed": False,
            "reviews_on_pdp": True,
            "card_style": "clean",
            "motion": "subtle",
            "video_on_pdp": False,
            "media_3d": False,
        }
    elif pid == "business":
        base["decisions"] = {
            "first_screen_products": first_screen_products,
            "hero_banner": "quality_image_or_video_if_fits",
            "search_placement": "header_prominent",
            "recommendations": True,
            "recently_viewed": True,
            "reviews_on_home": True,
            "reviews_on_pdp": True,
            "card_style": "rich_hover",
            "motion": "business",
            "trust_blocks": True,
            "video_on_pdp": "if_fits",
            "media_3d": False,
        }
    else:
        base["decisions"] = {
            "first_screen_products": first_screen_products,
            "hero_banner": "premium_cinematic",
            "search_placement": "header_prominent",
            "recommendations": True,
            "recently_viewed": True,
            "reviews_on_home": True,
            "reviews_on_pdp": True,
            "wishlist": True,
            "card_style": "premium",
            "motion": "premium",
            "trust_blocks": True,
            "video_on_pdp": "if_fits",
            "media_3d_or_360": "if_category_helps",
            "luxury_merchandising": True,
        }
        base["customer_auth"]["b2b_ready"] = True

    return base
