"""CraftsmanRenderer — craft / roof / fence / garden site architecture.

NOT Layout D + shuffled sections.
DOM: work-site proof → case wall → process spine → crew → kit → ask.
"""

from __future__ import annotations

import html as html_lib

from app.factory.renderers.base import RenderContext, RenderedSite
from app.factory.renderers.first_impression_dom import (
    _FI_BASE_CSS,
    first_impression_copy_html,
)

_esc = html_lib.escape


class CraftsmanRenderer:
    id = "craftsman"
    label = "Craftsman work-site"

    def render(self, ctx: RenderContext) -> RenderedSite:
        name = _esc(ctx.business_name)
        city = _esc(ctx.city or "")
        phone = _esc(ctx.phone)
        email = _esc(ctx.email)
        hours = _esc(ctx.hours)
        demo = (
            '<p class="cr-demo">Demonstrativ — Referenzbilder und Profile sind Beispiele.</p>'
            if ctx.demo
            else ""
        )

        # Always materialize a photo layer — empty stage = black void = trust fail.
        media = (
            f'<img class="cr-hero-photo" src="assets/hero.jpg" alt="{name}" '
            f'width="1600" height="900" decoding="async">'
        )
        if (ctx.hero_video or "").strip():
            v = _esc(ctx.hero_video.strip())
            media = (
                f'<video class="cr-hero-video" autoplay muted loop playsinline '
                f'poster="assets/hero.jpg" aria-hidden="true">'
                f'<source src="{v}" type="video/mp4"></video>'
            )

        cases = _craft_cases(ctx.niche_id, city)
        crew = _craft_crew(ctx.niche_id)
        kit = _craft_kit(ctx.niche_id)
        fi = first_impression_copy_html(
            ctx,
            cta_href="#cc-contact",
            cta_class="cr-btn",
            extra_cta_html='<a class="cr-btn cr-btn-ghost" href="#cr-cases">Projekte</a>',
        )
        site_beat = (
            '<p class="cr-site-beat" data-atmosphere="1">'
            "Baustelle · Material · Handwerk</p>"
        )

        from app.factory.renderers.enrichment import (
            ENRICHMENT_CSS,
            photo_band_html,
            rich_about_html,
            rich_services_html,
        )

        hero = f"""
  <header class="cr-hero" data-renderer-hero="craftsman-site" data-stage="first-impression-generation" data-split-hero="1">
    <div class="cr-hero-stage" aria-hidden="true">{media}</div>
    <div class="cr-hero-board">
      <p class="cr-kicker">{name}{(' · ' + city) if city else ''}</p>
      {site_beat}
      {fi}
    </div>
  </header>
"""

        body = f"""
  <main class="cr-site" data-renderer="craftsman" id="cr-main">
    {demo}
    {rich_about_html(ctx)}
    <section class="cr-block cr-cases" id="cr-cases">
      <p class="cr-kicker">01 · Projekte</p>
      <h2>Neulich erledigt — mit Fotobeweis</h2>
      <p class="cr-lead">Keine Wortliste. Echte Auftragsarten mit Dauer und Ergebnis.</p>
      <div class="cr-case-wall">{cases}</div>
    </section>

    <section class="cr-block cr-spine" id="cr-process">
      <p class="cr-kicker">02 · Ablauf</p>
      <h2>So läuft der Auftrag</h2>
      <ol class="cr-process-spine">
        <li><span>01</span><strong>Anfrage / WhatsApp</strong></li>
        <li><span>02</span><strong>Kurz-Check</strong></li>
        <li><span>03</span><strong>Festpreis</strong></li>
        <li><span>04</span><strong>Termin</strong></li>
        <li><span>05</span><strong>Durchführung</strong></li>
        <li><span>06</span><strong>Fotodoku</strong></li>
        <li><span>07</span><strong>Saubere Übergabe</strong></li>
      </ol>
    </section>

    {rich_services_html(ctx, section_id="cr-services")}
    {photo_band_html(ctx)}

    <section class="cr-block cr-crew" id="cr-crew">
      <p class="cr-kicker">03 · Team</p>
      <h2>Menschen hinter dem Einsatz</h2>
      <div class="cr-crew-grid">{crew}</div>
    </section>

    <section class="cr-block cr-kit" id="cr-kit">
      <p class="cr-kicker">04 · Ausrüstung</p>
      <h2>Werkzeug & Fahrzeug</h2>
      <ul class="cr-kit-list">{kit}</ul>
    </section>

    <section class="cr-block cr-ask" id="cr-ask">
      <p class="cr-kicker">Kontakt</p>
      <h2>Festpreis anfragen</h2>
      <div class="cr-contact">
        <p><strong>Telefon</strong> <a href="tel:{phone}">{phone}</a></p>
        <p><strong>E-Mail</strong> <a href="mailto:{email}">{email}</a></p>
        <p><strong>Zeiten</strong> {hours}</p>
      </div>
      <a class="cr-btn" href="tel:{phone}">Jetzt anrufen</a>
    </section>
  </main>
"""

        nav = (
            ' <a href="#rx-about">Unternehmen</a>'
            ' <a href="#cr-cases">Projekte</a>'
            ' <a href="#cr-services">Leistungen</a>'
            ' <a href="#cr-crew">Team</a>'
            ' <a href="#rx-photos">Einblicke</a>'
            ' <a href="#cc-contact">Kontakt</a>'
        )

        return RenderedSite(
            strategy_id=self.id,
            hero_html=hero,
            body_html=body,
            css=_FI_BASE_CSS + ENRICHMENT_CSS + _CRAFTSMAN_CSS,
            js="",
            nav_links_html=nav,
            hero_layout_attr="craftsman",
            extras={"forbids_pillow_premium": True},
        )


