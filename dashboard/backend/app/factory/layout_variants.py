"""R2.2f — Layout Variants: composition profiles, not random shuffles.

Client · Package · Market · Niche
  → Layout Profile Resolver
  → Page Composition
  → Quality Gate
  → ZIP

Layout Profile owns structure (order, CTA strategy, trust position, footer).
Hero / Component / Trust composers remain the block engines; the profile
selects and places them so future Composer Engine works with profiles only.
"""

from __future__ import annotations

import hashlib
import html as html_lib
from dataclasses import dataclass
from typing import Any

PROFILE_IDS = ("L1", "L2", "L3", "L4", "L5", "L6")

BODY_SLOTS = (
    "info",
    "stats",
    "catalog",
    "services",
    "mid_cta",
    "benefits",
    "trust",
    "process",
    "showcase",
    "gallery",
    "about",
    "faq",
    "calculator",
    "reviews",
    "maps",
    "late_cta",
    "contact",
)


@dataclass(frozen=True)
class LayoutProfile:
    """One page composition language — structure + placement strategies."""

    id: str
    label: str
    hero_variants: tuple[str, ...]
    preferred_component: str | None
    cta_strategy: str
    services_layout: str
    trust_position: str
    gallery_style: str
    faq_style: str
    footer_variant: str
    section_order: tuple[str, ...]


LAYOUT_PROFILES: dict[str, LayoutProfile] = {
    "L1": LayoutProfile(
        id="L1",
        label="Classic service funnel",
        hero_variants=("A", "C", "E"),
        preferred_component="A",
        cta_strategy="early",
        services_layout="glass",
        trust_position="after_services",
        gallery_style="masonry",
        faq_style="rounded",
        footer_variant="compact",
        section_order=(
            "info",
            "stats",
            "catalog",
            "services",
            "mid_cta",
            "benefits",
            "trust",
            "process",
            "showcase",
            "gallery",
            "about",
            "faq",
            "calculator",
            "reviews",
            "maps",
            "contact",
        ),
    ),
    "L2": LayoutProfile(
        id="L2",
        label="Trust-first professional",
        hero_variants=("C", "A", "E"),
        preferred_component="C",
        cta_strategy="mid",
        services_layout="minimal",
        trust_position="after_benefits",
        gallery_style="feature_first",
        faq_style="accordion",
        footer_variant="legal",
        section_order=(
            "info",
            "trust",
            "stats",
            "catalog",
            "benefits",
            "services",
            "mid_cta",
            "gallery",
            "process",
            "showcase",
            "about",
            "faq",
            "reviews",
            "calculator",
            "maps",
            "contact",
        ),
    ),
    "L3": LayoutProfile(
        id="L3",
        label="Visual portfolio lead",
        hero_variants=("E", "A", "C"),
        preferred_component="A",
        cta_strategy="late",
        services_layout="glass",
        trust_position="after_gallery",
        gallery_style="masonry",
        faq_style="twocol",
        footer_variant="contact",
        section_order=(
            "info",
            "stats",
            "gallery",
            "showcase",
            "services",
            "benefits",
            "trust",
            "process",
            "catalog",
            "about",
            "faq",
            "reviews",
            "calculator",
            "maps",
            "late_cta",
            "contact",
        ),
    ),
    "L4": LayoutProfile(
        id="L4",
        label="Dense industrial / crafts",
        hero_variants=("B", "D", "F"),
        preferred_component="B",
        cta_strategy="dual",
        services_layout="solid",
        trust_position="after_services",
        gallery_style="grid",
        faq_style="twocol",
        footer_variant="split",
        section_order=(
            "info",
            "stats",
            "services",
            "mid_cta",
            "process",
            "benefits",
            "trust",
            "gallery",
            "showcase",
            "catalog",
            "about",
            "faq",
            "calculator",
            "reviews",
            "maps",
            "late_cta",
            "contact",
        ),
    ),
    "L5": LayoutProfile(
        id="L5",
        label="Contact-forward local",
        hero_variants=("A", "B", "F"),
        preferred_component="B",
        cta_strategy="early",
        services_layout="list",
        trust_position="before_contact",
        gallery_style="grid",
        faq_style="rounded",
        footer_variant="contact",
        section_order=(
            "info",
            "stats",
            "catalog",
            "services",
            "mid_cta",
            "benefits",
            "process",
            "showcase",
            "gallery",
            "about",
            "faq",
            "calculator",
            "reviews",
            "maps",
            "trust",
            "contact",
        ),
    ),
    "L6": LayoutProfile(
        id="L6",
        label="Editorial story",
        hero_variants=("C", "E", "A"),
        preferred_component="C",
        cta_strategy="mid",
        services_layout="minimal",
        trust_position="after_gallery",
        gallery_style="feature_first",
        faq_style="accordion",
        footer_variant="split",
        section_order=(
            "info",
            "about",
            "benefits",
            "services",
            "mid_cta",
            "gallery",
            "trust",
            "process",
            "showcase",
            "catalog",
            "stats",
            "faq",
            "reviews",
            "calculator",
            "maps",
            "contact",
        ),
    ),
}

