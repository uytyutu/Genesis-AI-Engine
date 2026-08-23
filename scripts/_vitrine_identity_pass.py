"""Vitrine polish: one legal pair + distinct niche look (sites + stores).

- Remove duplicate Impressum/Datenschutz/Haftung chrome
- Keep a single Impressum + Datenschutz in the footer
- Inject niche identity CSS (palette, fonts, backgrounds)
- Soft-hide empty Reputation «Demo» document spam at page bottom
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
PREVIEWS = PUBLIC / "package-previews"

SITES = [
    "beauty",
    "cleaning",
    "it_support",
    "dental",
    "restaurant",
    "handwerk",
    "law",
    "auto",
]
STORES = [
    "beauty",
    "cleaning_shop",
    "electronics",
    "food",
    "furniture",
    "fashion",
]

# Distinct visual DNA per public website niche
SITE_THEMES: dict[str, dict[str, str]] = {
    "beauty": {
        "font": "Cormorant+Garamond:wght@500;600;700|DM+Sans:wght@400;500;600",
        "display": '"Cormorant Garamond", Georgia, serif',
        "body": '"DM Sans", system-ui, sans-serif',
        "bg": "#f7f1ee",
        "ink": "#1c1412",
        "muted": "#5c4a45",
        "accent": "#b76e79",
        "accent2": "#d4a5a5",
        "surface": "#fffaf8",
        "hero_overlay": "linear-gradient(105deg, rgba(247,241,238,.92) 42%, rgba(247,241,238,.2) 100%)",
        "topbar": "rgba(28,20,18,0.92)",
        "mood": "porcelain rose atelier",
    },
    "cleaning": {
        "font": "Manrope:wght@400;600;700|Source+Sans+3:wght@400;600",
        "display": '"Manrope", system-ui, sans-serif',
        "body": '"Source Sans 3", system-ui, sans-serif',
        "bg": "#eef6f3",
        "ink": "#0f2420",
        "muted": "#3d5c54",
        "accent": "#0d9488",
        "accent2": "#5eead4",
        "surface": "#ffffff",
        "hero_overlay": "linear-gradient(120deg, rgba(15,36,32,.78) 0%, rgba(15,36,32,.15) 70%)",
        "topbar": "rgba(15,36,32,0.94)",
        "mood": "fresh aqua clean",
    },
    "it_support": {
        "font": "Space+Grotesk:wght@500;600;700|IBM+Plex+Sans:wght@400;500;600",
        "display": '"Space Grotesk", system-ui, sans-serif',
        "body": '"IBM Plex Sans", system-ui, sans-serif',
        "bg": "#0b1220",
        "ink": "#e8eef8",
        "muted": "#9fb0c9",
        "accent": "#38bdf8",
        "accent2": "#818cf8",
        "surface": "#121a2b",
        "hero_overlay": "linear-gradient(135deg, rgba(11,18,32,.9) 30%, rgba(56,189,248,.18) 100%)",
        "topbar": "rgba(8,12,22,0.96)",
        "mood": "dark tech desk",
    },
    "dental": {
        "font": "Libre+Baskerville:wght@400;700|Nunito+Sans:wght@400;600;700",
        "display": '"Libre Baskerville", Georgia, serif',
        "body": '"Nunito Sans", system-ui, sans-serif',
        "bg": "#f4f8fb",
        "ink": "#132033",
        "muted": "#4a6278",
        "accent": "#0284c7",
        "accent2": "#7dd3fc",
        "surface": "#ffffff",
        "hero_overlay": "linear-gradient(100deg, rgba(244,248,251,.95) 38%, rgba(244,248,251,.25) 100%)",
        "topbar": "rgba(19,32,51,0.93)",
        "mood": "clinic calm blue",
    },
    "restaurant": {
        "font": "Playfair+Display:wght@500;600;700|Karla:wght@400;500;600",
        "display": '"Playfair Display", Georgia, serif',
        "body": '"Karla", system-ui, sans-serif',
        "bg": "#1a1210",
        "ink": "#f6ebe3",
        "muted": "#d2b8a6",
        "accent": "#c45c26",
        "accent2": "#e8b86d",
        "surface": "#241816",
        "hero_overlay": "linear-gradient(180deg, rgba(26,18,16,.35) 0%, rgba(26,18,16,.85) 100%)",
        "topbar": "rgba(20,12,10,0.94)",
        "mood": "candlelit dining",
    },
    "handwerk": {
        "font": "Oswald:wght@500;600|Work+Sans:wght@400;500;600",
        "display": '"Oswald", system-ui, sans-serif',
        "body": '"Work Sans", system-ui, sans-serif',
        "bg": "#f3efe6",
        "ink": "#1a1712",
        "muted": "#5a5246",
        "accent": "#b45309",
        "accent2": "#d97706",
        "surface": "#fffdf8",
        "hero_overlay": "linear-gradient(115deg, rgba(26,23,18,.82) 0%, rgba(26,23,18,.2) 75%)",
        "topbar": "rgba(26,23,18,0.94)",
        "mood": "workshop timber",
    },
    "law": {
        "font": "Cormorant:wght@500;600;700|Source+Serif+4:wght@400;600",
        "display": '"Cormorant", Georgia, serif',
        "body": '"Source Serif 4", Georgia, serif',
        "bg": "#f7f5f0",
        "ink": "#1c1917",
        "muted": "#57534e",
        "accent": "#44403c",
        "accent2": "#a8a29e",
        "surface": "#ffffff",
        "hero_overlay": "linear-gradient(100deg, rgba(247,245,240,.94) 40%, rgba(247,245,240,.2) 100%)",
        "topbar": "rgba(28,25,23,0.94)",
        "mood": "editorial chamber",
    },
    "auto": {
        "font": "Barlow+Condensed:wght@600;700|Barlow:wght@400;500;600",
        "display": '"Barlow Condensed", system-ui, sans-serif',
        "body": '"Barlow", system-ui, sans-serif',
        "bg": "#111827",
        "ink": "#f3f4f6",
        "muted": "#9ca3af",
        "accent": "#ef4444",
        "accent2": "#fbbf24",
        "surface": "#1f2937",
        "hero_overlay": "linear-gradient(125deg, rgba(17,24,39,.88) 20%, rgba(239,68,68,.22) 100%)",
        "topbar": "rgba(10,14,22,0.96)",
        "mood": "garage night red",
    },
}

STORE_THEMES: dict[str, dict[str, str]] = {
    "beauty": {
        "font": "Fraunces:wght@500;600|Outfit:wght@400;500;600",
        "display": '"Fraunces", Georgia, serif',
        "body": '"Outfit", system-ui, sans-serif',
        "bg": "#fff5f7",
        "ink": "#3b1020",
        "accent": "#db2777",
        "surface": "#ffffff",
        "hero": "radial-gradient(circle at 20% 20%, #fce7f3, #fff5f7 55%, #fdf2f8)",
    },
    "cleaning_shop": {
        "font": "Sora:wght@500;600;700|Inter:wght@400;500;600",
        "display": '"Sora", system-ui, sans-serif',
        "body": '"Inter", system-ui, sans-serif',
        "bg": "#f0fdfa",
        "ink": "#134e4a",
        "accent": "#0f766e",
        "surface": "#ffffff",
        "hero": "linear-gradient(160deg, #ccfbf1, #f0fdfa 50%, #ecfeff)",
    },
    "electronics": {
        "font": "Orbitron:wght@500;600|Rajdhani:wght@500;600",
        "display": '"Orbitron", system-ui, sans-serif',
        "body": '"Rajdhani", system-ui, sans-serif',
        "bg": "#0a0f1a",
        "ink": "#e2e8f0",
        "accent": "#22d3ee",
        "surface": "#111827",
        "hero": "radial-gradient(ellipse at 70% 0%, #164e63 0%, #0a0f1a 55%)",
    },
    "food": {
        "font": "Libre+Bodoni:wght@500;600|Nunito:wght@400;600",
        "display": '"Libre Bodoni", Georgia, serif',
        "body": '"Nunito", system-ui, sans-serif',
        "bg": "#fff7ed",
        "ink": "#431407",
        "accent": "#ea580c",
        "surface": "#fffbeb",
        "hero": "linear-gradient(180deg, #ffedd5, #fff7ed 60%)",
    },
    "furniture": {
        "font": "Newsreader:wght@500;600|Figtree:wght@400;500;600",
        "display": '"Newsreader", Georgia, serif',
        "body": '"Figtree", system-ui, sans-serif',
        "bg": "#f5f0e8",
        "ink": "#292524",
        "accent": "#78716c",
        "surface": "#fffcf7",
        "hero": "linear-gradient(135deg, #e7e5e4, #f5f0e8 40%, #d6d3d1)",
    },
    "fashion": {
        "font": "Bodoni+Moda:wght@500;600|Jost:wght@400;500;600",
        "display": '"Bodoni Moda", Georgia, serif',
        "body": '"Jost", system-ui, sans-serif',
        "bg": "#0c0a09",
        "ink": "#fafaf9",
        "accent": "#a8a29e",
        "surface": "#1c1917",
        "hero": "linear-gradient(180deg, #1c1917, #0c0a09 70%)",
    },
}

STYLE_ID = "vitrine-identity"
LEGAL_STYLE_ID = "vitrine-legal-cleanup"


def _strip_block(html: str, pattern: str) -> str:
    return re.sub(pattern, "", html, flags=re.I | re.S)


def clean_site_legal(html: str, brand: str) -> str:
    # Remove duplicate Rechtliches nav (Impressum / Datenschutz / Haftung)
    html = _strip_block(
        html,
        r'\s*<nav\s+class="cc-legal"[^>]*>.*?</nav>\s*',
    )
    # Remove white Reputation demo-document pack (handwerk filler)
    html = _strip_block(
        html,
        r'\s*<section\s+class="section reputation-pack"[^>]*>.*?</section>\s*',
    )
    # Drop Reputation nav link
    html = re.sub(
        r'\s*<a\s+href="#reputation">Reputation</a>',
        "",
        html,
        flags=re.I,
    )
    # Form note: keep consent text, no second Datenschutz link
    html = re.sub(
        r'(<p class="cc-note">Mit dem Absenden stimmen Sie der Kontaktaufnahme zu\.)\s*'
        r'<a href="datenschutz\.html">Datenschutz</a></p>',
        r"\1</p>",
        html,
        flags=re.I,
    )
    # Collapse footer to one legal pair
    footer_re = re.compile(
        r"<footer\b[^>]*>.*?</footer>",
        re.I | re.S,
    )

    def _footer_one(m: re.Match[str]) -> str:
        return (
            f'<footer data-footer-variant="compact" data-market="DE" '
            f'data-legal-keys="impressum,datenschutz" class="vitrine-legal-footer">'
            f'<a href="impressum.html">Impressum</a>'
            f'<span aria-hidden="true"> · </span>'
            f'<a href="datenschutz.html">Datenschutz</a>'
            f"</footer>"
        )

    html = footer_re.sub(_footer_one, html, count=1)
    legal_css = (
        f'<style id="{LEGAL_STYLE_ID}">'
        f".cc-legal, #reputation, .reputation-pack {{ display:none !important; }}"
        # Dark legal strip + fill body padding under sticky (kills white gap)
        f"html body footer.vitrine-legal-footer {{"
        f"background:#111827 !important; background-image:none !important;"
        f"color:#f3f4f6 !important; opacity:1 !important;"
        f"text-align:center; font-size:.95rem; border:0 !important;"
        f"padding:1.1rem 1rem calc(1.1rem + 72px) !important;"
        f"margin:0 !important; }}"
        f"html body footer.vitrine-legal-footer a {{"
        f"color:#ffffff !important; text-decoration:underline;"
        f"text-underline-offset:.18em; margin:0 .4rem; opacity:1 !important; }}"
        f"html body .cc-chrome label,"
        f"html body .cc-chrome .cc-note,"
        f"html body .cc-chrome .cc-lead,"
        f"html body .cc-chrome .cc-kicker,"
        f"html body .cc-chrome h2,"
        f"html body .cc-chrome li,"
        f"html body .cc-chrome li a {{"
        f"color: var(--vi-ink, #1f2430) !important; opacity:1 !important; }}"
        f"html body .cc-chrome {{ background: var(--vi-surface, #fffaf8) !important; }}"
        f"html body .cc-chrome .cc-form {{ background: transparent !important; }}"
        f"</style>"
    )
    html = re.sub(
        rf'<style id="{LEGAL_STYLE_ID}">.*?</style>\s*',
        "",
        html,
        flags=re.I | re.S,
    )
    html = html.replace("</body>", legal_css + "\n</body>", 1)
    return html


def site_identity_css(niche: str, theme: dict[str, str]) -> str:
    font = theme["font"]
    return f"""<link id="vitrine-identity-font" rel="stylesheet" href="https://fonts.googleapis.com/css2?family={font}&display=swap">