def _craft_cases(niche_id: str, city: str) -> str:
    niche = (niche_id or "").lower()
    loc = city or "Region"
    if niche == "dachreinigung":
        items = (
            ("Haus Nürnberg-Nord", "Dachreinigung · 1 Tag", "Demo"),
            ("Familienhaus Fürth", "Imprägnierung · 1–2 Tage", "Demo"),
            ("Villa Erlangen", "Inspektion + Doku · 2 Tage", "Demo"),
            ("Townhouse Schwabach", "Rinne + Reinigung · 1 Tag", "Demo"),
        )
    elif niche == "zaunbau":
        items = (
            ("Grundstück Erlangen", "Metallzaun · 3 Tage", "Demo"),
            ("Garten Nürnberg", "Holzlatten · 2 Tage", "Demo"),
            ("Gewerbe Fürth", "Toranlage · 4 Tage", "Demo"),
        )
    elif niche in ("gartenpflege", "green"):
        items = (
            (f"Garten {loc}", "Pflege + Heckenschnitt · 1 Tag", "Demo"),
            (f"Terrasse {loc}", "Reinigung · Halbtag", "Demo"),
            (f"Anlage {loc}", "Saisonpflege · 2 Tage", "Demo"),
        )
    else:
        # handwerk / cleaning / default — Meister auf Abruf projects
        items = (
            (f"Badrenovierung {loc}", "4 Tage · Fliesen & Armaturen", "Demo"),
            (f"IKEA-Küche {loc}", "2 Tage · Montage komplett", "Demo"),
            (f"Streichen 78 m² {loc}", "3 Tage · Wände + Decke", "Demo"),
            (f"Vinylboden {loc}", "2 Tage · inkl. Leisten", "Demo"),
            (f"Büro-Auffrischung {loc}", "3 Tage · Maler + Montage", "Demo"),
            (f"Lampen & Regale {loc}", "Halbtag · Festpreis", "Demo"),
        )
    parts = []
    for i, (title, meta, chip) in enumerate(items):
        img = f"assets/gallery_{(i % 3) + 1}.jpg"
        parts.append(
            f"""
<article class="cr-case">
  <div class="cr-case-visual" aria-hidden="true"
       style="background-image:linear-gradient(180deg,rgba(10,12,14,.15),rgba(10,12,14,.5)),url('{_esc(img)}')"></div>
  <span class="cr-chip">{_esc(chip)}</span>
  <h3>{_esc(title)}</h3>
  <p>{_esc(meta)}</p>
</article>"""
        )
    return "".join(parts)