NICHE_LAYOUT_POOL: dict[str, tuple[str, ...]] = {
    "dental": ("L1", "L2", "L6"),
    "auto": ("L4", "L5", "L1"),
    "law": ("L2", "L6", "L1"),
    "energy": ("L1", "L4", "L5"),
    "beauty": ("L3", "L6", "L1"),
    "green": ("L1", "L6", "L3"),
    "computer": ("L1", "L5", "L4"),
    "appliance": ("L5", "L4", "L1"),
    "handwerk": ("L4", "L5", "L1"),
    "generic": ("L1", "L2", "L3", "L5"),
}

MARKET_LAYOUT_BIAS: dict[str, tuple[str, ...]] = {
    "DE": ("L1", "L2", "L4"),
    "AT": ("L1", "L2", "L5"),
    "FR": ("L6", "L3", "L2"),
    "ES": ("L3", "L5", "L1"),
    "NL": ("L1", "L5", "L6"),
}


def get_layout_profile(profile_id: str) -> LayoutProfile:
    pid = (profile_id or "L1").strip().upper()
    return LAYOUT_PROFILES.get(pid) or LAYOUT_PROFILES["L1"]


def resolve_layout_profile(
    *,
    business_name: str,
    package_id: str,
    market_code: str,
    niche_id: str,
) -> LayoutProfile:
    """Deterministic Layout Profile from Client × Package × Market × Niche."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    market = (market_code or "DE").strip().upper() or "DE"
    package = (package_id or "basic").strip().lower() or "basic"
    niche_pool = NICHE_LAYOUT_POOL.get(niche) or NICHE_LAYOUT_POOL["generic"]
    market_bias = MARKET_LAYOUT_BIAS.get(market) or ()
    ordered: list[str] = []
    for pid in market_bias + niche_pool:
        if pid in niche_pool and pid not in ordered:
            ordered.append(pid)
    for pid in niche_pool:
        if pid not in ordered:
            ordered.append(pid)
    if package == "basic" and len(ordered) > 2:
        ordered = ordered[: max(2, len(ordered) - 1)]
    seed = f"{business_name.strip()}|{package}|{niche}|{market}|layout-profile"
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    pick = ordered[int(digest[:8], 16) % len(ordered)]
    return get_layout_profile(pick)


def resolve_hero_for_layout(
    profile: LayoutProfile,
    *,
    niche_id: str,
    business_name: str,
    package_id: str,
) -> str:
    """Hero from profile.hero_variants ∩ niche allowlist (fallback: niche pool).

    R3.1: Premium always uses cinematic compositions (B/D/F) — product class,
    not a niche twin of Basic. Basic prefers simple A/C when available.
    """
    from app.factory.hero_composer import NICHE_LAYOUT_ALLOWLIST
    from app.factory.landing_tier_css import BASIC_HERO_PREFER, PREMIUM_HERO_POOL

    niche = (niche_id or "generic").strip().lower() or "generic"
    package = (package_id or "basic").strip().lower() or "basic"
    niche_pool = NICHE_LAYOUT_ALLOWLIST.get(niche) or NICHE_LAYOUT_ALLOWLIST["generic"]

    if package == "premium":
        pool = PREMIUM_HERO_POOL
        seed = f"{business_name.strip()}|premium|{niche}|cinematic-hero"
    elif package == "basic":
        preferred = tuple(h for h in BASIC_HERO_PREFER if h in niche_pool)
        pool = preferred or tuple(
            h for h in profile.hero_variants if h in niche_pool
        ) or niche_pool
        seed = (
            f"{business_name.strip()}|basic|{niche}|{profile.id}|layout-hero"
        )
    else:
        pool = tuple(h for h in profile.hero_variants if h in niche_pool) or niche_pool
        seed = (
            f"{business_name.strip()}|{package}|{niche}|"
            f"{profile.id}|layout-hero"
        )
    digest = hashlib.sha256(seed.encode("utf-8")).hexdigest()
    return pool[int(digest[:8], 16) % len(pool)]


def resolve_component_for_layout(
    profile: LayoutProfile,
    *,
    hero_layout: str,
    business_name: str,
    package_id: str,
    niche_id: str,
) -> str:
    """Prefer profile.component when hero-compatible; else Component Composer."""
    from app.factory.component_composer import (
        HERO_PROFILE_COMPAT,
        select_component_profile,
    )

    hero = (hero_layout or "A").strip().upper()
    compat = HERO_PROFILE_COMPAT.get(hero) or ("A",)
    preferred = (profile.preferred_component or "").strip().upper()
    if preferred and preferred in compat:
        return preferred
    return select_component_profile(
        hero_layout=hero,
        business_name=business_name,
        package_id=package_id,
        niche_id=niche_id,
    )


def style_overrides(profile: LayoutProfile) -> dict[str, str | None]:
    services = profile.services_layout
    gallery = profile.gallery_style
    faq = profile.faq_style
    return {
        "cards": None if services == "auto" else services,
        "gallery": None if gallery == "auto" else gallery,
        "faq": None if faq == "auto" else faq,
    }


def assemble_body(sections: dict[str, str], order: tuple[str, ...] | list[str]) -> str:
    """Join non-empty section HTML in profile order."""
    parts: list[str] = []
    seen: set[str] = set()
    for key in order:
        if key in seen:
            continue
        seen.add(key)
        chunk = (sections.get(key) or "").strip()
        if chunk:
            parts.append(chunk)
    for key, chunk in sections.items():
        if key in seen:
            continue
        text = (chunk or "").strip()
        if text:
            parts.append(text)
    return "\n".join(parts)


def compose_footer(
    *,
    variant: str,
    business_name: str,
    ui: dict[str, str],
    phone: str = "",
    email: str = "",
    city: str = "",
    market_profile: Any = None,
) -> str:
    """Build footer HTML.

    R3.4.1.3: when ``market_profile`` is provided (MarketProfile or dict from
    CompositionResult), legal links come only from that profile — Footer does
    not call resolve() and does not invent country rules.
    """
    esc = html_lib.escape
    business = esc(business_name)
    legal = _footer_legal_html(ui=ui, market_profile=market_profile)
    v = (variant or "compact").strip().lower()
    if v == "contact":
        bits = [f"<strong>{business}</strong>"]
        if phone:
            bits.append(esc(phone))
        if email:
            bits.append(esc(email))
        if city:
            bits.append(esc(city))
        return (
            f'<footer class="footer-contact" data-footer-variant="contact"'
            f'{_footer_profile_attrs(market_profile)}>'
            f'<div class="footer-contact-row">{" · ".join(bits)}</div>'
            f"<div>{legal}</div>"
            f'<p class="footer-copy">© {business}</p>'
            f"</footer>"
        )
    if v == "split":
        left = (
            f"<div><strong>{business}</strong><br>"
            f'<span class="muted">© {business}</span></div>'
        )
        right = f'<div class="footer-legal">{legal}</div>'
        return (
            f'<footer class="footer-split" data-footer-variant="split"'
            f'{_footer_profile_attrs(market_profile)}>'
            f'<div class="footer-split-grid">{left}{right}</div>'
            f"</footer>"
        )
    if v == "legal":
        return (
            f'<footer class="footer-legal-heavy" data-footer-variant="legal"'
            f'{_footer_profile_attrs(market_profile)}>'
            f"<p>{business} · © {business}</p>"
            f'<nav class="footer-legal-nav">{legal}</nav>'
            f"</footer>"
        )
    return (
        f'<footer data-footer-variant="compact"'
        f'{_footer_profile_attrs(market_profile)}>'
        f"{business} · © {business}<br>"
        f"{legal}"
        f"</footer>"
    )


def _coerce_market_profile(market_profile: Any) -> Any:
    from app.factory.market_profile import coerce_market_profile

    return coerce_market_profile(market_profile)


def _footer_profile_attrs(market_profile: Any) -> str:
    profile = _coerce_market_profile(market_profile)
    if profile is None:
        return ""
    esc = html_lib.escape
    keys = ",".join(profile.legal_footer_keys)
    return (
        f' data-market="{esc(profile.market_code)}"'
        f' data-legal-keys="{esc(keys)}"'
    )


def _footer_legal_html(*, ui: dict[str, str], market_profile: Any) -> str:
    esc = html_lib.escape
    profile = _coerce_market_profile(market_profile)
    if profile is not None:
        from app.factory.market_profile import legal_link_pairs

        pairs = legal_link_pairs(profile)
        if not pairs:
            return ""
        bits = []
        for i, (label, href) in enumerate(pairs):
            margin = ' style="color:#94a3b8;margin-right:0.75rem"' if i < len(pairs) - 1 else ' style="color:#94a3b8"'
            bits.append(f'<a href="{esc(href)}"{margin}>{esc(label)}</a>')
        return "".join(bits)
    # Legacy path (Landing Builder without profile) — keep ui legal_a/b
    return (
        f'<a href="{esc(ui["legal_a_href"])}" style="color:#94a3b8;margin-right:0.75rem">'
        f'{esc(ui["legal_a"])}</a>'
        f'<a href="{esc(ui["legal_b_href"])}" style="color:#94a3b8">{esc(ui["legal_b"])}</a>'
    )


def layout_profile_css(profile: LayoutProfile) -> str:
    return (
        "    /* Layout Variants R2.2f */\n"
        f'    body[data-layout-profile="{profile.id}"] '
        f'{{ --layout-cta: "{profile.cta_strategy}"; }}\n'
        "    .services-list { list-style:none; margin:0; padding:0; "
        "display:flex; flex-direction:column; gap:0.35rem; }\n"
        "    .svc-row { border-bottom:1px solid rgba(15,23,42,.08); "
        "padding:0.85rem 0; }\n"
        "    .svc-row h3 { margin:0 0 0.25rem; font-size:1.05rem; }\n"
        "    .footer-split-grid { display:grid; grid-template-columns:1fr 1fr; "
        "gap:1.5rem; align-items:start; }\n"
        "    .footer-contact-row { margin-bottom:0.75rem; }\n"
        "    @media (max-width:720px) { .footer-split-grid { grid-template-columns:1fr; } }\n"
    )


def profile_as_dict(profile: LayoutProfile) -> dict[str, Any]:
    return {
        "id": profile.id,
        "label": profile.label,
        "hero_variants": list(profile.hero_variants),
        "preferred_component": profile.preferred_component,
        "cta_strategy": profile.cta_strategy,
        "services_layout": profile.services_layout,
        "trust_position": profile.trust_position,
        "gallery_style": profile.gallery_style,
        "faq_style": profile.faq_style,
        "footer_variant": profile.footer_variant,
        "section_order": list(profile.section_order),
    }
