"""Brand Style packs for Path A Factory — additive to niche colors & package tiers.

Client picks a brief style (Modern / Premium / …). Factory adjusts palette,
typography, radii, and buttons. Existing niche packs remain the default when
style is auto / unset.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


BRAND_STYLE_IDS = (
    "auto",
    "modern",
    "premium",
    "elegant",
    "minimal",
    "corporate",
    "friendly",
)


@dataclass(frozen=True)
class BrandStylePack:
    id: str
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str
    ink: str = "#0f172a"
    muted: str = "#64748b"
    surface: str = "#f8fafc"
    line: str = "#e2e8f0"
    font_body: str = '"Segoe UI", system-ui, -apple-system, sans-serif'
    font_display: str = '"Segoe UI", system-ui, -apple-system, sans-serif'
    radius: str = "12px"
    btn_radius: str = "999px"
    card_radius: str = "12px"
    shadow: str = "0 12px 24px rgba(0,0,0,0.08)"
    btn_weight: str = "700"
    letter_spacing: str = "-0.02em"


_PACKS: dict[str, BrandStylePack] = {
    "modern": BrandStylePack(
        id="modern",
        primary="#2563eb",
        primary_dark="#1e3a8a",
        accent="#38bdf8",
        hero_gradient="linear-gradient(145deg,#0f172a 0%,#1e40af 55%,#0369a1 100%)",
        font_body='"Inter", "Segoe UI", system-ui, sans-serif',
        font_display='"Inter", "Segoe UI", system-ui, sans-serif',
        radius="14px",
        btn_radius="12px",
        card_radius="14px",
        letter_spacing="-0.03em",
    ),
    "premium": BrandStylePack(
        id="premium",
        primary="#1c1917",
        primary_dark="#0c0a09",
        accent="#d4af37",
        hero_gradient="linear-gradient(160deg,#0c0a09 0%,#292524 50%,#44403c 100%)",
        ink="#1c1917",
        muted="#78716c",
        surface="#fafaf9",
        line="#e7e5e4",
        font_body='Georgia, "Times New Roman", serif',
        font_display='Georgia, "Times New Roman", serif',
        radius="6px",
        btn_radius="4px",
        card_radius="6px",
        shadow="0 16px 40px rgba(0,0,0,0.12)",
        letter_spacing="0.01em",
    ),
    "elegant": BrandStylePack(
        id="elegant",
        primary="#4c1d95",
        primary_dark="#2e1065",
        accent="#c4b5fd",
        hero_gradient="linear-gradient(150deg,#1e1b4b 0%,#4c1d95 60%,#6d28d9 100%)",
        surface="#faf5ff",
        line="#ede9fe",
        font_body='"Palatino Linotype", Palatino, Georgia, serif',
        font_display='"Palatino Linotype", Palatino, Georgia, serif',
        radius="10px",
        btn_radius="999px",
        card_radius="10px",
        letter_spacing="0.02em",
    ),
    "minimal": BrandStylePack(
        id="minimal",
        primary="#171717",
        primary_dark="#0a0a0a",
        accent="#a3a3a3",
        hero_gradient="linear-gradient(180deg,#171717 0%,#404040 100%)",
        ink="#171717",
        muted="#737373",
        surface="#ffffff",
        line="#e5e5e5",
        font_body='"Helvetica Neue", Helvetica, Arial, sans-serif',
        font_display='"Helvetica Neue", Helvetica, Arial, sans-serif',
        radius="2px",
        btn_radius="2px",
        card_radius="2px",
        shadow="none",
        btn_weight="600",
        letter_spacing="-0.04em",
    ),
    "corporate": BrandStylePack(
        id="corporate",
        primary="#0f766e",
        primary_dark="#115e59",
        accent="#5eead4",
        hero_gradient="linear-gradient(135deg,#042f2e 0%,#0f766e 55%,#134e4a 100%)",
        surface="#f0fdfa",
        line="#ccfbf1",
        font_body='"Segoe UI", Calibri, system-ui, sans-serif',
        font_display='"Segoe UI", Calibri, system-ui, sans-serif',
        radius="8px",
        btn_radius="8px",
        card_radius="8px",
        letter_spacing="-0.01em",
    ),
    "friendly": BrandStylePack(
        id="friendly",
        primary="#ea580c",
        primary_dark="#c2410c",
        accent="#fdba74",
        hero_gradient="linear-gradient(140deg,#7c2d12 0%,#ea580c 50%,#fb923c 100%)",
        ink="#431407",
        muted="#9a3412",
        surface="#fff7ed",
        line="#ffedd5",
        font_body='"Trebuchet MS", "Segoe UI", system-ui, sans-serif',
        font_display='"Trebuchet MS", "Segoe UI", system-ui, sans-serif',
        radius="18px",
        btn_radius="999px",
        card_radius="18px",
        shadow="0 10px 28px rgba(234,88,12,0.15)",
        letter_spacing="0",
    ),
}


def normalize_brand_style(raw: str | None) -> str:
    """Return pack id or 'auto' (keep niche defaults)."""
    key = (raw or "auto").strip().lower().replace(" ", "_").replace("-", "_")
    aliases = {
        "": "auto",
        "default": "auto",
        "niche": "auto",
        "none": "auto",
        "classic": "corporate",
        "lux": "premium",
        "luxury": "premium",
        "clean": "minimal",
        "warm": "friendly",
    }
    key = aliases.get(key, key)
    if key in _PACKS or key == "auto":
        return key
    return "auto"


def get_brand_style_pack(style_id: str | None) -> BrandStylePack | None:
    nid = normalize_brand_style(style_id)
    if nid == "auto":
        return None
    return _PACKS.get(nid)


def list_brand_styles(*, lang: str = "en") -> list[dict[str, str]]:
    """Public catalog for order UI."""
    labels = {
        "en": {
            "auto": ("Auto (niche default)", "Keep the niche palette — safest default."),
            "modern": ("Modern", "Clean blues, sharp UI, contemporary feel."),
            "premium": ("Premium", "Dark stone + gold accent, serif headlines."),
            "elegant": ("Elegant", "Violet tones, refined spacing."),
            "minimal": ("Minimal", "Near-monochrome, tight radii, quiet luxury."),
            "corporate": ("Corporate", "Teal trust palette, business-ready."),
            "friendly": ("Friendly", "Warm orange, soft cards, approachable."),
        },
        "de": {
            "auto": ("Auto (Nische)", "Farbwelt der Branche behalten — Standard."),
            "modern": ("Modern", "Klare Blautöne, zeitgemäßes UI."),
            "premium": ("Premium", "Dunkel + Gold, serife Überschriften."),
            "elegant": ("Elegant", "Violett, fein und ruhig."),
            "minimal": ("Minimal", "Fast monochrom, ruhig und klar."),
            "corporate": ("Corporate", "Petrol/Teal — vertrauenswürdig."),
            "friendly": ("Friendly", "Warmes Orange, einladende Karten."),
        },
        "ru": {
            "auto": ("Авто (ниша)", "Оставить палитру ниши — по умолчанию."),
            "modern": ("Modern", "Чистый синий, современный UI."),
            "premium": ("Premium", "Тёмный камень + золото, serif."),
            "elegant": ("Elegant", "Фиолетовые тона, спокойный ритм."),
            "minimal": ("Minimal", "Почти монохром, строгие углы."),
            "corporate": ("Corporate", "Бирюза доверия, деловой вид."),
            "friendly": ("Friendly", "Тёплый оранжевый, мягкие карточки."),
        },
        "uk": {
            "auto": ("Авто (ніша)", "Залишити палітру ніші — за замовчуванням."),
            "modern": ("Modern", "Чистий синій, сучасний UI."),
            "premium": ("Premium", "Темний камінь + золото, serif."),
            "elegant": ("Elegant", "Фіолетові тони, спокійний ритм."),
            "minimal": ("Minimal", "Майже монохром, строгі кути."),
            "corporate": ("Corporate", "Бірюза довіри, діловий вигляд."),
            "friendly": ("Friendly", "Теплий помаранчевий, м’які картки."),
        },
    }
    L = labels.get(lang) or labels["en"]
    out: list[dict[str, str]] = []
    for sid in BRAND_STYLE_IDS:
        title, hint = L.get(sid) or labels["en"][sid]
        out.append({"id": sid, "label": title, "hint": hint})
    return out


def apply_brand_to_build_style(base: Any, pack: BrandStylePack) -> Any:
    """Replace palette/gradient on BuildStyle-like object; keep type."""
    return type(base)(
        pack.primary,
        pack.primary_dark,
        pack.accent,
        pack.hero_gradient,
    )


def brand_style_extra_css(pack: BrandStylePack) -> str:
    """CSS overrides layered on top of tier + niche styles."""
    return f"""
    /* Brand Style: {pack.id} */
    body[data-brand="{pack.id}"] {{
      --ink: {pack.ink};
      --muted: {pack.muted};
      --surface: {pack.surface};
      --line: {pack.line};
      --radius: {pack.radius};
      --btn-radius: {pack.btn_radius};
      --card-radius: {pack.card_radius};
      font-family: {pack.font_body};
      color: var(--ink);
    }}
    body[data-brand="{pack.id}"] .hero h1,
    body[data-brand="{pack.id}"] .section h2 {{
      font-family: {pack.font_display};
      letter-spacing: {pack.letter_spacing};
    }}
    body[data-brand="{pack.id}"] .btn {{
      border-radius: var(--btn-radius);
      font-weight: {pack.btn_weight};
    }}
    body[data-brand="{pack.id}"] .service-card,
    body[data-brand="{pack.id}"] .process-card,
    body[data-brand="{pack.id}"] .faq-item,
    body[data-brand="{pack.id}"] .client-photo {{
      border-radius: var(--card-radius);
      box-shadow: {pack.shadow};
    }}
    body[data-brand="{pack.id}"] .brand img,
    body[data-brand="{pack.id}"] .brand .logo-fallback {{
      border-radius: {pack.radius};
    }}
    body[data-brand="{pack.id}"] .trust-pill {{
      border-radius: var(--btn-radius);
    }}
    body[data-brand="{pack.id}"] input,
    body[data-brand="{pack.id}"] textarea,
    body[data-brand="{pack.id}"] select,
    body[data-brand="{pack.id}"] .contact-form button {{
      border-radius: {pack.radius};
    }}
"""
