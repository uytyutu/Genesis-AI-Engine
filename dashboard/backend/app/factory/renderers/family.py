"""Additional Renderer Strategies — distinct DOM per approach (not CSS variants)."""

from __future__ import annotations

import html as html_lib

from app.factory.renderers.base import RenderContext, RenderedSite

_esc = html_lib.escape


def _contact(ctx: RenderContext, *, anchor: str, title: str) -> str:
    return f"""
    <section class="rx-ask" id="{anchor}">
      <h2>{_esc(title)}</h2>
      <p><a href="tel:{_esc(ctx.phone)}">{_esc(ctx.phone)}</a></p>
      <p><a href="mailto:{_esc(ctx.email)}">{_esc(ctx.email)}</a></p>
      <p>{_esc(ctx.hours)}</p>
      <a class="rx-cta" href="mailto:{_esc(ctx.email)}">{_esc(ctx.cta)}</a>
    </section>"""


def _svc_list(ctx: RenderContext, cls: str = "rx-list") -> str:
    items = "".join(f"<li>{_esc(s)}</li>" for s in ctx.services[:8] if str(s).strip())
    return f'<ul class="{cls}">{items}</ul>'


class LuxuryRenderer:
    id = "luxury"
    label = "Luxury brand"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="lx-enter"
        )
        mood = _esc(
            {
                "car_dealership": "Nasser Asphalt · Licht der Scheinwerfer · Metall",
                "realestate": "Ruhe · Raum · Licht",
            }.get((ctx.niche_id or "").strip().lower(), "Stille · Material · Licht")
        )
        hero = split_hero_shell(
            ctx,
            fi_html=(
                f'<p class="lx-mood" data-atmosphere="1">{mood}</p>'
                f"{fi}"
            ),
            eyebrow=ctx.business_name,
            hero_class="lx-hero",
            band_class="lx-band",
            media_class="lx-hero-media",
        )
        body = f"""
  <main class="lx-site" data-renderer="luxury" id="lx-world">
    {enriched_body(ctx, services_id="lx-offer")}
    {_contact(ctx, anchor="lx-ask", title="Persönlich")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _LUXURY_CSS,
            nav_links_html=(
                ' <a href="#rx-about">Welt</a>'
                ' <a href="#lx-offer">Angebot</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Kontakt</a>'
            ),
            hero_layout_attr="luxury",
        )


class CorporateRenderer:
    id = "corporate"
    label = "Corporate clarity"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="co-btn"
        )
        eyebrow = f"{ctx.business_name}{(' · ' + ctx.city) if ctx.city else ''}"
        hero = split_hero_shell(
            ctx,
            fi_html=fi,
            eyebrow=eyebrow,
            hero_class="co-hero",
            band_class="co-band",
            media_class="co-hero-media",
        )
        trust = "".join(
            f"<li>{_esc(t)}</li>" for t in ctx.trust_points[:4] if str(t).strip()
        )
        body = f"""
  <main class="co-site" data-renderer="corporate">
    <section class="co-strip"><ul>{trust}</ul></section>
    {enriched_body(ctx, services_id="co-services")}
    {_contact(ctx, anchor="co-ask", title="Kontakt")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _CORPORATE_CSS,
            nav_links_html=(
                ' <a href="#rx-about">Unternehmen</a>'
                ' <a href="#co-services">Leistungen</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Kontakt</a>'
            ),
            hero_layout_attr="corporate",
        )


