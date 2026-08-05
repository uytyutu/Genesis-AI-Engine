"""AI Store (ecommerce_shop) brief contract — R1 validate/normalize; R2 Factory reads same shape."""

from __future__ import annotations

from typing import Any

SHOP_PACKAGE_ID = "ecommerce_shop"

# R1 uses accepted → preparing → factory_queue.
# R2+ may advance: generating → quality_check → ready_to_publish → published.
SHOP_PIPELINE_ACCEPTED = "accepted"
SHOP_PIPELINE_PREPARING = "preparing"
SHOP_PIPELINE_FACTORY_QUEUE = "factory_queue"
SHOP_PIPELINE_GENERATING = "generating"
SHOP_PIPELINE_QUALITY = "quality_check"
SHOP_PIPELINE_READY_PUBLISH = "ready_to_publish"
SHOP_PIPELINE_PUBLISHED = "published"

# Legacy aliases (older R1 stub)
SHOP_PIPELINE_CREATING = SHOP_PIPELINE_ACCEPTED
SHOP_PIPELINE_READY = SHOP_PIPELINE_FACTORY_QUEUE

SHOP_PIPELINE_LABELS = {
    SHOP_PIPELINE_ACCEPTED: {
        "en": "Accepted",
        "de": "Angenommen",
        "ru": "Принят",
    },
    SHOP_PIPELINE_PREPARING: {
        "en": "Preparing",
        "de": "Vorbereitung",
        "ru": "Подготовка",
    },
    SHOP_PIPELINE_FACTORY_QUEUE: {
        "en": "In preparation queue",
        "de": "In der Vorbereitungswarteschlange",
        "ru": "В очереди на подготовку",
    },
    SHOP_PIPELINE_GENERATING: {
        "en": "Creating your shop",
        "de": "Shop wird erstellt",
        "ru": "Создаём ваш магазин",
    },
    SHOP_PIPELINE_QUALITY: {
        "en": "Quality check",
        "de": "Qualitätsprüfung",
        "ru": "Проверка качества",
    },
    SHOP_PIPELINE_READY_PUBLISH: {
        "en": "Ready to publish",
        "de": "Bereit zur Veröffentlichung",
        "ru": "Готов к публикации",
    },
    SHOP_PIPELINE_PUBLISHED: {
        "en": "Published",
        "de": "Veröffentlicht",
        "ru": "Опубликован",
    },
    # legacy keys still stored on old orders
    "creating": {"en": "Accepted", "de": "Angenommen", "ru": "Принят"},
    "ready_for_factory": {
        "en": "In preparation queue",
        "de": "In der Vorbereitungswarteschlange",
        "ru": "В очереди на подготовку",
    },
}

CATEGORIES = frozenset(
    {
        "clothing",
        "electronics",
        "auto",
        "beauty",
        "jewelry",
        "furniture",
        "food",
        "other",
    }
)
CATALOG_SIZES = frozenset({"20", "100", "500", "1000+"})
PAYMENT_METHODS = frozenset({"stripe", "paypal", "bank"})
SHIPPING_METHODS = frozenset({"dhl", "hermes", "dpd", "pickup"})
PAGE_IDS = frozenset(
    {
        "home",
        "catalog",
        "pdp",
        "about",
        "contact",
        "faq",
        "legal",
        "returns",
        "news",
        "blog",
    }
)
STYLE_PRESETS = frozenset(
    {
        "modern",
        "minimal",
        "minimalism",
        "luxury",
        "tech",
        "bold",
        "warm",
        "graphite",
        "storefront_light",
    }
)
LOGO_NEEDS = frozenset({"have_logo", "need_new_logo", "skip"})
INTEGRATIONS = frozenset(
    {
        "instagram_shop",
        "facebook_shop",
        "google_merchant",
        "google_analytics",
        "meta_pixel",
    }
)


def shop_pipeline_label(pipeline: str, ui_lang: str = "en") -> str:
    key = str(pipeline or "").strip()
    row = SHOP_PIPELINE_LABELS.get(key) or {}
    lang = (ui_lang or "en").strip().lower()[:2]
    return str(row.get(lang) or row.get("en") or key or "")


def _as_bool(raw: Any, default: bool = False) -> bool:
    if isinstance(raw, bool):
        return raw
    if raw is None:
        return default
    s = str(raw).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def _str_list(raw: Any, allowed: frozenset[str] | None = None) -> list[str]:
    if isinstance(raw, str):
        items = [p.strip() for p in raw.split(",") if p.strip()]
    elif isinstance(raw, list):
        items = [str(x).strip() for x in raw if str(x).strip()]
    else:
        items = []
    if allowed is not None:
        items = [x.lower() for x in items if x.lower() in allowed]
    return items[:24]


