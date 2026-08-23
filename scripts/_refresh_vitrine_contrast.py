"""Refresh contrast CSS on public website demos."""
from __future__ import annotations

import re
from pathlib import Path

PREVIEWS = Path(__file__).resolve().parents[1] / "dashboard" / "frontend" / "public" / "package-previews"
NICHES = [
    "beauty",
    "cleaning",
    "it_support",
    "dental",
    "restaurant",
    "handwerk",
    "law",
    "auto",
]

CSS = """
<style id="vitrine-contrast-fix">
/* Public demos: readable nav + copy — never white-on-light */
.topbar,
.topbar.is-scrolled,
header.topbar,
body[data-dna-style] .topbar,
body[data-dna-style] .topbar.is-scrolled {
  background: rgba(12, 16, 22, 0.94) !important;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(255,255,255,0.14) !important;
  box-shadow: 0 8px 28px rgba(0,0,0,0.25) !important;
}
.topbar .brand-word,
.topbar .brand strong,
.topbar a:not(.btn):not(.topbar-cta):not(.cta-button),
.topbar-links a,
body[data-dna-style] .topbar,
body[data-dna-style] .topbar .brand,
body[data-dna-style] .topbar .brand-word,
body[data-dna-style] .topbar a:not(.btn):not(.topbar-cta):not(.cta-button) {
  color: #f4f6f8 !important;
  opacity: 1 !important;
  text-shadow: none !important;
}
.topbar a:not(.btn):not(.topbar-cta):hover,
body[data-dna-style] .topbar a:not(.btn):not(.topbar-cta):hover {
  color: #ffffff !important;
}
.hero h1, .hero h2, .hero .headline, .hero .hero-title,
.cl-hero h1, .cl-hero h2, [class*="-hero"] h1, [class*="-hero"] h2 {
  color: #14181f !important;
}
.hero p, .hero li, .hero .lead, .hero .sub, .hero .hero-sub,
.cl-hero p, .cl-panel p, [class*="-hero"] p {
  color: #1f2430 !important;
}
html body .cl-glass,
html body p.cl-glass,
html body [data-atmosphere="1"],
html body .rx-hero-eyebrow,
html body .cl-hero .eyebrow,
html body .cl-hero .kicker,
html body .cl-hero .meta,
html body .cl-hero .tagline,
html body .hero .eyebrow, html body .hero .kicker, html body .hero .meta, html body .hero .tagline,
html body .hero [class*="eyebrow"], html body .hero [class*="kicker"], html body .hero [class*="meta"],
html body .hero .fi-problem, html body .hero .fi-emotion, html body .hero .fi-trust,
html body .hero .fi-offer, html body .hero .fi-idea {
  color: #2a3340 !important;
  opacity: 1 !important;
}
/* Footer / legal — skip dark legal strip (identity pass) */
footer:not(.vitrine-legal-footer),
footer:not(.vitrine-legal-footer) a,
.site-footer, .site-footer a, .legal-strip, .legal-strip a {
  color: #1f2430 !important;
  opacity: 1 !important;
}
footer:not(.vitrine-legal-footer) a:hover, .site-footer a:hover { color: #000 !important; }
html body footer.vitrine-legal-footer,
html body footer.vitrine-legal-footer a {
  background: #111827 !important;
  color: #f3f4f6 !important;
  opacity: 1 !important;
}
</style>
"""


def main() -> None:
    for niche in NICHES:
        path = PREVIEWS / "sites" / "premium" / niche / "index.html"
        text = path.read_text(encoding="utf-8")
        # drop any previous contrast block (head or body)
        text = re.sub(
            r'<style id="vitrine-contrast-fix">.*?</style>\s*',
            "",
            text,
            flags=re.S,
        )
        # inject at end of body so it wins over earlier page CSS
        if "</body>" in text:
            new = text.replace("</body>", CSS + "\n</body>", 1)
        elif "</head>" in text:
            new = text.replace("</head>", CSS + "\n</head>", 1)
        else:
            new = text + CSS
        path.write_text(new, encoding="utf-8")
        print(niche, "updated")


if __name__ == "__main__":
    main()