class CommerceRenderer:
    id = "commerce"
    label = "Commerce merchandising"

    def render(self, ctx: RenderContext) -> RenderedSite:
        cards = "".join(
            f'<article class="cm-card"><h3>{_esc(s)}</h3><a href="#cm-ask">Anfragen</a></article>'
            for s in ctx.services[:6]
            if str(s).strip()
        )
        hero = f"""
  <header class="cm-hero" data-renderer-hero="commerce-stage">
    <div class="cm-stage">
      <img src="assets/hero.jpg" alt="" width="1200" height="800" decoding="async">
    </div>
    <div class="cm-copy">
      <h1>{_esc(ctx.headline)}</h1>
      <p>{_esc(ctx.subtitle)}</p>
      <a class="cm-btn" href="#cm-grid">{_esc(ctx.cta)}</a>
    </div>
  </header>"""
        body = f"""
  <main class="cm-site" data-renderer="commerce">
    <section class="cm-grid" id="cm-grid"><h2>Auswahl</h2><div class="cm-cards">{cards}</div></section>
    {_contact(ctx, anchor="cm-ask", title="Bestellung / Anfrage")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_COMMERCE_CSS,
            nav_links_html=' <a href="#cm-grid">Auswahl</a> <a href="#cm-ask">Kontakt</a>',
            hero_layout_attr="commerce",
        )


class ClinicRenderer:
    id = "clinic"
    label = "Clinic care"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="cl-btn"
        )
        glass = (
            '<p class="cl-glass" data-atmosphere="1">'
            "Licht · Glas · Klarheit</p>"
        )
        hero = split_hero_shell(
            ctx,
            fi_html=glass + fi,
            eyebrow=ctx.city or "Praxis",
            hero_class="cl-hero",
            band_class="cl-panel",
            media_class="cl-hero-media",
        )
        body = f"""
  <main class="cl-site" data-renderer="clinic">
    {enriched_body(ctx, services_id="cl-care")}
    {_contact(ctx, anchor="cl-ask", title="Termin")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _CLINIC_CSS,
            nav_links_html=(
                ' <a href="#rx-about">Praxis</a>'
                ' <a href="#cl-care">Behandlungen</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Termin</a>'
            ),
            hero_layout_attr="clinic",
        )


class LegalRenderer:
    id = "legal"
    label = "Legal authority"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="lg-link"
        )
        hero = split_hero_shell(
            ctx,
            fi_html=fi,
            eyebrow=f"Kanzlei · {ctx.city or ''}".strip(" ·"),
            hero_class="lg-hero",
            band_class="lg-band",
            media_class="lg-hero-media",
        )
        body = f"""
  <main class="lg-site" data-renderer="legal">
    {enriched_body(ctx, services_id="lg-focus")}
    {_contact(ctx, anchor="lg-ask", title="Erstberatung")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _LEGAL_CSS,
            nav_links_html=(
                ' <a href="#rx-about">Kanzlei</a>'
                ' <a href="#lg-focus">Rechtsgebiete</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Kontakt</a>'
            ),
            hero_layout_attr="legal",
        )


class RestaurantRenderer:
    id = "restaurant"
    label = "Restaurant atmosphere"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="rt-btn"
        )
        ember = (
            '<p class="rt-ember" data-atmosphere="1">'
            "Feuer · Rauch · Wärme</p>"
        )
        eyebrow = f"{ctx.business_name}{(' · ' + ctx.city) if ctx.city else ''}"
        hero = split_hero_shell(
            ctx,
            fi_html=ember + fi,
            eyebrow=eyebrow,
            hero_class="rt-hero",
            band_class="rt-plate",
            media_class="rt-hero-media",
        )
        body = f"""
  <main class="rt-site" data-renderer="restaurant">
    {enriched_body(ctx, services_id="rt-menu")}
    {_contact(ctx, anchor="rt-ask", title="Reservierung")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _RESTAURANT_CSS,
            nav_links_html=(
                ' <a href="#rx-about">Haus</a>'
                ' <a href="#rt-menu">Menü</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Reservierung</a>'
            ),
            hero_layout_attr="restaurant",
        )