def validate_shop_brief(raw: Any) -> dict[str, Any]:
    """Normalize buyer questionnaire into a stable Factory contract."""
    if not isinstance(raw, dict):
        raise ValueError("shop_brief_required")
    company = str(raw.get("company_name") or raw.get("business_name") or "").strip()
    store = str(raw.get("store_name") or "").strip()
    if not company:
        raise ValueError("shop_brief_company_required")
    if not store:
        raise ValueError("shop_brief_store_name_required")

    category = str(raw.get("category") or "other").strip().lower()
    if category not in CATEGORIES:
        category = "other"
    catalog_size = str(raw.get("catalog_size") or "20").strip()
    if catalog_size not in CATALOG_SIZES:
        catalog_size = "20"

    languages = raw.get("languages") or ["de"]
    if isinstance(languages, str):
        languages = [p.strip() for p in languages.split(",") if p.strip()]
    languages = [str(x).strip().lower()[:5] for x in languages if str(x).strip()][:8]
    if not languages:
        languages = ["de"]

    currency = str(raw.get("currency") or "EUR").strip().upper()[:3] or "EUR"

    payments = _str_list(raw.get("payments") or ["stripe"], PAYMENT_METHODS) or ["stripe"]
    shipping = _str_list(raw.get("shipping") or [], SHIPPING_METHODS)

    pages = _str_list(
        raw.get("pages") or ["home", "catalog", "pdp", "contact", "legal"], PAGE_IDS
    )
    if "home" not in pages:
        pages = ["home", *pages]
    if "catalog" not in pages:
        pages.append("catalog")

    style = str(raw.get("style") or "modern").strip().lower()
    if style == "minimalism":
        style = "minimal"
    if style not in STYLE_PRESETS:
        style = "modern"
    color = str(raw.get("color_scheme") or raw.get("color") or "").strip()[:80]

    logo_need = str(raw.get("logo_need") or "").strip().lower()
    if logo_need not in LOGO_NEEDS:
        if str(raw.get("logo_url") or "").strip():
            logo_need = "have_logo"
        else:
            logo_need = "need_new_logo"

    product_categories = raw.get("product_categories") or raw.get("category_list") or []
    if isinstance(product_categories, str):
        product_categories = [p.strip() for p in product_categories.split(",") if p.strip()]
    product_categories = [str(x).strip()[:80] for x in product_categories if str(x).strip()][
        :24
    ]

    integrations = _str_list(raw.get("integrations") or [], INTEGRATIONS)

    return {
        "company_name": company[:120],
        "store_name": store[:120],
        "business_description": str(raw.get("business_description") or "").strip()[:2000],
        "what_is_sold": str(raw.get("what_is_sold") or raw.get("products") or "").strip()[
            :2000
        ],
        "category": category,
        "product_categories": product_categories,
        "catalog_size": catalog_size,
        "languages": languages,
        "currency": currency,
        "payments": payments,
        "shipping": shipping,
        "pages": pages,
        "wishes": str(raw.get("wishes") or raw.get("extra_wishes") or "").strip()[:3000],
        "logo_url": str(raw.get("logo_url") or "").strip()[:500],
        "logo_need": logo_need,
        "photo_urls": [
            str(u).strip()[:500]
            for u in (raw.get("photo_urls") or [])
            if str(u).strip()
        ][:12],
        "color_scheme": color,
        "style": style,
        # Shop features (R2 Factory reads; not auto-built in R1)
        "need_variants": _as_bool(raw.get("need_variants")),
        "need_search": _as_bool(raw.get("need_search"), default=True),
        "need_reviews": _as_bool(raw.get("need_reviews")),
        # Sales features
        "need_promo_codes": _as_bool(raw.get("need_promo_codes")),
        "need_gift_cards": _as_bool(raw.get("need_gift_cards")),
        "has_digital_products": _as_bool(raw.get("has_digital_products")),
        # Integrations wishlist
        "integrations": integrations,
    }


def brief_summary_line(brief: dict[str, Any]) -> str:
    store = str(brief.get("store_name") or "").strip()
    cat = str(brief.get("category") or "").strip()
    size = str(brief.get("catalog_size") or "").strip()
    style = str(brief.get("style") or "").strip()
    parts = [p for p in (store, cat, style, f"~{size} SKUs" if size else "") if p]
    return " · ".join(parts)[:240] or "AI Store brief"
