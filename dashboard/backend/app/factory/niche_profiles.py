"""Niche design profiles for Path A Factory landings.

Gate 1: in-code profiles (niche_id → full design system). Horizon: load
factory/themes/{niche_id}/config.json without changing build_landing call shape —
only resolve_niche_profile() grows.

R2.1: niches are not color swaps — typography, radii, surfaces differ so dental
vs auto vs law read as different agency products.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NicheStyle:
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
    letter_spacing: str = "-0.02em"
    btn_weight: str = "700"


@dataclass(frozen=True)
class NicheProfile:
    niche_id: str
    label_de: str
    style: NicheStyle


# Path A industry systems — fonts/radii/surfaces are part of identity, not optional.
_PROFILES: dict[str, NicheProfile] = {
    "auto": NicheProfile(
        "auto",
        "Autowerkstatt",
        NicheStyle(
            primary="#b91c1c",
            primary_dark="#7f1d1d",
            accent="#f87171",
            hero_gradient="linear-gradient(135deg,#0a0a0a 0%,#1c1917 45%,#b91c1c 100%)",
            ink="#0c0a09",
            muted="#78716c",
            surface="#f5f5f4",
            line="#e7e5e4",
            font_body='"Segoe UI", "Helvetica Neue", Arial, sans-serif',
            font_display='"Segoe UI", "Helvetica Neue", Arial, sans-serif',
            radius="6px",
            btn_radius="6px",
            card_radius="8px",
            shadow="0 16px 32px rgba(0,0,0,0.14)",
            letter_spacing="-0.03em",
            btn_weight="800",
        ),
    ),
    "dental": NicheProfile(
        "dental",
        "Zahnmedizin",
        NicheStyle(
            primary="#0284c7",
            primary_dark="#0369a1",
            accent="#e0f2fe",
            hero_gradient="linear-gradient(135deg,#0369a1 0%,#0ea5e9 55%,#38bdf8 100%)",
            ink="#0c4a6e",
            muted="#64748b",
            surface="#f0f9ff",
            line="#bae6fd",
            font_body='"Segoe UI", system-ui, -apple-system, sans-serif',
            font_display='"Segoe UI", system-ui, -apple-system, sans-serif',
            radius="16px",
            btn_radius="999px",
            card_radius="18px",
            shadow="0 10px 28px rgba(3,105,161,0.10)",
            letter_spacing="-0.02em",
            btn_weight="700",
        ),
    ),
    "law": NicheProfile(
        "law",
        "Kanzlei",
        NicheStyle(
            primary="#1e3a5f",
            primary_dark="#0f172a",
            accent="#c9a227",
            hero_gradient="linear-gradient(135deg,#0f172a 0%,#1e3a5f 70%,#334155 100%)",
            ink="#0f172a",
            muted="#64748b",
            surface="#f8fafc",
            line="#e2e8f0",
            font_body='"Segoe UI", Calibri, system-ui, sans-serif',
            font_display='Georgia, "Times New Roman", serif',
            radius="4px",
            btn_radius="4px",
            card_radius="6px",
            shadow="0 8px 20px rgba(15,23,42,0.08)",
            letter_spacing="0.01em",
            btn_weight="600",
        ),
    ),
    "beauty": NicheProfile(
        "beauty",
        "Salon",
        NicheStyle(
            primary="#be185d",
            primary_dark="#9d174d",
            accent="#fbcfe8",
            hero_gradient="linear-gradient(150deg,#831843 0%,#be185d 50%,#db2777 100%)",
            ink="#500724",
            muted="#9d174d",
            surface="#fdf2f8",
            line="#fbcfe8",
            font_body='"Segoe UI", "Helvetica Neue", system-ui, sans-serif',
            font_display='Georgia, "Palatino Linotype", Palatino, serif',
            radius="14px",
            btn_radius="999px",
            card_radius="16px",
            shadow="0 14px 36px rgba(190,24,93,0.12)",
            letter_spacing="0.02em",
            btn_weight="600",
        ),
    ),
    "energy": NicheProfile(
        "energy",
        "Photovoltaik",
        NicheStyle(
            primary="#16a34a",
            primary_dark="#15803d",
            accent="#facc15",
            hero_gradient="linear-gradient(135deg,#14532d 0%,#16a34a 50%,#ca8a04 100%)",
            ink="#14532d",
            muted="#4d7c0f",
            surface="#f7fee7",
            line="#d9f99d",
            font_body='"Segoe UI", system-ui, -apple-system, sans-serif',
            font_display='"Segoe UI", system-ui, -apple-system, sans-serif',
            radius="18px",
            btn_radius="14px",
            card_radius="20px",
            shadow="0 12px 30px rgba(22,163,74,0.12)",
            letter_spacing="-0.01em",
            btn_weight="700",
        ),
    ),
    "green": NicheProfile(
        "green",
        "Garten",
        NicheStyle("#22c55e", "#166534", "#86efac", "linear-gradient(135deg,#14532d,#22c55e)"),
    ),
    "computer": NicheProfile(
        "computer",
        "PC-Service",
        NicheStyle("#0369a1", "#0c4a6e", "#38bdf8", "linear-gradient(135deg,#0f172a,#0284c7)"),
    ),
    "appliance": NicheProfile(
        "appliance",
        "Hausgeräte",
        NicheStyle("#475569", "#1e293b", "#94a3b8", "linear-gradient(135deg,#0f172a,#475569)"),
    ),
    "handwerk": NicheProfile(
        "handwerk",
        "Handwerk",
        NicheStyle("#b45309", "#78350f", "#fbbf24", "linear-gradient(135deg,#1c1917,#b45309)"),
    ),
    "generic": NicheProfile(
        "generic",
        "Lokalgeschäft",
        NicheStyle("#334155", "#0f172a", "#38bdf8", "linear-gradient(135deg,#0f172a,#334155)"),
    ),
}


def resolve_niche_profile(niche_id: str | None) -> NicheProfile:
    """Extension point for tomorrow: niche_id from order / site analysis → profile."""
    key = (niche_id or "generic").strip().lower() or "generic"
    return _PROFILES.get(key, _PROFILES["generic"])


def known_niche_ids() -> tuple[str, ...]:
    return tuple(sorted(_PROFILES.keys()))


def niche_style_extra_css(profile: NicheProfile) -> str:
    """CSS overrides so each niche reads as its own design system (not a recolor)."""
    s = profile.style
    nid = profile.niche_id
    return f"""
    /* Niche Design System: {nid} */
    body[data-niche="{nid}"] {{
      --p: {s.primary};
      --pd: {s.primary_dark};
      --acc: {s.accent};
      --ink: {s.ink};
      --muted: {s.muted};
      --surface: {s.surface};
      --line: {s.line};
      --radius: {s.radius};
      --btn-radius: {s.btn_radius};
      --card-radius: {s.card_radius};
      font-family: {s.font_body};
      color: var(--ink);
    }}
    body[data-niche="{nid}"] .hero h1,
    body[data-niche="{nid}"] .section h2 {{
      font-family: {s.font_display};
      letter-spacing: {s.letter_spacing};
    }}
    body[data-niche="{nid}"] .btn {{
      border-radius: var(--btn-radius);
      font-weight: {s.btn_weight};
    }}
    body[data-niche="{nid}"] .service-card,
    body[data-niche="{nid}"] .process-card,
    body[data-niche="{nid}"] .faq-item,
    body[data-niche="{nid}"] .client-photo,
    body[data-niche="{nid}"] .product-card,
    body[data-niche="{nid}"] .mid-cta {{
      border-radius: var(--card-radius);
      box-shadow: {s.shadow};
    }}
    body[data-niche="{nid}"] .brand img,
    body[data-niche="{nid}"] .brand .logo-fallback {{
      border-radius: {s.radius};
    }}
    body[data-niche="{nid}"] .trust-pill {{
      border-radius: var(--btn-radius);
    }}
    body[data-niche="{nid}"] input,
    body[data-niche="{nid}"] textarea,
    body[data-niche="{nid}"] select,
    body[data-niche="{nid}"] .contact-form button {{
      border-radius: {s.radius};
    }}
"""
