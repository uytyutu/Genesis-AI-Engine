"""Niche → theme tokens + section set for AI Store storefronts."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class StoreTheme:
    template_id: str
    primary: str
    secondary: str
    accent: str
    background: str
    surface: str
    text: str
    muted: str
    hero_eyebrow: str
    hero_cta: str
    sections: tuple[str, ...] = (
        "hero",
        "featured",
        "catalog_teaser",
        "trust",
        "footer",
    )
    demo_product_names: tuple[str, ...] = ()
    category_labels: tuple[str, ...] = ()


_CATEGORY_THEMES: dict[str, StoreTheme] = {
    "clothing": StoreTheme(
        template_id="niche_clothing",
        primary="#1a1a1a",
        secondary="#f0ebe4",
        accent="#c45c26",
        background="#f7f3ee",
        surface="#fffaf5",
        text="#1a1a1a",
        muted="#6b6560",
        hero_eyebrow="New season",
        hero_cta="Shop collection",
        demo_product_names=(
            "Classic Tee",
            "Linen Shirt",
            "City Jacket",
            "Everyday Trousers",
            "Canvas Tote",
        ),
        category_labels=("Jackets", "Shirts", "Trousers", "Accessories"),
    ),
    "electronics": StoreTheme(
        template_id="niche_electronics",
        primary="#0f172a",
        secondary="#e8eef5",
        accent="#2563eb",
        background="#f1f5f9",
        surface="#f8fafc",
        text="#0f172a",
        muted="#64748b",
        hero_eyebrow="Tech essentials",
        hero_cta="Browse devices",
        demo_product_names=(
            "Wireless Earbuds",
            "USB-C Hub",
            "Smart Watch",
            "Portable Charger",
            "Desk Lamp LED",
        ),
        category_labels=("Audio", "Wearables", "Accessories", "Power"),
    ),
    "auto": StoreTheme(
        template_id="niche_auto",
        primary="#111827",
        secondary="#e8e9eb",
        accent="#dc2626",
        background="#f0f1f3",
        surface="#f7f8fa",
        text="#111827",
        muted="#6b7280",
        hero_eyebrow="Parts & care",
        hero_cta="Find parts",
        demo_product_names=(
            "Oil Filter Kit",
            "Car Cover",
            "LED Headlight Set",
            "Floor Mats",
            "Jump Starter",
        ),
        category_labels=("Filters", "Lighting", "Interior", "Tools"),
    ),
    "beauty": StoreTheme(
        template_id="niche_beauty",
        primary="#4a1942",
        secondary="#f8e8f0",
        accent="#db2777",
        background="#faf0f5",
        surface="#fff5fa",
        text="#3b102f",
        muted="#9d6b8a",
        hero_eyebrow="Care routine",
        hero_cta="Discover products",
        demo_product_names=(
            "Hydrating Serum",
            "Day Cream SPF",
            "Lip Balm Set",
            "Face Cleanser",
            "Hair Oil",
        ),
        category_labels=("Skincare", "Hair", "Sets", "SPF"),
    ),
    "jewelry": StoreTheme(
        template_id="niche_jewelry",
        primary="#1c1917",
        secondary="#efeae3",
        accent="#a16207",
        background="#f5f0e8",
        surface="#faf6f0",
        text="#1c1917",
        muted="#78716c",
        hero_eyebrow="Fine details",
        hero_cta="View pieces",
        demo_product_names=(
            "Gold Hoop Earrings",
            "Silver Chain",
            "Pearl Studs",
            "Signet Ring",
            "Bracelet Set",
        ),
        category_labels=("Earrings", "Necklaces", "Rings", "Bracelets"),
    ),
    "furniture": StoreTheme(
        template_id="niche_furniture",
        primary="#292524",
        secondary="#efe6d9",
        accent="#92400e",
        background="#f3ebe2",
        surface="#faf6f1",
        text="#292524",
        muted="#78716c",
        hero_eyebrow="Home & living",
        hero_cta="Explore furniture",
        demo_product_names=(
            "Oak Side Table",
            "Linen Cushion",
            "Floor Lamp",
            "Storage Shelf",
            "Ceramic Vase",
        ),
        category_labels=("Tables", "Lighting", "Textiles", "Decor"),
    ),
    "food": StoreTheme(
        template_id="niche_food",
        primary="#14532d",
        secondary="#dcefdc",
        accent="#16a34a",
        background="#eef6ee",
        surface="#f5faf5",
        text="#14532d",
        muted="#4d7c5a",
        hero_eyebrow="Fresh selection",
        hero_cta="Order now",
        demo_product_names=(
            "Organic Honey",
            "Artisan Bread",
            "Olive Oil",
            "Spice Mix",
            "Tea Sampler",
        ),
        category_labels=("Pantry", "Bakery", "Oils", "Tea"),
    ),
    "other": StoreTheme(
        template_id="niche_general",
        primary="#18181b",
        secondary="#ebe6df",
        accent="#059669",
        background="#f5f1eb",
        surface="#faf7f2",
        text="#18181b",
        muted="#71717a",
        hero_eyebrow="Featured",
        hero_cta="Shop now",
        demo_product_names=(
            "Starter Pack",
            "Best Seller",
            "Gift Set",
            "Everyday Essential",
            "Limited Edition",
            "Bundle Deal",
        ),
        category_labels=("New", "Bestsellers", "Gifts", "Essentials"),
    ),
}

# Style overrides must keep warm non-white page backgrounds (Visual Design Rule).
_STYLE_OVERRIDES: dict[str, dict[str, str]] = {
    "minimal": {"accent": "#525252", "background": "#f5f2ed", "secondary": "#ebe7e1", "surface": "#faf8f5"},
    "luxury": {"accent": "#a16207", "primary": "#0c0a09", "background": "#f5f0e8", "surface": "#faf6f0"},
    "tech": {"accent": "#2563eb", "primary": "#0f172a", "background": "#eef2f6", "surface": "#f5f8fb"},
    "bold": {"accent": "#e11d48", "primary": "#18181b", "background": "#f5f0ec"},
    "warm": {"accent": "#c2410c", "background": "#fff4e8", "secondary": "#ffe8d4", "surface": "#fffaf5"},
    "graphite": {"accent": "#64748b", "primary": "#0f172a", "background": "#eef1f4", "surface": "#f5f7f9"},
    "storefront_light": {"background": "#f7f3ee", "accent": "#059669", "surface": "#faf7f2"},
}

_PURE_WHITE = frozenset({"#fff", "#ffffff", "white"})


def _warm_bg(value: str, fallback: str = "#f5f1eb") -> str:
    v = (value or "").strip().lower()
    if v in _PURE_WHITE or not v:
        return fallback
    return value


@dataclass
class ResolvedTemplate:
    template_id: str
    theme: StoreTheme
    colors: dict[str, str] = field(default_factory=dict)
    sections: tuple[str, ...] = ()
    demo_products: list[dict[str, Any]] = field(default_factory=list)
    category_labels: tuple[str, ...] = ()


class StoreTemplateRegistry:
    """Map shop_brief.category / style → one base storefront adaptation."""

    def resolve(self, brief: dict[str, Any]) -> ResolvedTemplate:
        category = str(brief.get("category") or "other").strip().lower()
        base = _CATEGORY_THEMES.get(category) or _CATEGORY_THEMES["other"]
        style = str(brief.get("style") or "modern").strip().lower()
        if style == "minimalism":
            style = "minimal"

        colors = {
            "primary": base.primary,
            "secondary": base.secondary,
            "accent": base.accent,
            "background": base.background,
            "surface": base.surface,
            "text": base.text,
            "muted": base.muted,
        }
        for key, val in (_STYLE_OVERRIDES.get(style) or {}).items():
            colors[key] = val

        colors["background"] = _warm_bg(colors["background"], base.background)
        colors["surface"] = _warm_bg(colors.get("surface", base.surface), base.surface)

        custom = str(brief.get("color_scheme") or brief.get("color") or "").strip()
        if custom.startswith("#") and len(custom) in (4, 7):
            colors["accent"] = custom

        currency = str(brief.get("currency") or "EUR").upper()
        symbol = "€" if currency == "EUR" else ("$" if currency == "USD" else currency + " ")
        prices = [29.90, 49.00, 79.00, 99.00, 129.00, 159.00]
        old_prices = [39.90, 69.00, 99.00, 129.00, 159.00, 199.00]
        names = list(base.demo_product_names) or list(_CATEGORY_THEMES["other"].demo_product_names)
        count = min(6, max(3, len(names)))
        demo: list[dict[str, Any]] = []
        for i, name in enumerate(names[:count]):
            price = prices[i % len(prices)]
            old = old_prices[i % len(old_prices)]
            badge = ""
            if i == 0:
                badge = "NEW"
            elif i % 2 == 1:
                badge = "SALE"
            demo.append(
                {
                    "id": f"demo-{i + 1}",
                    "name": name,
                    "price": price,
                    "price_label": f"{symbol}{price:.2f}",
                    "old_price": old if badge == "SALE" else None,
                    "old_price_label": f"{symbol}{old:.2f}" if badge == "SALE" else "",
                    "badge": badge,
                    "rating": 4.2 + (i % 4) * 0.2,
                    "reviews": 12 + i * 7,
                    "stock": "In stock" if i != 3 else "Few left",
                    "category": category,
                }
            )

        return ResolvedTemplate(
            template_id=base.template_id,
            theme=base,
            colors=colors,
            sections=base.sections,
            demo_products=demo,
            category_labels=base.category_labels
            or _CATEGORY_THEMES["other"].category_labels,
        )
