"""Font packs for Path A landings — Google Fonts with system fallbacks.

Store Factory already uses DM Sans + Fraunces; Website Factory aligns so
both products share one Virtus Core type language.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FontPack:
    """CSS stacks + optional Google Fonts stylesheet URL."""

    body: str
    display: str
    google_css_url: str | None = None
    label: str = "system"


# Shared URL fragments (opsz axes kept for optical sizing where available).
_DM_SANS = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;"
    "1,9..40,400&display=swap"
)
_FRAUNCES_DM = (
    "https://fonts.googleapis.com/css2?"
    "family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;"
    "1,9..40,400&family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700&display=swap"
)
_LIBRE_SOURCE = (
    "https://fonts.googleapis.com/css2?"
    "family=Libre+Baskerville:wght@400;700&family=Source+Sans+3:ital,wght@"
    "0,400;0,600;0,700;1,400&display=swap"
)
_CORMORANT_DM = (
    "https://fonts.googleapis.com/css2?"
    "family=Cormorant+Garamond:wght@500;600;700&family=DM+Sans:opsz,wght@"
    "9..40,400;9..40,500;9..40,600;9..40,700&display=swap"
)
_BARLOW_DM = (
    "https://fonts.googleapis.com/css2?"
    "family=Barlow+Condensed:wght@600;700;800&family=DM+Sans:opsz,wght@"
    "9..40,400;9..40,500;9..40,600;9..40,700&display=swap"
)
_OSWALD_SOURCE = (
    "https://fonts.googleapis.com/css2?"
    "family=Oswald:wght@500;600;700&family=Source+Sans+3:ital,wght@"
    "0,400;0,600;0,700;1,400&display=swap"
)
_SOURCE_SERIF_SANS = (
    "https://fonts.googleapis.com/css2?"
    "family=Source+Serif+4:opsz,wght@8..60,500;8..60,600;8..60,700&"
    "family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400&display=swap"
)

_SYSTEM_SANS = '"DM Sans", "Segoe UI", system-ui, -apple-system, sans-serif'
_SYSTEM_SERIF = 'Georgia, "Times New Roman", serif'

_SYNE_FIGTREE = (
    "https://fonts.googleapis.com/css2?"
    "family=Syne:wght@600;700;800&family=Figtree:ital,wght@"
    "0,400;0,500;0,600;0,700;1,400&display=swap"
)
_PLAYFAIR_MANROPE = (
    "https://fonts.googleapis.com/css2?"
    "family=Playfair+Display:wght@500;600;700&family=Manrope:wght@"
    "400;500;600;700&display=swap"
)
_BEBAS_OUTFIT = (
    "https://fonts.googleapis.com/css2?"
    "family=Bebas+Neue&family=Outfit:wght@400;500;600;700&display=swap"
)

FONT_PACKS: dict[str, FontPack] = {
    "restaurant": FontPack(
        body='"Figtree", "Segoe UI", system-ui, sans-serif',
        display='"Playfair Display", Georgia, "Times New Roman", serif',
        google_css_url=(
            "https://fonts.googleapis.com/css2?"
            "family=Playfair+Display:wght@500;600;700&family=Figtree:wght@"
            "400;500;600;700&display=swap"
        ),
        label="restaurant",
    ),
    "handwerk": FontPack(
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        display='"Oswald", "Arial Narrow", Impact, sans-serif',
        google_css_url=_OSWALD_SOURCE,
        label="handwerk",
    ),
    "dental": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="dental",
    ),
    "law": FontPack(
        body='"Source Sans 3", Calibri, "Segoe UI", system-ui, sans-serif',
        display='"Libre Baskerville", Georgia, "Times New Roman", serif',
        google_css_url=_LIBRE_SOURCE,
        label="law",
    ),
    "beauty": FontPack(
        body='"Manrope", "Helvetica Neue", system-ui, sans-serif',
        display='"Cormorant Garamond", Georgia, Palatino, serif',
        google_css_url=(
            "https://fonts.googleapis.com/css2?"
            "family=Cormorant+Garamond:wght@500;600;700&family=Manrope:wght@"
            "400;500;600;700&display=swap"
        ),
        label="beauty",
    ),
    "psychology": FontPack(
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        display='"Cormorant Garamond", Georgia, "Times New Roman", serif',
        google_css_url=_CORMORANT_DM,
        label="psychology",
    ),
    "fashion": FontPack(
        body='"Figtree", "Helvetica Neue", Arial, sans-serif',
        display='"Syne", Georgia, "Times New Roman", sans-serif',
        google_css_url=_SYNE_FIGTREE,
        label="fashion",
    ),
    "auto": FontPack(
        body='"Outfit", "Helvetica Neue", Arial, sans-serif',
        display='"Bebas Neue", "Arial Narrow", Impact, sans-serif',
        google_css_url=_BEBAS_OUTFIT,
        label="auto",
    ),
    "auto_ankauf": FontPack(
        body='"Outfit", "Helvetica Neue", Arial, sans-serif',
        display='"Bebas Neue", "Arial Narrow", Impact, sans-serif',
        google_css_url=_BEBAS_OUTFIT,
        label="auto_ankauf",
    ),
    "energy": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="energy",
    ),
    "photography": FontPack(
        body='"DM Sans", "Segoe UI", system-ui, sans-serif',
        display='"Source Serif 4", Georgia, "Times New Roman", serif',
        google_css_url=_SOURCE_SERIF_SANS,
        label="photography",
    ),
    "accounting": FontPack(
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        display='"Source Serif 4", Georgia, serif',
        google_css_url=_SOURCE_SERIF_SANS,
        label="accounting",
    ),
    "green": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="green",
    ),
    "computer": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="computer",
    ),
    "appliance": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="appliance",
    ),
    "cleaning": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="cleaning",
    ),
    "fitness": FontPack(
        body='"DM Sans", "Segoe UI", system-ui, sans-serif',
        display='"Oswald", "Arial Narrow", sans-serif',
        google_css_url=_OSWALD_SOURCE,
        label="fitness",
    ),
    "realestate": FontPack(
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        display='"Libre Baskerville", Georgia, serif',
        google_css_url=_LIBRE_SOURCE,
        label="realestate",
    ),
    "generic": FontPack(
        body=_SYSTEM_SANS,
        display=_SYSTEM_SANS,
        google_css_url=_DM_SANS,
        label="generic",
    ),
}


def font_pack_for_niche(niche_id: str | None) -> FontPack:
    key = (niche_id or "generic").strip().lower() or "generic"
    return FONT_PACKS.get(key, FONT_PACKS["generic"])


def font_link_tags(font_pack: FontPack) -> str:
    """HTML for <head>: preconnect + stylesheet. Empty if no Google URL."""
    url = (font_pack.google_css_url or "").strip()
    if not url:
        return ""
    return (
        '  <link rel="preconnect" href="https://fonts.googleapis.com">\n'
        '  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        f'  <link rel="stylesheet" href="{url}">\n'
    )
