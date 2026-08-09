"""Make vitrine demos show unique niche photos + fix law copy errors.

- Unhide service media / full photo band
- Unique gallery slots (no 1-2-3 recycle)
- Niche-correct Einblicke headlines + captions (law ≠ Handwerk)
- Unique service blurbs (especially Kanzlei)
- Store product cards: force visible media + unique graded frames
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "dashboard" / "frontend" / "public"
PREVIEWS = PUBLIC / "package-previews"
SITES_DIR = PREVIEWS / "sites" / "premium"
STORES_DIR = PREVIEWS / "stores" / "premium"

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

PHOTO_BAND = {
    "beauty": (
        "Atmosphäre im Atelier",
        ["Spiegel", "Ruhe", "Pflege", "Licht", "Details", "Empfang", "Behandlung", "Finish"],
    ),
    "cleaning": (
        "Sauberkeit, die man sieht",
        ["Vorher", "Nachher", "Team", "Büro", "Privat", "Detail", "Material", "Ergebnis"],
    ),
    "it_support": (
        "Werkbank statt Hotline-Theater",
        ["Diagnose", "Board", "Labor", "Daten", "Reparatur", "Test", "Übergabe", "Support"],
    ),
    "dental": (
        "Praxis, die Vertrauen schafft",
        ["Empfang", "Behandlungsraum", "Team", "Technik", "Hygiene", "Beratung", "Ruhe", "Nachsorge"],
    ),
    "restaurant": (
        "Küche, Service, Atmosphäre",
        ["Gericht", "Saal", "Bar", "Team", "Detail", "Abend", "Wein", "Empfang"],
    ),
    "handwerk": (
        "Arbeit auf dem Objekt — mit Fotobeweis",
        ["Baustelle", "Material", "Montage", "Detail", "Team", "Werkzeug", "Ergebnis", "Übergabe"],
    ),
    "law": (
        "Einblicke in die Kanzlei — Ruhe statt Show",
        ["Kanzlei", "Beratung", "Akte", "Besprechung", "Frankfurt", "Team", "Fokus", "Vertraulichkeit"],
    ),
    "auto": (
        "Werkstatt mit klarer Diagnose",
        ["Hebebühne", "Diagnose", "Reifen", "Motor", "Team", "Service", "Teile", "Übergabe"],
    ),
}

LAW_SERVICES = [
    ("Erstberatung", "60 Minuten Klarheit: Lage, Risiken und nächste Schritte — schriftlich festgehalten."),
    ("Vertragsprüfung", "Kritische Klauseln markiert, Alternativen vorgeschlagen — bevor Sie unterschreiben."),
    ("Gesellschaftsrecht", "Gründung, Gesellschafterstreit, Verträge — strukturiert und vertraulich."),
    ("Arbeitsrecht", "Abmahnung, Kündigung, Aufhebungsvertrag — Orientierung vor dem nächsten Schritt."),
    ("Vertretung", "Außergerichtlich und vor Gericht — mit ruhiger, nachvollziehbarer Strategie."),
    ("Verhandlungen", "Interessen klar vertreten, Eskalation vermeiden, Ergebnisse dokumentieren."),
    ("Markenrecht", "Schutz, Abmahnung, Lizenz — Rechte sichern, ohne Panikmache."),
    ("Datenschutz", "DSGVO-Pflichten verständlich: was nötig ist, was entbehrlich bleibt."),
]

# Niche service blurbs (title stays; replace repeating p text by card order)
NICHE_SERVICE_BLURBS: dict[str, list[str]] = {
    "law": [b for _, b in LAW_SERVICES],
    "beauty": [
        "Schnitt mit Beratung — Ergebnis, das den Alltag trägt.",
        "Farbe ehrlich empfohlen, Premium-Produkte ohne Upsell-Druck.",
        "Maniküre im ruhigen Atelier — Termin online buchbar.",
        "Gesichtsbehandlung mit klarer Hautanalyse vor dem Start.",
        "Styling für Anlässe — Probe und Look vorher abgestimmt.",
        "Pflegerituale, die zu Ihrer Haut und Ihrem Tempo passen.",
        "Brauen & Wimpern präzise — natürliches Finish.",
        "Nachsorge-Tipps schriftlich — damit das Ergebnis hält.",
    ],
    "cleaning": [
        "Unterhaltsreinigung mit Checkliste — sichtbar sauber.",
        "Grundreinigung für Wohnung oder Büro nach Festpreis.",
        "Fenster & Glas streifenfrei, auch in oberen Etagen.",
        "Büroreinigung außerhalb Ihrer Kernzeiten.",
        "Umzugsreinigung mit Übergabeprotokoll.",
        "Küche & Bad intensiv — Kalk und Fett weg.",
        "Gewerbe: regelmäßig, dokumentiert, ansprechbar.",
        "Express-Einsatz, wenn es schnell gehen muss.",
    ],
    "it_support": [
        "Fehlerdiagnose vor dem Teilewechsel — ehrlich kalkuliert.",
        "Datenrettung mit Priorität auf Ihre Dateien.",
        "Laptop-Reparatur inkl. Funktionstest.",
        "Viren- und Malware-Bereinigung inkl. Härten.",
        "Netzwerk & WLAN stabilisieren — vor Ort.",
        "Backup-Konzept, das Sie wirklich verstehen.",
        "Firmen-IT: Remote + Vor-Ort ohne Theater.",
        "Gerätetausch mit Übernahme Ihrer Daten.",
    ],
    "dental": [
        "Vorsorge mit ruhiger Aufklärung — ohne Druck.",
        "Professionelle Zahnreinigung mit Zeit für Fragen.",
        "Ästhetik: Ergebnis vorher besprochen.",
        "Schmerzarme Behandlung, klare Kosteninfo.",
        "Implantat-Beratung verständlich und ehrlich.",
        "Kinderzahnheilkunde mit Geduld.",
        "Notfälle: schnelle Ersteinschätzung.",
        "Recall-Erinnerung, damit Vorsorge bleibt.",
    ],
    "restaurant": [
        "Saisonaler Mittagstisch — frisch, nicht austauschbar.",
        "Abendmenü mit Weinempfehlung vom Haus.",
        "Reservierung ohne Telefon-Marathon.",
        "Private Events mit festem Ablauf.",
        "Vegetarische Gerichte als gleichwertige Karte.",
        "Mittag für Büros in der Nähe — pünktlich.",
        "Dessert & Bar — Abschluss mit Charakter.",
        "Catering-Anfragen mit klarer Kalkulation.",
    ],
    "handwerk": [
        "Festpreis nach Kurz-Check — schriftlich.",
        "Montage mit Fotodoku vor und nach dem Einsatz.",
        "Malerarbeiten sauber abgedeckt und termintreu.",
        "Böden verlegen inkl. Leisten und Übergabe.",
        "Kleine Reparaturen gebündelt — ein Termin.",
        "Bad-/Küchenmontage mit Funktionscheck.",
        "Materialvorschlag mit Vor- und Nachteilen.",
        "Nachsorge: eine Nachfrage nach dem Auftrag.",
    ],
    "auto": [
        "Schriftliche Diagnose vor dem Preis.",
        "Inspektion nach Herstellervorgabe.",
        "Bremsen & Verschleißteile mit Foto-Nachweis.",
        "Reifenwechsel inkl. Wuchten und Check.",
        "Klimaservice mit messbarem Ergebnis.",
        "HU/AU-Vorbereitung ohne Überraschungen.",
        "Batterie & Starthilfe — ehrlich empfohlen.",
        "Shuttle auf Wunsch während der Reparatur.",
    ],
}

MEDIA_CSS = """
<style id="vitrine-media-visible">
/* Always show service photos + full Einblicke grid */
html body .rx-svc-media {
  display: block !important;
  min-height: 150px !important;
  background-size: cover !important;
  background-position: center !important;
}
html body .rx-svc-card {
  display: grid !important;
  grid-template-columns: 1fr !important;
  gap: 0 !important;
  border: 1px solid rgba(28,25,23,.1) !important;
  background: var(--vi-surface, #fff) !important;
  overflow: hidden;
}
html body .rx-svc-media {
  max-height: 200px !important;
  min-height: 160px !important;
}
@media (min-width: 720px) {
  html body .rx-svc-card {
    grid-template-columns: minmax(180px, 36%) 1fr !important;
  }
  html body .rx-svc-media {
    max-height: none !important;
    min-height: 100% !important;
  }
}
html body .rx-band-cell { display: block !important; }
html body .rx-band-grid {
  display: grid !important;
  grid-template-columns: repeat(2, 1fr) !important;
  gap: .75rem !important;
}
@media (min-width: 720px) {
  html body .rx-band-grid { grid-template-columns: repeat(4, 1fr) !important; }
}
html body .rx-band-img {
  display: block !important;
  min-height: 160px !important;
  height: 160px !important;
  opacity: 1 !important;
  background-size: cover !important;
  background-position: center !important;
  border-radius: 8px;
}
html body .rx-photo-band figcaption {
  font-size: .85rem;
  color: var(--vi-ink, #1c1917) !important;
  opacity: 1 !important;
  margin-top: .35rem;
}
/* Store products always visible */
html body .product-media-slot,
html body .card-media,
html body [data-product-card] img {
  display: block !important;
  min-height: 180px !important;
  object-fit: cover !important;
  width: 100% !important;
  opacity: 1 !important;
}
</style>
"""


def _md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


def _grade_unique(src: Path, dest: Path, salt: int) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(src) as im:
        im = im.convert("RGB")
        # Unique crop/grade per salt so slots never look identical
        w, h = im.size
        dx = (salt * 17) % max(1, w // 12)
        dy = (salt * 11) % max(1, h // 12)
        im = im.crop((dx, dy, w - dx, h - dy))
        im = ImageOps.fit(im, (1280, 960), Image.Resampling.LANCZOS)
        im = ImageEnhance.Brightness(im).enhance(0.92 + (salt % 5) * 0.03)
        im = ImageEnhance.Contrast(im).enhance(1.05 + (salt % 4) * 0.04)
        im = ImageEnhance.Color(im).enhance(0.95 + (salt % 6) * 0.05)
        im.save(dest, "JPEG", quality=88, optimize=True)


def ensure_unique_gallery(niche: str) -> list[str]:
    assets = SITES_DIR / niche / "assets"
    sources = sorted(
        [
            p
            for p in assets.rglob("*")
            if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"} and p.is_file()
        ]
    )
    if not sources:
        return []
    rels: list[str] = []
    for i in range(1, 13):
        dest = assets / f"gallery_{i}.jpg"
        src = sources[(i * 3 + hash(niche) % 7) % len(sources)]
        _grade_unique(src, dest, salt=i * 13 + (hash(niche) % 97))
        rels.append(f"assets/gallery_{i}.jpg")
    # service-dedicated frames
    for i in range(1, 9):
        dest = assets / f"service_{i}.jpg"
        src = sources[(i * 5 + 2) % len(sources)]
        _grade_unique(src, dest, salt=100 + i * 9 + (hash(niche) % 53))
    return rels


def patch_css_media(html: str) -> str:
    html = re.sub(
        r"body\[data-niche=\"law\"\] \.rx-svc-media \{ display: none; \}",
        "body[data-niche=\"law\"] .rx-svc-media { display: block; min-height: 150px; }",
        html,
    )
    html = re.sub(
        r"body\[data-niche=\"law\"\] \.rx-svc-card \{[^}]*\}",
        "body[data-niche=\"law\"] .rx-svc-card { border-radius: 0; border: 1px solid rgba(20,22,28,.12); background: #fff; display: grid; grid-template-columns: minmax(120px,38%) 1fr; }",
        html,
        count=1,
        flags=re.S,
    )
    html = re.sub(
        r"body\[data-niche=\"law\"\] \.rx-band-cell:nth-child\(n\+5\) \{ display: none; \}",
        "body[data-niche=\"law\"] .rx-band-cell:nth-child(n+5) { display: block; }",
        html,
    )
    html = re.sub(
        r'<style id="vitrine-media-visible">.*?</style>\s*',
        "",
        html,
        flags=re.I | re.S,
    )
    if "</head>" in html:
        html = html.replace("</head>", MEDIA_CSS + "</head>", 1)
    else:
        html = MEDIA_CSS + html
    return html


def rebuild_photo_band(html: str, niche: str) -> str:
    title, caps = PHOTO_BAND[niche]
    cells = []
    for i, cap in enumerate(caps, start=1):
        cells.append(
            "<figure class=\"rx-band-cell\">"
            f"<div class=\"rx-band-img\" style=\"background-image:url('assets/gallery_{i}.jpg')\"></div>"
            f"<figcaption>{cap}</figcaption>"
            "</figure>"
        )
    new_band = (
        f'<section class="rx-photo-band" id="rx-photos" aria-label="Einblicke">'
        f'<p class="rx-eyebrow">Einblicke</p>'
        f"<h2>{title}</h2>"
        f'<div class="rx-band-grid">{"".join(cells)}</div>'
        f"</section>"
    )
    html2, n = re.subn(
        r'<section class="rx-photo-band"[^>]*>.*?</section>',
        new_band,
        html,
        count=1,
        flags=re.I | re.S,
    )
    return html2 if n else html


def rebuild_services(html: str, niche: str) -> str:
    blurbs = NICHE_SERVICE_BLURBS.get(niche)
    if not blurbs:
        return html

    # Replace each rx-svc-card media url + paragraph in order
    cards = list(
        re.finditer(
            r'<article class="rx-svc-card">.*?</article>',
            html,
            flags=re.I | re.S,
        )
    )
    if not cards:
        return html

    out = html
    # replace from end to keep offsets stable
    for idx in range(min(len(cards), 8) - 1, -1, -1):
        m = cards[idx]
        block = m.group(0)
        title_m = re.search(r"<h3>(.*?)</h3>", block, flags=re.I | re.S)
        title = title_m.group(1).strip() if title_m else f"Leistung {idx+1}"
        if niche == "law" and idx < len(LAW_SERVICES):
            title, blurb = LAW_SERVICES[idx]
        else:
            blurb = blurbs[idx % len(blurbs)]
        media = (
            f"url('assets/service_{idx+1}.jpg')"
            if (SITES_DIR / niche / "assets" / f"service_{idx+1}.jpg").exists()
            else f"url('assets/gallery_{idx+1}.jpg')"
        )
        new_block = (
            '<article class="rx-svc-card">'
            f'<div class="rx-svc-media" style="background-image:linear-gradient(160deg,rgba(15,20,16,.2),rgba(15,20,16,.45)),{media}"></div>'
            '<div class="rx-svc-body">'
            f"<h3>{title}</h3>"
            f"<p>{blurb}</p>"
            "</div></article>"
        )
        out = out[: m.start()] + new_block + out[m.end() :]
    return out


def fix_law_about(html: str) -> str:
    # Replace generic Stammgäste / Handwerk template with law voice
    html = html.replace("Stammgästen", "Mandanten")
    html = html.replace(
        "Arbeit auf dem Objekt — nicht nur Worte",
        "Einblicke in die Kanzlei — Ruhe statt Show",
    )
    about = (
        "Kanzlei Bergmann wurde 2022 in Frankfurt gegründet. "
        "Wir begleiten Unternehmen und Privatpersonen, wenn die Lage unübersichtlich wird — "
        "mit ruhiger Analyse, klaren Honoraren und schriftlicher Einschätzung nach dem Erstgespräch. "
        "Mission: Orientierung geben, bevor Konflikte eskalieren. "
        "Werte: Präzision, Vertraulichkeit, Transparenz, Verlässlichkeit. "
        "Team vor Ort: Sofia Weber (Rechtsanwältin)."
    )
    html = re.sub(
        r"(<section[^>]*rx-about[^>]*>.*?<p>)(.*?)(</p>)",
        lambda m: m.group(1) + about + m.group(3)
        if "Kanzlei Bergmann wurde" in m.group(2) or "Frankfurt" in m.group(2)
        else m.group(0),
        html,
        count=1,
        flags=re.I | re.S,
    )
    # More reliable: replace first long about paragraph containing gegründet
    html = re.sub(
        r"Kanzlei Bergmann wurde 2022 in Frankfurt gegründet\..{80,800}?",
        about,
        html,
        count=1,
        flags=re.S,
    )
    return html


def patch_site(niche: str) -> str:
    path = SITES_DIR / niche / "index.html"
    if not path.exists():
        return f"{niche}: MISSING"
    ensure_unique_gallery(niche)
    html = path.read_text(encoding="utf-8", errors="replace")
    html = patch_css_media(html)
    html = rebuild_photo_band(html, niche)
    html = rebuild_services(html, niche)
    if niche == "law":
        html = fix_law_about(html)
    path.write_text(html, encoding="utf-8")
    hero = SITES_DIR / niche / "assets" / "hero.jpg"
    return f"{niche}: media+copy ok hero={_md5(hero) if hero.exists() else '?'}"


def patch_store(niche: str) -> str:
    store = STORES_DIR / niche
    assets = store / "assets" / "images"
    if not assets.exists():
        assets = store / "assets"
    products = sorted(assets.glob("product_*.jpg"))
    if not products:
        products = sorted(assets.rglob("product_*.jpg"))
    # Re-grade each product uniquely from itself + salt
    for i, p in enumerate(products, start=1):
        _grade_unique(p, p, salt=i * 19 + (hash(niche) % 41))
    n_pages = 0
    for html_path in store.glob("*.html"):
        html = html_path.read_text(encoding="utf-8", errors="replace")
        html = re.sub(
            r'<style id="vitrine-media-visible">.*?</style>\s*',
            "",
            html,
            flags=re.I | re.S,
        )
        if "</head>" in html:
            html = html.replace("</head>", MEDIA_CSS + "</head>", 1)
        html_path.write_text(html, encoding="utf-8")
        n_pages += 1
    return f"store/{niche}: {len(products)} products, {n_pages} pages"


def main() -> None:
    for niche in SITES:
        print(patch_site(niche))
    for niche in STORES:
        print(patch_store(niche))
    print("done")


if __name__ == "__main__":
    main()
