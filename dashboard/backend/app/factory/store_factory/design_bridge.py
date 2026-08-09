"""Bridge Design Engine → AI Store Factory (Premium Generation).

Website and Store share palettes, typography, radii and shadows via
``app.factory.design_engine``. Store keeps specialised components
(catalog, PDP, cart) but no longer invents a parallel theme stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.factory.design_engine import (
    DesignTokens,
    FontPack,
    font_link_tags,
    font_pack_for_niche,
    resolve_for_niche,
)

# Store brief category → Website Design Engine niche_id
STORE_CATEGORY_TO_NICHE: dict[str, str] = {
    "clothing": "fashion",
    "fashion": "fashion",
    "beauty": "beauty",
    "auto": "auto",
    "electronics": "computer",
    "food": "restaurant",
    "jewelry": "fashion",
    "accessories": "fashion",
    "furniture": "realestate",
    "handwerk": "handwerk",
    "dachreinigung": "dachreinigung",
    "zaunbau": "zaunbau",
    "gartenpflege": "gartenpflege",
    "psychology": "psychology",
    "therapy": "psychology",
    "cleaning": "cleaning",
    "auto_detailing": "auto_detailing",
    "orthodontics": "orthodontics",
    "books": "photography",  # editorial / quiet retail feel
    "it_parts": "computer",
    "solar": "energy",
    "auto_parts": "auto",
    "maler": "maler",
    "paint": "maler",
    "wine": "restaurant",
    "optics": "computer",
    "other": "generic",
}


@dataclass(frozen=True)
class ImageSlots:
    """Architecture for R5 AI images — placeholders today, slots always present."""

    hero: str = "assets/images/hero.jpg"
    banner: str = "assets/images/banner.jpg"
    category: str = "assets/images/category.jpg"
    product: str = "assets/images/product.jpg"


@dataclass(frozen=True)
class StoreVisualPreset:
    """Niche-specific composition — not just colors."""

    niche_id: str
    hero_layout: str  # editorial | industrial | soft | culinary | tech | boutique
    catalog_layout: str  # large | dense | brand | technical | warm
    card_preset: str  # fashion | beauty | auto | electronics | food | furniture | jewelry | craft | general
    radius: str
    shadow: str
    btn_radius: str
    hero_min_height: str = "72vh"
    card_media_ratio: str = "1 / 1"
    show_quick_view: bool = False
    show_specs: bool = False
    show_brands: bool = False
    show_certs: bool = False
    image_slots: ImageSlots = field(default_factory=ImageSlots)


_PRESETS: dict[str, StoreVisualPreset] = {
    "fashion": StoreVisualPreset(
        niche_id="fashion",
        hero_layout="editorial",
        catalog_layout="large",
        card_preset="fashion",
        radius="2px",
        shadow="0 24px 48px rgba(0,0,0,0.12)",
        btn_radius="999px",
        hero_min_height="78vh",
        card_media_ratio="3 / 4",
        show_quick_view=True,
    ),
    "beauty": StoreVisualPreset(
        niche_id="beauty",
        hero_layout="soft",
        catalog_layout="brand",
        card_preset="beauty",
        radius="16px",
        shadow="0 14px 36px rgba(190,24,93,0.12)",
        btn_radius="999px",
        hero_min_height="70vh",
        card_media_ratio="1 / 1",
        show_brands=True,
    ),
    "psychology": StoreVisualPreset(
        niche_id="psychology",
        hero_layout="soft",
        catalog_layout="brand",
        card_preset="beauty",
        radius="18px",
        shadow="0 14px 36px rgba(63,90,79,0.10)",
        btn_radius="999px",
        hero_min_height="72vh",
        card_media_ratio="4 / 5",
        show_brands=False,
    ),
    "auto": StoreVisualPreset(
        niche_id="auto",
        hero_layout="tech",
        catalog_layout="technical",
        card_preset="auto",
        radius="6px",
        shadow="0 16px 32px rgba(0,0,0,0.14)",
        btn_radius="6px",
        hero_min_height="68vh",
        card_media_ratio="4 / 3",
        show_specs=True,
    ),
    "computer": StoreVisualPreset(
        niche_id="computer",
        hero_layout="tech",
        catalog_layout="technical",
        card_preset="electronics",
        radius="10px",
        shadow="0 10px 24px rgba(3,105,161,0.10)",
        btn_radius="8px",
        hero_min_height="66vh",
        card_media_ratio="1 / 1",
        show_specs=True,
        show_quick_view=True,
    ),
    "restaurant": StoreVisualPreset(
        niche_id="restaurant",
        hero_layout="culinary",
        catalog_layout="warm",
        card_preset="food",
        radius="12px",
        shadow="0 18px 40px rgba(124,45,18,0.12)",
        btn_radius="999px",
        hero_min_height="74vh",
        card_media_ratio="16 / 10",
    ),
    "handwerk": StoreVisualPreset(
        niche_id="handwerk",
        hero_layout="industrial",
        catalog_layout="dense",
        card_preset="craft",
        radius="4px",
        shadow="0 14px 28px rgba(28,25,23,0.12)",
        btn_radius="4px",
        hero_min_height="70vh",
        card_media_ratio="4 / 3",
        show_certs=True,
    ),
    "dachreinigung": StoreVisualPreset(
        niche_id="dachreinigung",
        hero_layout="industrial",
        catalog_layout="technical",
        card_preset="craft",
        radius="6px",
        shadow="0 16px 32px rgba(15,23,42,0.14)",
        btn_radius="6px",
        hero_min_height="72vh",
        card_media_ratio="4 / 3",
        show_specs=True,
        show_certs=True,
    ),
    "zaunbau": StoreVisualPreset(
        niche_id="zaunbau",
        hero_layout="industrial",
        catalog_layout="dense",
        card_preset="craft",
        radius="4px",
        shadow="0 14px 28px rgba(28,25,23,0.12)",
        btn_radius="4px",
        hero_min_height="70vh",
        card_media_ratio="16 / 10",
        show_specs=True,
    ),
    "gartenpflege": StoreVisualPreset(
        niche_id="gartenpflege",
        hero_layout="soft",
        catalog_layout="warm",
        card_preset="craft",
        radius="14px",
        shadow="0 16px 36px rgba(20,83,45,0.12)",
        btn_radius="999px",
        hero_min_height="74vh",
        card_media_ratio="1 / 1",
        show_certs=True,
    ),
    "realestate": StoreVisualPreset(
        niche_id="realestate",
        hero_layout="editorial",
        catalog_layout="large",
        card_preset="furniture",
        radius="8px",
        shadow="0 12px 28px rgba(29,78,216,0.10)",
        btn_radius="6px",
        hero_min_height="72vh",
        card_media_ratio="16 / 10",
    ),
    "generic": StoreVisualPreset(
        niche_id="generic",
        hero_layout="editorial",
        catalog_layout="dense",
        card_preset="general",
        radius="12px",
        shadow="0 12px 24px rgba(0,0,0,0.08)",
        btn_radius="999px",
    ),
}


def store_category_to_niche_id(category: str | None) -> str:
    key = (category or "other").strip().lower() or "other"
    return STORE_CATEGORY_TO_NICHE.get(key, "generic")


def visual_preset_for_niche(niche_id: str) -> StoreVisualPreset:
    nid = (niche_id or "generic").strip().lower() or "generic"
    return _PRESETS.get(nid, _PRESETS["generic"])


def visual_preset_for_category(category: str | None) -> StoreVisualPreset:
    return visual_preset_for_niche(store_category_to_niche_id(category))


def resolve_store_design(
    category: str | None,
    *,
    package_id: str = "business",
) -> tuple[DesignTokens, StoreVisualPreset, FontPack]:
    niche_id = store_category_to_niche_id(category)
    pid = (package_id or "business").strip().lower() or "business"
    # Visual Intelligence Engine — Style Engine drives niche language;
    # Design Engine tokens + StoreVisualPreset remain the store component layer.
    try:
        from app.factory.visual_intelligence.engine import resolve_visual_plan

        plan = resolve_visual_plan(
            niche_id=niche_id,
            surface="store",
            package_id=pid,
            pick_assets=True,
        )
        tokens = plan.tokens
        pack = plan.fonts
        preset = visual_preset_for_niche(plan.niche_id)
        return tokens, preset, pack
    except Exception:
        tokens = resolve_for_niche(niche_id)
        preset = visual_preset_for_niche(niche_id)
        pack = font_pack_for_niche(niche_id)
        return tokens, preset, pack


def store_colors_from_tokens(
    tokens: DesignTokens,
    *,
    warm_background: str,
    warm_surface: str,
    warm_secondary: str,
) -> dict[str, str]:
    """Map Design Engine tokens → store color dict; keep warm non-white backgrounds."""
    # Fashion website uses dark surface — storefronts stay light/warm for shop UX.
    ink = tokens.ink if tokens.ink.lower() not in ("#0c0a09", "#09090b") else "#1c1917"
    return {
        "primary": tokens.primary_dark if tokens.niche_id == "fashion" else tokens.primary,
        "secondary": warm_secondary,
        "accent": tokens.accent if tokens.accent.lower() not in ("#e0f2fe", "#fbcfe8") else tokens.primary,
        "background": warm_background,
        "surface": warm_surface,
        "text": ink,
        "muted": tokens.muted,
        "hero_gradient": tokens.hero_gradient,
    }


def emit_store_root_css(
    *,
    colors: dict[str, str],
    tokens: DesignTokens,
    preset: StoreVisualPreset,
) -> str:
    """`:root` + niche body hooks for storefront CSS (keeps --store-* contract)."""
    pack = tokens.font_pack
    return f"""/* Design Engine · Store Premium · niche={tokens.niche_id} */