def _craft_crew(niche_id: str) -> str:
    niche = (niche_id or "").lower()
    if niche == "dachreinigung":
        people = (
            ("Jonas Weber", "Gründer", "assets/gallery_1.jpg"),
            ("Anna Becker", "Dachreinigung", "assets/gallery_2.jpg"),
            ("Lukas Hoffmann", "Höhenarbeit", "assets/gallery_3.jpg"),
        )
    else:
        people = (
            ("Tom Berger", "Meister", "assets/gallery_1.jpg"),
            ("Mira Schulz", "Montage", "assets/gallery_2.jpg"),
            ("Jonas Krämer", "Maler", "assets/gallery_3.jpg"),
            ("Lea Vogt", "Disposition", "assets/gallery_1.jpg"),
        )
    parts = []
    for name, role, img in people:
        parts.append(
            f"""
<article class="cr-person">
  <div class="cr-person-photo" style="background-image:url('{_esc(img)}')" aria-hidden="true"></div>
  <h3>{_esc(name)}</h3>
  <p>{_esc(role)}</p>
</article>"""
        )
    return "".join(parts)


def _craft_kit(niche_id: str) -> str:
    niche = (niche_id or "").lower()
    if niche == "dachreinigung":
        items = (
            "Mercedes Sprinter",
            "Kärcher Professional",
            "Sicherheitsgurte",
            "Arbeitsbühne",
        )
    else:
        items = (
            "Einsatzfahrzeug mit Logo",
            "Bosch / Makita Akku-Werkzeug",
            "Milwaukee Bohrhammer",
            "Laser-Wasserwaage",
            "Abdeck- & Saugsysteme",
        )
    return "".join(f"<li>{_esc(x)}</li>" for x in items)