<style id="{STYLE_ID}">
/* Niche identity — {niche}: {theme['mood']} */
html body {{
  --vi-bg: {theme['bg']};
  --vi-ink: {theme['ink']};
  --vi-muted: {theme['muted']};
  --vi-accent: {theme['accent']};
  --vi-accent2: {theme['accent2']};
  --vi-surface: {theme['surface']};
  background: var(--vi-bg) !important;
  color: var(--vi-ink);
  font-family: {theme['body']} !important;
}}
html body h1, html body h2, html body h3, html body .brand-word, html body .cl-hero h1 {{
  font-family: {theme['display']} !important;
  letter-spacing: -0.02em;
}}
html body .topbar,
html body .topbar.is-scrolled,
html body header.topbar {{
  background: {theme['topbar']} !important;
}}
html body .btn, html body .topbar-cta, html body .cta-button, html body a.btn {{
  background: var(--vi-accent) !important;
  border-color: var(--vi-accent) !important;
  color: #fff !important;
}}
html body .cl-hero, html body .hero, html body [class*="-hero"] {{
  position: relative;
}}
html body .cl-hero::before, html body .hero::before {{
  content: "";
  position: absolute; inset: 0; pointer-events: none; z-index: 0;
  background: {theme['hero_overlay']};
}}
html body .cl-hero > *, html body .hero > * {{ position: relative; z-index: 1; }}
html body .section, html body .svc-card, html body .process-card, html body .cc-chrome {{
  background: var(--vi-surface);
}}
html body .cc-chrome {{
  background: var(--vi-surface) !important;
  color: var(--vi-ink) !important;
  border-top: 1px solid color-mix(in srgb, var(--vi-ink) 12%, transparent);
}}
html body .cc-chrome h2, html body .cc-chrome p, html body .cc-chrome li, html body .cc-chrome label {{
  color: var(--vi-ink) !important;
  opacity: 1 !important;
}}
html body .cc-btn.cc-call, html body .cc-btn.cc-wa {{
  background: var(--vi-accent) !important;
  color: #fff !important;
}}
/* Dark niches: force light copy on hero glass */
html body[data-niche="{niche}"] .cl-glass,
html body[data-niche="{niche}"] .cl-hero p,
html body[data-niche="{niche}"] .cl-hero h1 {{
  color: var(--vi-ink) !important;
}}
</style>
"""


def clean_store_legal(html: str) -> str:
    # Remove Rechtliches group from drawer (keep footer Service links only once)
    html = re.sub(
        r'\s*<p class="nav-group">Rechtliches</p>\s*'
        r'(?:<a[^>]*>Rückgabe</a>\s*)?'
        r'(?:<a[^>]*>Impressum</a>\s*)?'
        r'(?:<a[^>]*>Datenschutz</a>\s*)?',
        "\n",
        html,
        flags=re.I,
    )
    # Ensure footer Service has exactly Impressum + Datenschutz (+ returns/contact ok)
    # Deduplicate consecutive Impressum/Datenschutz list items in footer
    html = re.sub(
        r'(<li><a href="impressum\.html">Impressum</a></li>\s*){2,}',
        r'<li><a href="impressum.html">Impressum</a></li>\n',
        html,
        flags=re.I,
    )
    html = re.sub(
        r'(<li><a href="datenschutz\.html">Datenschutz</a></li>\s*){2,}',
        r'<li><a href="datenschutz.html">Datenschutz</a></li>\n',
        html,
        flags=re.I,
    )
    return html


def store_identity_css(niche: str, theme: dict[str, str]) -> str:
    return f"""<link id="vitrine-identity-font" rel="stylesheet" href="https://fonts.googleapis.com/css2?family={theme['font']}&display=swap">