:root {{
  --store-primary: {colors['primary']};
  --store-secondary: {colors['secondary']};
  --store-accent: {colors['accent']};
  --store-bg: {colors['background']};
  --store-surface: {colors['surface']};
  --store-text: {colors['text']};
  --store-muted: {colors['muted']};
  --store-radius: {preset.radius};
  --store-shadow: {preset.shadow};
  --store-shadow-hover: 0 18px 48px rgba(28, 25, 23, 0.14);
  --store-btn-radius: {preset.btn_radius};
  --store-card-ratio: {preset.card_media_ratio};
  --store-hero-min: {preset.hero_min_height};
  --font-sans: {pack.body};
  --font-display: {pack.display};
  --p: {tokens.primary};
  --pd: {tokens.primary_dark};
  --acc: {tokens.accent};
  --font-body: {pack.body};
}}
"""


def niche_store_css(preset: StoreVisualPreset) -> str:
    """Composition CSS that makes niches diverge beyond recolor."""
    hl = preset.hero_layout
    cl = preset.catalog_layout
    cp = preset.card_preset
    bits = [
        f"""
/* Niche composition: hero={hl} catalog={cl} cards={cp} */
body[data-niche="{preset.niche_id}"] .btn {{
  border-radius: var(--store-btn-radius);
}}
body[data-niche="{preset.niche_id}"] .card {{
  border-radius: var(--store-radius);
  box-shadow: var(--store-shadow);
}}
body[data-niche="{preset.niche_id}"] .card-media {{
  aspect-ratio: var(--store-card-ratio);
  border-radius: calc(var(--store-radius) - 1px);
}}
body[data-niche="{preset.niche_id}"] .hero {{
  min-height: var(--store-hero-min);
  display: flex;
  align-items: center;
}}
"""
    ]
    if hl == "editorial":
        bits.append(
            """