_CRAFTSMAN_CSS = """
/* CraftsmanRenderer — work-site architecture (not Layout D ladder) */
body[data-renderer="craftsman"] .topbar { border-bottom: 1px solid rgba(255,255,255,.12); }
.cr-hero {
  display: grid;
  grid-template-columns: 1.15fr 0.85fr;
  min-height: 88vh;
  background: #12161c;
  color: #e8eef2;
}
.cr-hero-stage {
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(145deg, rgba(20,28,36,.25), rgba(12,16,22,.55)),
    url("assets/hero.jpg") center/cover,
    #1a2430;
}
.cr-hero-photo, .cr-hero-video {
  width: 100%; height: 100%; object-fit: cover; display: block;
  min-height: 88vh;
}
.cr-hero-board {
  display: flex; flex-direction: column; justify-content: center;
  padding: clamp(1.5rem, 4vw, 3.5rem);
  gap: 1rem;
  background: linear-gradient(160deg, #1a222c, #0f141a);
}
.cr-kicker {
  margin: 0; font-size: .72rem; letter-spacing: .14em; text-transform: uppercase;
  opacity: .65;
}
.cr-site-beat {
  margin: 0; font-size: .78rem; letter-spacing: .12em; text-transform: uppercase;
  opacity: .55; color: #f59e0b;
}
.cr-hero h1 {
  margin: 0; font-size: clamp(1.9rem, 4vw, 3.1rem); line-height: 1.1;
  font-weight: 650; letter-spacing: -0.02em; max-width: 14ch;
}
.cr-lead { margin: 0; opacity: .82; max-width: 34ch; line-height: 1.55; }
.cr-hero-actions { display: flex; flex-wrap: wrap; gap: .6rem; margin-top: .4rem; }
.cr-btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: .7rem 1.15rem; background: #c9d6de; color: #101418;
  text-decoration: none; font-weight: 600; border-radius: 2px;
}
.cr-btn-ghost {
  background: transparent; color: #e8eef2;
  border: 1px solid rgba(232,238,242,.35);
}
.cr-proof-rail {
  list-style: none; margin: 1rem 0 0; padding: 0;
  display: flex; flex-wrap: wrap; gap: .45rem;
}
.cr-proof-rail li {
  font-size: .78rem; padding: .35rem .55rem;
  border: 1px solid rgba(232,238,242,.2);
  opacity: .85;
}
.cr-site { background: #0f1318; color: #e6edf2; }
.cr-demo {
  margin: 0; padding: .75rem 1.25rem;
  font-size: .75rem; opacity: .7;
  border-bottom: 1px solid rgba(255,255,255,.08);
}
.cr-block {
  padding: clamp(2.5rem, 6vw, 4.5rem) clamp(1.25rem, 4vw, 3rem);
  max-width: 1120px; margin: 0 auto;
}
.cr-block h2 {
  margin: .2rem 0 1.4rem;
  font-size: clamp(1.5rem, 3vw, 2.2rem);
}
.cr-case-wall {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  grid-auto-rows: minmax(160px, auto);
  gap: .85rem;
}
.cr-case {
  border: 1px solid rgba(255,255,255,.1);
  background: #161c24;
  padding: 0 0 1rem;
  display: flex; flex-direction: column;
}
.cr-case:first-child { grid-row: span 2; }
.cr-case-visual {
  min-height: 120px;
  background-size: cover;
  background-position: center;
  background-color: #1a2430;
}
.cr-case:first-child .cr-case-visual { min-height: 240px; }
.cr-case h3, .cr-case p, .cr-chip { padding-left: 1rem; padding-right: 1rem; }
.cr-chip {
  display: inline-block; margin: .75rem 0 .25rem;
  font-size: .65rem; letter-spacing: .08em; text-transform: uppercase; opacity: .55;
}
.cr-case h3 { margin: 0 0 .25rem; font-size: 1.05rem; }
.cr-case p { margin: 0; opacity: .75; font-size: .88rem; }
.cr-process-spine {
  list-style: none; margin: 0; padding: 0;
  display: grid; gap: 0;
  border-left: 2px solid rgba(201,214,222,.45);
  margin-left: .4rem;
}
.cr-process-spine li {
  position: relative;
  padding: .65rem 0 .65rem 1.4rem;
  display: grid; grid-template-columns: 2.2rem 1fr; gap: .6rem; align-items: baseline;
}
.cr-process-spine li::before {
  content: ""; position: absolute; left: -5px; top: 1rem;
  width: 8px; height: 8px; border-radius: 50%; background: #c9d6de;
}
.cr-process-spine span { opacity: .45; font-size: .75rem; letter-spacing: .08em; }
.cr-kit-list, .cr-offer-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-wrap: wrap; gap: .55rem;
}
.cr-kit-list li, .cr-offer-list li {
  padding: .55rem .9rem;
  border: 1px solid rgba(255,255,255,.14);
  font-size: .9rem;
}
.cr-crew-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}
.cr-person {
  background: #161c24;
  border: 1px solid rgba(255,255,255,.1);
  overflow: hidden;
}
.cr-person-photo {
  height: 140px;
  background-size: cover;
  background-position: center;
  background-color: #1a2430;
}
.cr-person h3 { margin: .75rem .9rem .2rem; font-size: 1rem; }
.cr-person p { margin: 0 .9rem 1rem; font-size: .85rem; opacity: .7; }
.cr-benefit-row {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: .75rem; margin-top: 1.25rem;
}
.cr-benefit {
  padding: 1rem; border-top: 2px solid rgba(201,214,222,.5);
  background: #161c24;
}
.cr-benefit p { margin: 0; font-size: .92rem; line-height: 1.45; }
.cr-contact p { margin: 0 0 .55rem; }
.cr-ask .cr-btn { margin-top: 1rem; }
@media (max-width: 860px) {
  .cr-hero { grid-template-columns: 1fr; min-height: 0; }
  .cr-hero-photo, .cr-hero-video { min-height: 42vh; }
  .cr-case-wall { grid-template-columns: 1fr; }
  .cr-case:first-child { grid-row: auto; }
}
"""


__all__ = ["CraftsmanRenderer"]