<style id="{STYLE_ID}">
/* Store identity — {niche} */
html body {{
  --vi-bg: {theme['bg']};
  --vi-ink: {theme['ink']};
  --vi-accent: {theme['accent']};
  --vi-surface: {theme['surface']};
  background: var(--vi-bg) !important;
  color: var(--vi-ink) !important;
  font-family: {theme['body']} !important;
}}
html body h1, html body h2, html body h3, html body .brand-word, html body .page-title {{
  font-family: {theme['display']} !important;
}}
html body .site-header, html body .store-hero, html body .hero-banner, html body .catalog-hero {{
  background: {theme['hero']} !important;
}}
html body .btn, html body button.btn, html body [data-action="add-cart"] {{
  background: var(--vi-accent) !important;
  border-color: var(--vi-accent) !important;
  color: #fff !important;
}}
html body .product-card, html body .card, html body .catalog-grid > * {{
  background: var(--vi-surface) !important;
  border-color: color-mix(in srgb, var(--vi-ink) 12%, transparent) !important;
}}
html body .site-footer {{
  background: color-mix(in srgb, var(--vi-ink) 92%, black) !important;
  color: #f5f5f4 !important;
}}
html body .site-footer a {{ color: #f5f5f4 !important; }}
</style>
"""


def upsert_head_assets(html: str, block: str) -> str:
    # Remove prior identity injects
    html = re.sub(
        r'<link id="vitrine-identity-font"[^>]*>\s*',
        "",
        html,
        flags=re.I,
    )
    html = re.sub(
        rf'<style id="{STYLE_ID}">.*?</style>\s*',
        "",
        html,
        flags=re.I | re.S,
    )
    if "</head>" in html:
        return html.replace("</head>", block + "</head>", 1)
    return block + html


def extract_brand(html: str) -> str:
    m = re.search(r'class="brand-word"[^>]*>([^<]+)', html)
    if m:
        return m.group(1).strip()
    m = re.search(r"<title>([^—|<]+)", html)
    if m:
        return m.group(1).strip()
    return "Virtus Demo"


def patch_site(niche: str) -> str:
    path = PREVIEWS / "sites" / "premium" / niche / "index.html"
    if not path.exists():
        return f"{niche}: MISSING"
    html = path.read_text(encoding="utf-8", errors="replace")
    brand = extract_brand(html)
    html = clean_site_legal(html, brand)
    theme = SITE_THEMES[niche]
    html = upsert_head_assets(html, site_identity_css(niche, theme))
    # Dark niches: light copy (beat contrast-fix dark-on-dark)
    if theme["bg"].startswith("#0") or theme["bg"].startswith("#1"):
        dark_fix = (
            f'<style id="vitrine-dark-ink">'
            f"html body,"
            f"html body .cl-hero h1, html body .hero h1,"
            f"html body .cl-hero h2, html body .hero h2,"
            f"html body .cl-hero p, html body .hero p,"
            f"html body .cl-hero li, html body .hero li,"
            f"html body .cl-glass, html body p.cl-glass,"
            f"html body [data-atmosphere],"
            f"html body .cl-panel, html body .cl-panel p,"
            f"html body .fi-problem, html body .fi-emotion,"
            f"html body .fi-trust, html body .fi-offer, html body .fi-idea {{"
            f"color:{theme['ink']} !important; opacity:1 !important; }}"
            f"html body .cl-hero, html body .hero, html body .cl-panel {{"
            f"background: transparent !important; }}"
            f"</style>"
        )
        html = re.sub(
            r'<style id="vitrine-dark-ink">.*?</style>\s*',
            "",
            html,
            flags=re.I | re.S,
        )
        html = html.replace("</body>", dark_fix + "\n</body>", 1)
    path.write_text(html, encoding="utf-8")
    return f"{niche}: updated ({theme['mood']})"


def patch_store(niche: str) -> str:
    store_dir = PREVIEWS / "stores" / "premium" / niche
    if not store_dir.exists():
        return f"store/{niche}: MISSING"
    theme = STORE_THEMES[niche]
    n = 0
    for path in sorted(store_dir.glob("*.html")):
        html = path.read_text(encoding="utf-8", errors="replace")
        html = clean_store_legal(html)
        html = upsert_head_assets(html, store_identity_css(niche, theme))
        path.write_text(html, encoding="utf-8")
        n += 1
    return f"store/{niche}: {n} pages ({theme['accent']})"


def main() -> None:
    for niche in SITES:
        print(patch_site(niche))
    for niche in STORES:
        print(patch_store(niche))
    # bump thumb cache hint via print (catalog bump done separately if needed)
    print("done")


if __name__ == "__main__":
    main()
