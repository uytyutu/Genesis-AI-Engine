"""R2.2b-intl — International Design Engine for Path A landings.

Market profiles change density, typography, measure, CTA sizing, and SEO locale —
not only translated strings. Static HTML + CSS only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass

from app.factory.market_delivery import normalize_market

MARKET_PROFILE_IDS = ("DE", "AT", "FR", "ES", "NL")


@dataclass(frozen=True)
class MarketDesignProfile:
    market_id: str
    label: str
    html_lang: str
    og_locale: str
    hreflang: str
    # Layout / typography (CSS values)
    density: str  # compact | comfortable | airy
    measure_ch: str
    section_pad_y: str
    hero_pad_extra: str
    hero_min_boost: str
    card_pad: str
    btn_pad: str
    btn_min_width: str
    h1_clamp: str
    h1_line_height: str
    h1_tracking: str
    body_size: str
    gap_scale: str
    surface_tint: str
    accent_filter: str
    trust_weight: str
    phone_placeholder: str
    word_break: str
    hyphens: str


# Registry — add markets without changing selection logic.
MARKET_DESIGN_PROFILES: dict[str, MarketDesignProfile] = {
    "DE": MarketDesignProfile(
        market_id="DE",
        label="Germany — strict trust",
        html_lang="de",
        og_locale="de_DE",
        hreflang="de-DE",
        density="compact",
        measure_ch="62ch",
        section_pad_y="3.25rem",
        hero_pad_extra="0.25rem",
        hero_min_boost="0vh",
        card_pad="1.15rem",
        btn_pad="0.8rem 1.65rem",
        btn_min_width="9.5rem",
        h1_clamp="clamp(1.85rem, 3.8vw, 2.65rem)",
        h1_line_height="1.18",
        h1_tracking="-0.015em",
        body_size="1rem",
        gap_scale="0.95",
        surface_tint="#f8fafc",
        accent_filter="none",
        trust_weight="700",
        phone_placeholder="+49 …",
        word_break="normal",
        hyphens="auto",
    ),
    "AT": MarketDesignProfile(
        market_id="AT",
        label="Austria — DE structure, warmer tone",
        html_lang="de",
        og_locale="de_AT",
        hreflang="de-AT",
        density="compact",
        measure_ch="62ch",
        section_pad_y="3.35rem",
        hero_pad_extra="0.35rem",
        hero_min_boost="0vh",
        card_pad="1.2rem",
        btn_pad="0.85rem 1.7rem",
        btn_min_width="9.5rem",
        h1_clamp="clamp(1.9rem, 3.9vw, 2.7rem)",
        h1_line_height="1.2",
        h1_tracking="-0.01em",
        body_size="1.02rem",
        gap_scale="1",
        surface_tint="#faf7f2",
        accent_filter="saturate(1.05)",
        trust_weight="700",
        phone_placeholder="+43 …",
        word_break="normal",
        hyphens="auto",
    ),
    "FR": MarketDesignProfile(
        market_id="FR",
        label="France — airy aesthetic",
        html_lang="fr",
        og_locale="fr_FR",
        hreflang="fr-FR",
        density="airy",
        measure_ch="58ch",
        section_pad_y="4.25rem",
        hero_pad_extra="1.25rem",
        hero_min_boost="4vh",
        card_pad="1.55rem",
        btn_pad="0.95rem 2.1rem",
        btn_min_width="11rem",
        h1_clamp="clamp(2.05rem, 4.4vw, 3.1rem)",
        h1_line_height="1.22",
        h1_tracking="0.01em",
        body_size="1.05rem",
        gap_scale="1.2",
        surface_tint="#fbfaf8",
        accent_filter="saturate(1.08)",
        trust_weight="600",
        phone_placeholder="+33 …",
        word_break="normal",
        hyphens="auto",
    ),
    "ES": MarketDesignProfile(
        market_id="ES",
        label="Spain — open & emotive",
        html_lang="es",
        og_locale="es_ES",
        hreflang="es-ES",
        density="comfortable",
        measure_ch="60ch",
        section_pad_y="3.85rem",
        hero_pad_extra="0.85rem",
        hero_min_boost="3vh",
        card_pad="1.4rem",
        btn_pad="1rem 2.25rem",
        btn_min_width="12rem",
        h1_clamp="clamp(2rem, 4.2vw, 3rem)",
        h1_line_height="1.2",
        h1_tracking="0",
        body_size="1.04rem",
        gap_scale="1.15",
        surface_tint="#fffaf5",
        accent_filter="saturate(1.22) contrast(1.04)",
        trust_weight="650",
        phone_placeholder="+34 …",
        word_break="normal",
        hyphens="auto",
    ),
    "NL": MarketDesignProfile(
        market_id="NL",
        label="Netherlands — practical minimal",
        html_lang="nl",
        og_locale="nl_NL",
        hreflang="nl-NL",
        density="comfortable",
        measure_ch="64ch",
        section_pad_y="3.1rem",
        hero_pad_extra="0.15rem",
        hero_min_boost="0vh",
        card_pad="1.1rem",
        btn_pad="0.75rem 1.5rem",
        btn_min_width="9rem",
        h1_clamp="clamp(1.8rem, 3.6vw, 2.55rem)",
        h1_line_height="1.16",
        h1_tracking="-0.02em",
        body_size="0.98rem",
        gap_scale="0.9",
        surface_tint="#f7fafc",
        accent_filter="saturate(0.95)",
        trust_weight="600",
        phone_placeholder="+31 …",
        word_break="normal",
        hyphens="auto",
    ),
}

# Fallback markets → nearest design profile (language may still differ via i18n).
_MARKET_ALIASES: dict[str, str] = {
    "CH": "DE",
    "BE": "NL",
    "US": "NL",
    "GB": "NL",
    "IE": "NL",
    "CA": "NL",
    "AU": "NL",
    "NZ": "NL",
    "IT": "FR",
    "PT": "ES",
    "PL": "DE",
    "CZ": "DE",
    "SK": "DE",
    "RO": "DE",
    "UA": "DE",
    "RU": "DE",
}


def resolve_market_design(market_code: str | None) -> MarketDesignProfile:
    code = normalize_market(market_code)
    if code in MARKET_DESIGN_PROFILES:
        return MARKET_DESIGN_PROFILES[code]
    alias = _MARKET_ALIASES.get(code, "DE")
    return MARKET_DESIGN_PROFILES[alias]


def market_design_extra_css(profile: MarketDesignProfile) -> str:
    p = profile
    return f"""
    /* International Design Engine — {p.market_id}: {p.label} */
    body[data-market="{p.market_id}"] {{
      --market-measure: {p.measure_ch};
      --market-section-pad: {p.section_pad_y};
      --market-card-pad: {p.card_pad};
      --market-btn-pad: {p.btn_pad};
      --market-btn-min: {p.btn_min_width};
      --market-gap: {p.gap_scale};
      --market-surface: {p.surface_tint};
      font-size: {p.body_size};
      -webkit-hyphens: {p.hyphens};
      hyphens: {p.hyphens};
      overflow-wrap: anywhere;
      word-break: {p.word_break};
    }}
    body[data-market="{p.market_id}"] .section {{
      padding-top: var(--market-section-pad);
      padding-bottom: var(--market-section-pad);
    }}
    body[data-market="{p.market_id}"] .hero {{
      padding-block: calc(2.5rem + {p.hero_pad_extra});
    }}
    body[data-market="{p.market_id}"] .hero h1 {{
      font-size: {p.h1_clamp};
      line-height: {p.h1_line_height};
      letter-spacing: {p.h1_tracking};
      max-width: var(--market-measure);
      overflow-wrap: break-word;
      hyphens: {p.hyphens};
    }}
    body[data-market="{p.market_id}"] .hero p.lead {{
      max-width: var(--market-measure);
      overflow-wrap: break-word;
    }}
    body[data-market="{p.market_id}"] .btn {{
      padding: var(--market-btn-pad);
      min-width: var(--market-btn-min);
      max-width: 100%;
      white-space: normal;
      text-align: center;
      line-height: 1.25;
      overflow-wrap: break-word;
    }}
    body[data-market="{p.market_id}"] .svc-card,
    body[data-market="{p.market_id}"] .service-card,
    body[data-market="{p.market_id}"] .faq-bubble,
    body[data-market="{p.market_id}"] .faq-panel,
    body[data-market="{p.market_id}"] .faq-item,
    body[data-market="{p.market_id}"] .process-card,
    body[data-market="{p.market_id}"] .product-card {{
      padding: var(--market-card-pad);
    }}
    body[data-market="{p.market_id}"] .services,
    body[data-market="{p.market_id}"] .services-glass,
    body[data-market="{p.market_id}"] .services-solid,
    body[data-market="{p.market_id}"] .ben-circles,
    body[data-market="{p.market_id}"] .process-grid {{
      gap: calc(1rem * var(--market-gap));
    }}
    body[data-market="{p.market_id}"] .about,
    body[data-market="{p.market_id}"] .benefits {{
      background-color: var(--market-surface);
    }}
    body[data-market="{p.market_id}"] .trust-pill,
    body[data-market="{p.market_id}"] .trust-strip {{
      font-weight: {p.trust_weight};
    }}
    body[data-market="{p.market_id}"] .btn,
    body[data-market="{p.market_id}"] .mid-cta {{
      filter: {p.accent_filter};
    }}
    body[data-market="{p.market_id}"][data-density="airy"] .hero-ctas {{
      gap: 1.1rem;
    }}
    body[data-market="{p.market_id}"][data-density="compact"] .section h2 {{
      letter-spacing: -0.01em;
    }}