body[data-hero-layout="editorial"] .hero {
  background:
    linear-gradient(105deg, rgba(12,10,9,.88) 0%, rgba(12,10,9,.35) 55%, transparent 100%),
    var(--store-hero-gradient, linear-gradient(135deg, var(--store-primary), var(--store-accent)));
  color: #fafaf9;
}
body[data-hero-layout="editorial"] .hero-eyebrow { color: rgba(250,250,249,.7); letter-spacing: 0.2em; }
body[data-hero-layout="editorial"] .hero h1 { max-width: 12ch; font-size: clamp(2.4rem, 6vw, 4rem); color: #fafaf9; }
body[data-hero-layout="editorial"] .hero p { color: rgba(250,250,249,.82); }
"""
        )
    elif hl == "industrial":
        bits.append(
            """
body[data-hero-layout="industrial"] .hero {
  background: linear-gradient(135deg, #1c1917 0%, #44403c 40%, var(--store-accent) 100%);
  color: #fafaf9;
  border-bottom: 4px solid var(--store-accent);
}
body[data-hero-layout="industrial"] .hero h1 {
  font-size: clamp(2.2rem, 5vw, 3.4rem); text-transform: uppercase; letter-spacing: 0.04em; color: #fafaf9;
}
body[data-hero-layout="industrial"] .trust { border-top: 2px solid var(--store-accent); }
"""
        )
    elif hl == "soft":
        bits.append(
            """
body[data-hero-layout="soft"] .hero {
  background:
    radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--store-accent) 28%, transparent), transparent 45%),
    linear-gradient(160deg, var(--store-surface), var(--store-secondary));
  border-radius: 0 0 2rem 2rem;
}
body[data-hero-layout="soft"] .hero h1 { letter-spacing: 0.02em; }
body[data-hero-layout="soft"] .btn { box-shadow: 0 12px 28px color-mix(in srgb, var(--store-accent) 30%, transparent); }
"""
        )
    elif hl == "culinary":
        bits.append(
            """
