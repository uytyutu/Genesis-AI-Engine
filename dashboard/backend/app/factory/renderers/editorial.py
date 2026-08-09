"""EditorialRenderer — quiet clinic / law / psychology architecture.

Long column + left media panel + rich company/services/photo band.
"""

from __future__ import annotations

import html as html_lib

from app.factory.renderers.base import RenderContext, RenderedSite
from app.factory.renderers.enrichment import (
    ENRICHMENT_CSS,
    enriched_body,
    split_hero_shell,
)
from app.factory.renderers.first_impression_dom import (
    _FI_BASE_CSS,
    first_impression_copy_html,
)

_esc = html_lib.escape


class EditorialRenderer:
    id = "editorial"
    label = "Editorial calm"

    def render(self, ctx: RenderContext) -> RenderedSite:
        phone = _esc(ctx.phone)
        email = _esc(ctx.email)
        hours = _esc(ctx.hours)

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="ed-link"
        )
        quiet = ""
        niche = (ctx.niche_id or "").strip().lower()
        if niche in ("psychology", "family_psychology"):
            quiet = (
                '<p class="ed-morning" data-atmosphere="1">'
                "Morgenlicht · Holz · Stille</p>"
            )
        hero = split_hero_shell(
            ctx,
            fi_html=quiet + fi,
            eyebrow=ctx.city or "Praxis",
            hero_class="ed-hero",
            band_class="ed-hero-copy",
            media_class="ed-hero-media",
        )

        body = f"""
  <main class="ed-site" data-renderer="editorial" id="ed-main">
    {enriched_body(ctx, services_id="ed-topics")}
    <section class="ed-block ed-contact" id="ed-contact">
      <p class="ed-eyebrow">Kontakt</p>
      <h2>Gespräch vereinbaren</h2>
      <div class="ed-contact-lines">
        <p>{phone}</p>
        <p>{email}</p>
        <p>{hours}</p>
      </div>
      <a class="ed-link" href="mailto:{email}">Nachricht senden</a>
    </section>
  </main>
"""

        nav = (
            ' <a href="#rx-about">Über uns</a>'
            ' <a href="#ed-topics">Schwerpunkte</a>'
            ' <a href="#rx-photos">Einblicke</a>'
            ' <a href="#cc-contact">Kontakt</a>'
        )

        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _EDITORIAL_CSS,
            js="",
            nav_links_html=nav,
            hero_layout_attr="editorial",
        )


_EDITORIAL_CSS = """
/* EditorialRenderer — essay + left media panel */
.ed-hero {
  background: #f7f4ef;
  color: #1c1916;
  padding: 0;
  align-items: stretch;
}
.ed-hero-media {
  background: #e4ddd2;
  filter: saturate(0.92) contrast(1.04);
}
.ed-hero-copy {
  padding: clamp(2.5rem, 7vw, 5rem) clamp(1.25rem, 5vw, 3.5rem);
  display: flex; flex-direction: column; justify-content: center;
  background: #f7f4ef;
}
.ed-morning {
  margin: 0 0 1.1rem;
  font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
  opacity: .5; max-width: 28ch;
}
.ed-eyebrow {
  margin: 0 0 .75rem;
  font-size: .72rem; letter-spacing: .16em; text-transform: uppercase;
  opacity: .55;
}
.ed-hero h1 {
  margin: 0 0 1rem;
  font-size: clamp(2rem, 4.2vw, 3.2rem);
  line-height: 1.12; font-weight: 450; max-width: 11ch;
  letter-spacing: -0.025em;
}
.ed-dek { margin: 0 0 1.5rem; max-width: 30ch; line-height: 1.7; opacity: .78; }
.ed-link {
  color: #1c1916; text-decoration: underline; text-underline-offset: .2em;
  font-weight: 500;
}
.ed-site { background: #fbfaf7; color: #1c1916; }
.ed-site .rx-svc-grid { grid-template-columns: 1fr; max-width: 640px; }
.ed-site .rx-svc-card {
  border: 0; border-bottom: 1px solid rgba(28,25,22,.1);
  background: transparent; box-shadow: none;
}
.ed-block {
  max-width: 720px; margin: 0 auto;
  padding: clamp(2.5rem, 6vw, 4rem) clamp(1.25rem, 5vw, 2rem);
}
.ed-block h2 {
  margin: .15rem 0 1.25rem;
  font-size: clamp(1.45rem, 2.5vw, 1.9rem);
  font-weight: 500;
}
.ed-contact-lines p { margin: 0 0 .4rem; }
.ed-site .rx-svc-card { background: #fff; }
"""


__all__ = ["EditorialRenderer"]