class TechnologyRenderer:
    id = "technology"
    label = "Technology product"

    def render(self, ctx: RenderContext) -> RenderedSite:
        hero = f"""
  <header class="tech-hero" data-renderer-hero="technology-console">
    <div class="tech-console">
      <p class="tech-tag">Product</p>
      <h1>{_esc(ctx.headline)}</h1>
      <p>{_esc(ctx.subtitle)}</p>
      <div class="tech-actions">
        <a class="tech-btn" href="#tech-ask">{_esc(ctx.cta)}</a>
        <a class="tech-ghost" href="#tech-stack">Features</a>
      </div>
    </div>
  </header>"""
        body = f"""
  <main class="tech-site" data-renderer="technology">
    <section class="tech-stack" id="tech-stack"><h2>Capabilities</h2>{_svc_list(ctx, "tech-feats")}</section>
    <section class="tech-note"><p>{_esc(ctx.about)}</p></section>
    {_contact(ctx, anchor="tech-ask", title="Talk to us")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_TECH_CSS,
            nav_links_html=' <a href="#tech-stack">Features</a> <a href="#tech-ask">Contact</a>',
            hero_layout_attr="technology",
        )


class MinimalRenderer:
    id = "minimal"
    label = "Minimal quiet"

    def render(self, ctx: RenderContext) -> RenderedSite:
        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            enriched_body,
            split_hero_shell,
        )
        from app.factory.renderers.first_impression_dom import (
            _FI_BASE_CSS,
            first_impression_copy_html,
        )

        fi = first_impression_copy_html(
            ctx, cta_href="#cc-contact", cta_class="mn-cta"
        )
        hero = split_hero_shell(
            ctx,
            fi_html=fi,
            eyebrow=ctx.business_name,
            hero_class="mn-hero",
            band_class="mn-band",
            media_class="mn-hero-media",
        )
        body = f"""
  <main class="mn-site" data-renderer="minimal">
    {enriched_body(ctx, services_id="mn-work")}
    {_contact(ctx, anchor="mn-ask", title="Kontakt")}
  </main>"""
        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS
            + ENRICHMENT_CSS
            + _MINIMAL_CSS
            + ".mn-cta{display:inline-block;margin-top:.5rem;color:inherit;font-weight:600}",
            nav_links_html=(
                ' <a href="#rx-about">Über uns</a>'
                ' <a href="#mn-work">Arbeit</a>'
                ' <a href="#rx-photos">Einblicke</a>'
                ' <a href="#cc-contact">Kontakt</a>'
            ),
            hero_layout_attr="minimal",
        )


_LUXURY_CSS = """
.lx-hero{background:#0a0a0a;color:#f5f0e8;padding:0;align-items:stretch}
.lx-hero-media{background:#141414;filter:saturate(.85)}
.lx-band{padding:clamp(3rem,8vw,5rem) clamp(1.5rem,6vw,4rem);display:flex;flex-direction:column;justify-content:center;background:#0a0a0a}
.lx-mood{margin:0 0 1.25rem;font-size:.78rem;letter-spacing:.18em;text-transform:uppercase;opacity:.55;max-width:28ch}
.lx-hero h1{font-size:clamp(2.8rem,7vw,5.5rem);font-weight:400;max-width:10ch;line-height:1;margin:0}
.lx-line{max-width:28ch;opacity:.7;margin:1.5rem 0 2.5rem}
.lx-enter{color:#f5f0e8;text-decoration:none;border-bottom:1px solid rgba(245,240,232,.5);padding-bottom:.2rem;width:max-content}
.lx-site{background:#0a0a0a;color:#f5f0e8}
.lx-site .rx-svc-card{background:#141414;border-color:rgba(245,240,232,.12);color:#f5f0e8}
.lx-site .rx-svc-body p{opacity:.7}
.lx-site .rx-about,.lx-site .rx-services,.lx-site .rx-photo-band{color:#f5f0e8}
"""

_CLINIC_CSS = """
.cl-hero{background:#f8fafc;color:#0f172a;padding:0;align-items:stretch;gap:0}
.cl-hero-media{background:#e2e8f0}
.cl-panel{padding:clamp(2.5rem,6vw,4rem) clamp(1.5rem,5vw,3rem);display:flex;flex-direction:column;justify-content:center;background:#f8fafc}
.cl-glass{margin:0 0 1rem;font-size:.72rem;letter-spacing:.14em;text-transform:uppercase;opacity:.5;color:#0f766e}
.cl-soft{opacity:.55;letter-spacing:.08em;text-transform:uppercase;font-size:.72rem}
.cl-btn{display:inline-block;margin-top:1rem;padding:.65rem 1.1rem;background:#0f766e;color:#fff;text-decoration:none;border-radius:999px;width:max-content}
.cl-site{background:#f8fafc;color:#0f172a}
.rx-ask{padding:2.5rem 5vw;max-width:800px}
"""

_LEGAL_CSS = """
.lg-hero{background:#faf8f4;color:#14161c;padding:0;align-items:stretch}
.lg-hero-media{background:#e8e2d6}
.lg-band{padding:clamp(3rem,7vw,5rem) clamp(1.5rem,6vw,4rem);display:flex;flex-direction:column;justify-content:center;position:relative;background:#faf8f4}
.lg-band::before{content:"";position:absolute;left:0;top:0;bottom:0;width:4px;background:#b4975a}
.lg-eyebrow,.rx-hero-eyebrow{letter-spacing:.2em;text-transform:uppercase;font-size:.7rem;opacity:.5}
.lg-link{color:#14161c;font-weight:600}
.lg-site{background:#faf8f4;color:#14161c}
.rx-ask{padding:2.5rem 8vw;max-width:820px}
"""

_RESTAURANT_CSS = """
.rt-hero{background:#1c1410;color:#faf6f1;padding:0;align-items:stretch}
.rt-hero-media{background:#2a1c14}
.rt-plate{padding:clamp(2.5rem,6vw,4rem) clamp(1.5rem,5vw,3rem);display:flex;flex-direction:column;justify-content:center;background:#1c1410;text-align:left}
.rt-ember{margin:0 0 1rem;font-size:.72rem;letter-spacing:.2em;text-transform:uppercase;opacity:.65;color:#e8a060}
.rt-place{letter-spacing:.2em;text-transform:uppercase;font-size:.7rem;opacity:.7}
.rt-btn{display:inline-block;margin-top:1rem;padding:.7rem 1.4rem;border:1px solid rgba(250,246,241,.6);color:#faf6f1;text-decoration:none;width:max-content}
.rt-site{background:#faf6f1;color:#1c1410}
.rt-site .rx-svc-card{background:#fff}
.rx-ask{padding:3rem 6vw;max-width:720px;margin:0 auto}
"""

_MINIMAL_CSS = """
.mn-hero{background:#fff;color:#111;padding:0;align-items:stretch}
.mn-hero-media{background:#eceae6}
.mn-band{padding:clamp(3rem,8vw,5rem) clamp(1.5rem,6vw,4rem);display:flex;flex-direction:column;justify-content:center;background:#fff}
.mn-hero h1{font-size:clamp(2rem,4vw,3rem);font-weight:400;margin:0 0 1rem}
.mn-site{background:#fff;color:#111}
.rx-cta{display:inline-block;margin-top:1rem;color:#111}
"""

_CORPORATE_CSS = """
.co-hero{background:#0f172a;color:#e2e8f0;padding:0;align-items:stretch}
.co-hero-media{background-color:#1e293b}
.co-band{padding:clamp(2.5rem,6vw,4rem) clamp(1.5rem,5vw,3rem);display:flex;flex-direction:column;justify-content:center;background:#0f172a}
.co-eyebrow,.rx-hero-eyebrow{text-transform:uppercase;letter-spacing:.12em;font-size:.72rem;opacity:.6}
.co-hero h1{font-size:clamp(2rem,4vw,3.2rem);max-width:18ch}
.co-btn{display:inline-block;margin-top:1rem;padding:.7rem 1.2rem;background:#38bdf8;color:#0f172a;text-decoration:none;font-weight:600;width:max-content}
.co-strip ul{display:flex;flex-wrap:wrap;gap:.5rem;list-style:none;margin:0;padding:1.25rem 6vw;background:#1e293b;color:#cbd5e1}
.co-strip li{border:1px solid rgba(203,213,225,.25);padding:.35rem .7rem;font-size:.8rem}
.co-grid,.co-about,.rx-ask{padding:2.5rem 6vw;max-width:960px}
.co-svc{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:1rem;list-style:none;padding:0}
.co-svc li{padding:1rem;background:#f1f5f9;color:#0f172a}
.co-site .rx-svc-card{background:#fff;color:#0f172a}
.co-site .rx-about-copy,.co-site .rx-services,.co-site .rx-photo-band{color:#0f172a}
"""

_COMMERCE_CSS = """
.cm-hero{display:grid;grid-template-columns:1.2fr .8fr;min-height:80vh;background:#fafafa}
.cm-stage{overflow:hidden;background:#e7e5e4}
.cm-stage img{width:100%;height:100%;object-fit:cover;min-height:80vh}
.cm-copy{display:flex;flex-direction:column;justify-content:center;padding:2rem}
.cm-btn{display:inline-block;margin-top:1rem;padding:.75rem 1.2rem;background:#111;color:#fff;text-decoration:none}
.cm-cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:1rem}
.cm-card{border:1px solid #e7e5e4;padding:1.25rem;background:#fff}
.cm-grid,.rx-ask{padding:2.5rem 4vw;max-width:1100px;margin:0 auto}
@media(max-width:800px){.cm-hero{grid-template-columns:1fr}.cm-stage img{min-height:40vh}}
"""

_TECH_CSS = """
.tech-hero{min-height:85vh;display:grid;align-items:center;padding:4rem 6vw;background:radial-gradient(ellipse at 20% 20%,#1e293b,#020617);color:#e2e8f0}
.tech-tag{display:inline-block;padding:.2rem .5rem;border:1px solid #334155;font-size:.7rem;letter-spacing:.08em;text-transform:uppercase}
.tech-hero h1{font-size:clamp(2.2rem,5vw,3.8rem);max-width:16ch;letter-spacing:-.03em}
.tech-actions{display:flex;gap:.6rem;flex-wrap:wrap;margin-top:1.25rem}
.tech-btn{padding:.7rem 1.1rem;background:#22d3ee;color:#082f49;text-decoration:none;font-weight:600}
.tech-ghost{padding:.7rem 1.1rem;border:1px solid #334155;color:#e2e8f0;text-decoration:none}
.tech-stack,.tech-note,.rx-ask{padding:2.5rem 6vw;max-width:900px}
.tech-feats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:.75rem;list-style:none;padding:0}
.tech-feats li{padding:1rem;background:#0f172a;border:1px solid #1e293b}
"""

# shared contact button baseline
_SHARED_RX = """
.rx-ask{padding:2.5rem 6vw}
.rx-cta{display:inline-block;margin-top:1rem;padding:.65rem 1.1rem;background:#111;color:#fff;text-decoration:none}
"""
_LUXURY_CSS += _SHARED_RX
_CORPORATE_CSS += _SHARED_RX
_COMMERCE_CSS += _SHARED_RX
_CLINIC_CSS += _SHARED_RX
_LEGAL_CSS += _SHARED_RX
_RESTAURANT_CSS += _SHARED_RX
_TECH_CSS += _SHARED_RX
_MINIMAL_CSS += _SHARED_RX


__all__ = [
    "ClinicRenderer",
    "CommerceRenderer",
    "CorporateRenderer",
    "LegalRenderer",
    "LuxuryRenderer",
    "MinimalRenderer",
    "RestaurantRenderer",
    "TechnologyRenderer",
]