body[data-hero-layout="culinary"] .hero {
  background:
    linear-gradient(155deg, rgba(28,25,23,.75) 0%, rgba(124,45,18,.45) 50%, transparent 100%),
    var(--store-hero-gradient, linear-gradient(135deg, #7c2d12, #c2410c));
  color: #faf6f1;
  min-height: 74vh;
}
body[data-hero-layout="culinary"] .hero h1 { color: #faf6f1; max-width: 14ch; }
body[data-hero-layout="culinary"] .hero p { color: rgba(250,246,241,.88); }
"""
        )
    elif hl == "tech":
        bits.append(
            """
body[data-hero-layout="tech"] .hero {
  background: linear-gradient(135deg, #0f172a 0%, var(--store-primary) 55%, var(--store-accent) 100%);
  color: #f8fafc;
}
body[data-hero-layout="tech"] .hero h1 { letter-spacing: -0.04em; color: #f8fafc; }
body[data-hero-layout="tech"] .hero-trust { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.25rem; }
"""
        )
    elif hl == "boutique":
        bits.append(
            """
body[data-hero-layout="boutique"] .hero {
  background: linear-gradient(145deg, #0c0a09, #1c1917 50%, var(--store-accent));
  color: #faf6f0;
}
"""
        )

    if cl == "large":
        bits.append(
            """
body[data-catalog="large"] .grid {
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 1.75rem;
}
body[data-catalog="large"] .card-media { min-height: 16rem; }
"""
        )
    elif cl == "technical":
        bits.append(
            """
body[data-catalog="technical"] .grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}
body[data-catalog="technical"] .card .card-meta {
  font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--store-muted);
}
"""
        )
    elif cl == "brand":
        bits.append(
            """
body[data-catalog="brand"] .grid {
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1.35rem;
}
body[data-catalog="brand"] .card { background: var(--store-surface); border: 1px solid color-mix(in srgb, var(--store-accent) 18%, transparent); }
"""
        )
    elif cl == "warm":
        bits.append(
            """
body[data-catalog="warm"] .grid {
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1.5rem;
}
body[data-catalog="warm"] .card-media {
  background: linear-gradient(145deg, var(--store-secondary), color-mix(in srgb, var(--store-accent) 25%, var(--store-surface)));
}
"""
        )
    elif cl == "dense":
        bits.append(
            """
body[data-catalog="dense"] .grid {
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 0.85rem;
}
"""
        )

    if cp == "fashion":
        bits.append(
            """
body[data-card="fashion"] .card h3 { font-family: var(--font-display); font-weight: 500; letter-spacing: 0.04em; text-transform: uppercase; font-size: 0.92rem; }
body[data-card="fashion"] .card .btn-row .btn-ghost { display: inline-flex; }
"""
        )
    elif cp == "beauty":
        bits.append(
            """
body[data-card="beauty"] .card { border-radius: 1rem; }
body[data-card="beauty"] .card-media { border-radius: 0.85rem; }
body[data-card="beauty"] .rating { color: var(--store-accent); }
"""
        )
    elif cp == "auto":
        bits.append(
            """
body[data-card="auto"] .card { border-left: 3px solid var(--store-accent); border-radius: 6px; }
body[data-card="auto"] .card h3 { font-weight: 800; letter-spacing: -0.02em; }
"""
        )
    elif cp == "electronics":
        bits.append(
            """
body[data-card="electronics"] .card .price { font-variant-numeric: tabular-nums; }
body[data-card="electronics"] .card-meta { display: block; }
"""
        )
    elif cp == "food":
        bits.append(
            """
body[data-card="food"] .card-media { border-radius: 12px; }
body[data-card="food"] .card h3 { font-family: var(--font-display); }
"""
        )
    elif cp == "craft":
        bits.append(
            """
body[data-card="craft"] .card { border: 1px solid #e7e5e4; border-radius: 4px; }
body[data-card="craft"] .card h3 { font-family: var(--font-display); text-transform: uppercase; letter-spacing: 0.06em; font-size: 0.95rem; }
"""
        )
    elif cp == "furniture":
        bits.append(
            """
body[data-card="furniture"] .card-media { aspect-ratio: 16 / 10; }
body[data-card="furniture"] .card h3 { font-family: var(--font-display); }
"""
        )

    if preset.show_certs:
        bits.append(
            """
body[data-certs="1"] .hero-certs {
  display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.25rem;
}
body[data-certs="1"] .hero-certs span {
  border: 1px solid rgba(250,250,249,.35); padding: 0.35rem 0.65rem; font-size: 0.72rem;
  letter-spacing: 0.06em; text-transform: uppercase; border-radius: 2px;
}
"""
        )

    # Image slot placeholders (ready for R5 AI images)
    bits.append(
        """
.hero-media, .banner-media, .category-media, .product-media-slot {
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
}
.hero.has-hero-image {
  background-image:
    linear-gradient(105deg, rgba(12,10,9,.72) 0%, rgba(12,10,9,.25) 55%, transparent 100%),
    var(--store-hero-image);
  background-size: cover;
  background-position: center;
}
.card-media.has-product-image {
  background-image: var(--store-product-image);
  font-size: 0;
  color: transparent;
}
"""
    )
    return "\n".join(bits)


def ensure_image_slot_dirs(product_dir: Any) -> list[str]:
    """Create assets/images/ with slot README so R5 can drop files later."""
    from pathlib import Path

    root = Path(product_dir) / "assets" / "images"
    root.mkdir(parents=True, exist_ok=True)
    readme = root / "README_IMAGE_SLOTS.txt"
    readme.write_text(
        "Virtus Core AI Store — Commercial Gallery image slots\n"
        "====================================================\n"
        "hero.jpg      — homepage hero (seeded by store_media)\n"
        "banner.jpg    — promo / collection banner\n"
        "category.jpg  — category strip fallback\n"
        "product.jpg   — default product media\n"
        "product_N.jpg — per-SKU product photos\n"
        "\n"
        "KPI: «Купил бы я здесь товар?» — empty letter cards = FAIL.\n",
        encoding="utf-8",
    )
    return ["assets/images/README_IMAGE_SLOTS.txt"]


__all__ = [
    "ImageSlots",
    "STORE_CATEGORY_TO_NICHE",
    "StoreVisualPreset",
    "emit_store_root_css",
    "ensure_image_slot_dirs",
    "font_link_tags",
    "niche_store_css",
    "resolve_store_design",
    "store_category_to_niche_id",
    "store_colors_from_tokens",
    "visual_preset_for_category",
    "visual_preset_for_niche",
]