"""


def build_seo_localization(
    *,
    profile: MarketDesignProfile,
    page_title: str,
    meta_description: str,
    business_name: str,
    subtitle: str,
    phone: str,
    email: str,
    city: str,
    market_code: str,
    extended: bool,
) -> str:
    """lang/hreflang always; OG + Schema when extended SEO is on."""
    esc_title = _xml_esc(page_title)
    esc_desc = _xml_esc(meta_description)
    parts = [
        f'  <link rel="canonical" href="./">',
        f'  <link rel="alternate" hreflang="{profile.hreflang}" href="./">',
        '  <link rel="alternate" hreflang="x-default" href="./">',
    ]
    if not extended:
        return "\n".join(parts)
    ld = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": business_name,
        "description": subtitle[:200],
        "telephone": phone,
        "email": email,
        "inLanguage": profile.html_lang,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": city or "",
            "addressCountry": normalize_market(market_code),
        },
    }
    parts.extend(
        [
            '  <meta name="robots" content="index,follow">',
            f'  <meta property="og:title" content="{esc_title}">',
            f'  <meta property="og:description" content="{esc_desc}">',
            '  <meta property="og:type" content="website">',
            f'  <meta property="og:locale" content="{profile.og_locale}">',
            f'  <script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>',
        ]
    )
    return "\n".join(parts)


_FORBIDDEN_LOCALIZATION = (
    "lorem ipsum",
    "loremipsum",
    "todo:",
    "fixme",
    "null",
    "undefined",
    "your company",
    "sample text",
    "placeholder text",
    "demo content",
    "preview only",
)


def assert_localization_hygiene(html: str) -> None:
    """Raise if English stubs / unfinished localization leak into deliverable."""
    lower = html.lower()
    for needle in _FORBIDDEN_LOCALIZATION:
        if needle in lower:
            raise ValueError(f"localization_hygiene:{needle}")
    # Unresolved i18n-style keys
    if re.search(r"\bui\.[a-z0-9_]+\b", html, flags=re.I):
        raise ValueError("localization_hygiene:ui_key")
    if re.search(r"\{\{[^{}]+\}\}", html):
        raise ValueError("localization_hygiene:mustache")


def _xml_esc(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )
