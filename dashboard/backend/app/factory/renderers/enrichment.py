"""Rich body blocks for Strategy sites — company + services + photo panels.

Business / Premium must feel like a real German firm:
  - left media panels (not text-only)
  - service cards with descriptions
  - about with substance
  - niche photo band (semi-transparent overlays)
"""

from __future__ import annotations

import html as html_lib

from app.factory.renderers.base import RenderContext

_esc = html_lib.escape


def _service_blurb(name: str, niche: str, i: int) -> str:
    n = (niche or "").lower()
    templates = {
        "auto": (
            "Schriftliche Diagnose vor dem Preis — transparente Empfehlung.",
            "Wartung nach Herstellervorgabe, Ersatzteile nach Absprache.",
            "Termin mit Bestätigung, Abholung auf Wunsch.",
        ),
        "dachreinigung": (
            "Vor-Ort-Besichtigung, Festpreis, Vorher/Nachher-Dokumentation.",
            "Versichert arbeiten — Schutz für Dach und Grundstück.",
            "Moos, Algen, Rinne — sauber und nachvollziehbar.",
        ),
        "psychology": (
            "Erstgespräch mit Klarheit über Ablauf und Honorar.",
            "Geschützter Rahmen — online oder vor Ort.",
            "Tempo des Menschen, keine Methodenfabrik.",
        ),
        "restaurant": (
            "Saisonale Gerichte, Allergene klar ausgewiesen.",
            "Reservierung mit Bestätigung — Tisch ohne Theater.",
            "Abendkarte und Mittagstisch mit frischen Produkten.",
        ),
        "law": (
            "Schriftliche Einschätzung nach dem Erstgespräch.",
            "Klare Honorare — keine leeren Versprechen.",
            "Wirtschaftsrecht und Vertragsprüfung mit Ruhe.",
        ),
        "beauty": (
            "Beratung vor dem Schnitt — Ergebnis, das hält.",
            "Premium-Produkte, ehrliche Empfehlung.",
            "Online-Termine, ruhiges Atelier.",
        ),
        "dental": (
            "Aufklärung vor Behandlung, Kostenplan schriftlich.",
            "Prophylaxe und Ästhetik mit moderner Technik.",
            "Schmerzarme Abläufe, ruhige Praxis.",
        ),
        "handwerk": (
            "Festpreisangebot vor Start — keine Baustellen-Überraschung.",
            "Pünktliche Termine, saubere Übergabe.",
            "Ein Ansprechpartner von Aufmaß bis Abnahme.",
        ),
        "fitness": (
            "Probetraining ohne Vertragsfalle.",
            "Coaches vor Ort, Pläne für den Alltag.",
            "Flexible Zeiten, moderne Geräte.",
        ),
        "realestate": (
            "Bewertung mit lokaler Marktkenntnis.",
            "Exposé digital, Begleitung bis Notar.",
            "Transparente Provision — ohne Nebel.",
        ),
    }
    pool = templates.get(n) or (
        "Klarer Ablauf, fester Ansprechpartner.",
        "Transparente Preise und Termine.",
        "Qualität, die Sie vor Ort spüren.",
    )
    return pool[i % len(pool)]


def rich_services_html(ctx: RenderContext, *, section_id: str = "co-services") -> str:
    cards = []
    for i, s in enumerate(ctx.services[:8]):
        if not str(s).strip():
            continue
        blurb = _service_blurb(str(s), ctx.niche_id, i)
        # Prefer dedicated service plates; fall back to distinct gallery plates
        svc_slot = f"assets/service_{(i % 3) + 1}.jpg"
        gal_slot = f"assets/gallery_{(i % 3) + 1}.jpg"
        img = svc_slot
        cards.append(
            f"""<article class="rx-svc-card">
  <div class="rx-svc-media" style="background-image:linear-gradient(160deg,rgba(15,20,16,.28),rgba(15,20,16,.68)),url('{_esc(img)}')" data-visual-role="service" data-visual-fallback="{_esc(gal_slot)}"></div>
  <div class="rx-svc-body">
    <h3>{_esc(s)}</h3>
    <p>{_esc(blurb)}</p>
  </div>
</article>"""
        )
    if not cards:
        return ""
    return f"""
    <section class="rx-services" id="{_esc(section_id)}">
      <p class="rx-eyebrow">Leistungen</p>
      <h2>Was Sie konkret bekommen</h2>
      <p class="rx-lead">Nicht nur Stichworte — der Nutzen hinter jeder Leistung.</p>
      <div class="rx-svc-grid">{"".join(cards)}</div>
    </section>"""


def rich_about_html(ctx: RenderContext) -> str:
    about = (ctx.about or "").strip()
    who = (ctx.offer_line or ctx.subtitle or "").strip()
    city = (ctx.city or "").strip()
    benefits = "".join(
        f"<li>{_esc(b)}</li>" for b in ctx.benefits[:5] if str(b).strip()
    )
    # Extra company substance so Business/Premium never feel like a slogan sheet
    extras = []
    if ctx.city:
        extras.append(
            f"Vor Ort in {_esc(ctx.city)} — erreichbar für Erstgespräch, Termin und Rückfragen."
        )
    if ctx.hours:
        extras.append(f"Öffnungszeiten: {_esc(ctx.hours)}.")
    if ctx.phone:
        extras.append(
            f"Direkter Draht: {_esc(ctx.phone)} — Anruf oder WhatsApp ohne Umwege."
        )
    extra_p = "".join(f"<p>{p}</p>" for p in extras)
    return f"""
    <section class="rx-about" id="rx-about">
      <div class="rx-about-media" style="background-image:linear-gradient(135deg,rgba(15,20,16,.25),rgba(15,20,16,.65)),url('assets/background.jpg')"></div>
      <div class="rx-about-copy">
        <p class="rx-eyebrow">Unternehmen{(' · ' + _esc(city)) if city else ''}</p>
        <h2>Über {_esc(ctx.business_name)}</h2>
        <p class="rx-lead">{_esc(who)}</p>
        <p>{_esc(about)}</p>
        {extra_p}
        <ul class="rx-about-points">{benefits}</ul>
      </div>
    </section>"""


def photo_band_html(ctx: RenderContext) -> str:
    """Semi-transparent niche photo strip — Auto-style density (6 plates)."""
    caps = {
        "auto": ("Werkstatt", "Diagnose", "Straße", "Motor", "Detail", "Übergabe"),
        "dachreinigung": ("Dach", "Regen", "Ergebnis", "Rinne", "Vorher", "Nachher"),
        "psychology": ("Raum", "Licht", "Gespräch", "Pause", "Ruhe", "Weg"),
        "restaurant": ("Küche", "Tisch", "Abend", "Wein", "Detail", "Gast"),
        "law": ("Fassade", "Ordnung", "Akte", "Besprechung", "Ruhe", "Klarheit"),
        "beauty": ("Atelier", "Ritual", "Detail", "Spiegel", "Produkt", "Ergebnis"),
        "dental": ("Praxis", "Präzision", "Ruhe", "Team", "Technik", "Lächeln"),
        "handwerk": (
            "Badrenovierung",
            "Küchenmontage",
            "Anstrich",
            "Boden",
            "Werkzeug",
            "Übergabe",
        ),
        "cleaning": (
            "Vorher",
            "Reinigung",
            "Detail",
            "Nachher",
            "Team",
            "Übergabe",
        ),
        "fitness": ("Training", "Coach", "Energie", "Geräte", "Gruppe", "Fokus"),
        "realestate": ("Objekt", "Stadt", "Schlüssel", "Raum", "Fassade", "Übergabe"),
    }.get((ctx.niche_id or "").lower(), ("Arbeit", "Detail", "Ort", "Team", "Prozess", "Ergebnis"))
    cells = []
    # Prefer distinct floor plates — never force hero into every band cell.
    plate_cycle = (
        "assets/gallery_1.jpg",
        "assets/gallery_2.jpg",
        "assets/gallery_3.jpg",
        "assets/background.jpg",
        "assets/illustration.jpg",
        "assets/gallery.jpg",
    )
    for i, cap in enumerate(caps):
        src = plate_cycle[i % len(plate_cycle)]
        cells.append(
            f"""<figure class="rx-band-cell">
  <div class="rx-band-img" style="background-image:linear-gradient(180deg,rgba(10,12,14,.18),rgba(10,12,14,.58)),url('{_esc(src)}')"></div>
  <figcaption>{_esc(cap)}</figcaption>
</figure>"""
        )
    return f"""
    <section class="rx-photo-band" id="rx-photos" aria-label="Einblicke">
      <p class="rx-eyebrow">Einblicke</p>
      <h2>Arbeit auf dem Objekt — nicht nur Worte</h2>
      <div class="rx-band-grid">{"".join(cells)}</div>
    </section>"""


def split_hero_shell(
    ctx: RenderContext,
    *,
    fi_html: str,
    eyebrow: str,
    hero_class: str,
    band_class: str,
    media_class: str = "rx-hero-media",
) -> str:
    """Left niche media panel + right First Impression — Business/Premium bar.

    Media sits under a solid copy panel (not transparent over photo) so text
    never blends into the background — Owner FAIL when ink washes out.
    """
    return f"""
  <header class="{_esc(hero_class)}" data-stage="first-impression-generation" data-split-hero="1">
    <div class="{_esc(media_class)}" aria-hidden="true"
         style="background-image:linear-gradient(115deg,rgba(12,16,20,.12),rgba(12,16,20,.45)),url('assets/hero.jpg')"></div>
    <div class="{_esc(band_class)}" data-fi-panel="1">
      <p class="rx-hero-eyebrow">{_esc(eyebrow)}</p>
      {fi_html}
    </div>
  </header>"""


ENRICHMENT_CSS = """
/* Split hero — left media panel (Business/Premium) */
[data-split-hero="1"] {
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  min-height: 78vh;
}
.rx-hero-media, .co-hero-media, .ed-hero-media, .cl-hero-media,
.lg-hero-media, .rt-hero-media, .lx-hero-media, .mn-hero-media {
  min-height: 78vh;
  background-size: cover;
  background-position: center;
  position: relative;
}
.rx-hero-media::after, .co-hero-media::after, .ed-hero-media::after,
.cl-hero-media::after, .lg-hero-media::after, .rt-hero-media::after,
.lx-hero-media::after, .mn-hero-media::after {
  content: "";
  position: absolute; inset: 0;
  background: linear-gradient(90deg, transparent 30%, rgba(10,12,14,.55));
  pointer-events: none;
}
.ed-hero-media::after, .cl-hero-media::after {
  background: linear-gradient(90deg, rgba(247,244,239,.05), rgba(247,244,239,.88) 88%);
}
.lx-hero-media::after, .rt-hero-media::after {
  background: linear-gradient(105deg, transparent 25%, rgba(8,10,14,.72));
}
.rx-hero-eyebrow {
  margin: 0 0 .75rem; font-size: .72rem;
  letter-spacing: .14em; text-transform: uppercase; opacity: .55;
}
.rx-eyebrow {
  margin: 0 0 .5rem; font-size: .72rem;
  letter-spacing: .12em; text-transform: uppercase; opacity: .55;
}
.rx-lead { max-width: 42ch; line-height: 1.55; opacity: .85; }
.rx-services, .rx-about, .rx-photo-band {
  padding: clamp(2.5rem, 6vw, 4rem) clamp(1.25rem, 5vw, 3rem);
  max-width: 1120px; margin: 0 auto;
}
.rx-svc-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1rem;
  margin-top: 1.5rem;
}
.rx-svc-card {
  border: 1px solid rgba(0,0,0,.08);
  background: #fff;
  overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease;
}
.rx-svc-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 14px 32px rgba(15, 23, 42, .10);
  border-color: rgba(0,0,0,.12);
}
.rx-svc-media {
  min-height: 168px;
  background-size: cover;
  background-position: center;
  transition: transform .45s ease;
}
.rx-svc-card:hover .rx-svc-media {
  transform: scale(1.03);
}
.rx-svc-body { padding: 1.05rem 1.15rem 1.3rem; }
.rx-svc-body h3 { margin: 0 0 .45rem; font-size: 1.08rem; letter-spacing: -0.01em; }
.rx-svc-body p { margin: 0; font-size: .9rem; line-height: 1.55; opacity: .8; }
.rx-about {
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
  gap: clamp(1.25rem, 4vw, 2.5rem);
  align-items: stretch;
  max-width: 1120px;
}
.rx-about-media {
  min-height: 320px;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
}
.rx-about-copy h2 {
  margin: 0 0 .65rem;
  font-size: clamp(1.45rem, 2.4vw, 1.9rem);
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.rx-about-points {
  margin: 1rem 0 0; padding: 0 0 0 1.1rem;
  display: grid; gap: .35rem;
}
.rx-band-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: .85rem;
  margin-top: 1.35rem;
}
.rx-band-cell { margin: 0; }
.rx-band-img {
  min-height: 176px;
  background-size: cover;
  background-position: center;
  border-radius: 4px;
  transition: transform .4s ease;
}
.rx-band-cell:hover .rx-band-img {
  transform: scale(1.02);
}
.rx-band-cell:nth-child(4) .rx-band-img,
.rx-band-cell:nth-child(5) .rx-band-img,
.rx-band-cell:nth-child(6) .rx-band-img {
  min-height: 140px;
  opacity: .82;
}
.rx-band-cell figcaption {
  margin-top: .4rem; font-size: .78rem;
  letter-spacing: .08em; text-transform: uppercase; opacity: .55;
}
body[data-renderer] .co-site,
body[data-renderer] .ed-site,
body[data-renderer] .cl-site,
body[data-renderer] .lg-site,
body[data-renderer] .rt-site,
body[data-renderer] .lx-site,
body[data-renderer] .mn-site {
  position: relative;
}
@media (max-width: 860px) {
  [data-split-hero="1"] {
    display: grid !important;
    grid-template-columns: 1fr !important;
    grid-template-rows: auto auto;
    min-height: auto !important;
    clip-path: none !important;
  }
  [data-split-hero="1"] .rx-hero-media,
  [data-split-hero="1"] .co-hero-media,
  [data-split-hero="1"] .ed-hero-media,
  [data-split-hero="1"] .cl-hero-media,
  [data-split-hero="1"] .lg-hero-media,
  [data-split-hero="1"] .rt-hero-media,
  [data-split-hero="1"] .lx-hero-media,
  [data-split-hero="1"] .mn-hero-media {
    min-height: min(52vh, 440px) !important;
    max-height: 56vh;
    width: 100%;
    order: 0;
  }
  [data-split-hero="1"] [data-fi-panel="1"],
  [data-split-hero="1"] .rt-plate,
  [data-split-hero="1"] .co-plate,
  [data-split-hero="1"] .ed-plate,
  [data-split-hero="1"] .cl-plate,
  [data-split-hero="1"] .lg-plate,
  [data-split-hero="1"] .lx-plate,
  [data-split-hero="1"] .mn-plate {
    order: 1;
    min-height: auto;
  }
  .rx-about { grid-template-columns: 1fr; }
  .rx-band-grid { grid-template-columns: 1fr; }
}
"""


def enriched_body(
    ctx: RenderContext,
    *,
    services_id: str = "co-services",
    extra_before: str = "",
    extra_after: str = "",
) -> str:
    return (
        extra_before
        + rich_about_html(ctx)
        + rich_services_html(ctx, section_id=services_id)
        + photo_band_html(ctx)
        + extra_after
    )


__all__ = [
    "ENRICHMENT_CSS",
    "enriched_body",
    "photo_band_html",
    "rich_about_html",
    "rich_services_html",
    "split_hero_shell",
]
