"""Reputation Pack — proof that sells before the first call (Sprint 3).

Goal: after opening the site, the visitor thinks
  "This company has existed for years."
Even for a demo brand — every fabricated asset is labeled Demo.

Blocks:
  1. Portfolio (real-feeling cases)
  2. Team
  3. Equipment
  4. Process (full visual story)
  5. Before / After (interactive)
  6. Knowledge
  7. Trust
  + Reputation Timeline

Chain: Business Identity → Brand Book → Atmosphere → Reputation → …
"""

from __future__ import annotations

import hashlib
import html as html_lib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.factory.design_dna.brand_book import BrandBook, resolve_brand_book
from app.factory.design_dna.media_truth import enforce_media_truth_on_product

_esc = html_lib.escape

DEMO_DISCLAIMER = (
    "Demo-Inhalt · Virtus Core Preview — Projekte, Personen, Ausrüstung und "
    "Nachweise sind demonstrativ erzeugt und keine echten Referenzen."
)


@dataclass(frozen=True)
class DemoCase:
    title: str
    city: str
    task: str
    duration: str
    works: tuple[str, ...]
    before_label: str = "Vorher"
    after_label: str = "Nachher"
    demo_label: str = "Demonstrationsbeispiel"

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["works"] = list(self.works)
        return d


@dataclass(frozen=True)
class DemoPerson:
    name: str
    role: str
    focus: str = ""
    demo_label: str = "Beispielprofil"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class KnowledgeArticle:
    title: str
    teaser: str
    demo_label: str = "Demo-Artikel"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimelineEvent:
    year: str
    title: str
    detail: str
    demo_label: str = "Demo"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TrustPillar:
    title: str
    detail: str
    demo_label: str = "Demo-Beispiel"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ReputationPack:
    brand_name: str
    niche_id: str
    package_id: str
    cases: tuple[DemoCase, ...]
    team: tuple[DemoPerson, ...]
    equipment: tuple[str, ...]
    process: tuple[str, ...]
    before_after_pairs: tuple[tuple[str, str], ...]
    knowledge: tuple[KnowledgeArticle, ...]
    trust: tuple[TrustPillar, ...]
    timeline: tuple[TimelineEvent, ...]
    gallery_roles: tuple[str, ...]
    media_truth_rule: str
    fingerprint: str
    disclaimer: str = DEMO_DISCLAIMER

    def as_dict(self) -> dict[str, Any]:
        return {
            "brand_name": self.brand_name,
            "niche_id": self.niche_id,
            "package_id": self.package_id,
            "portfolio": [c.as_dict() for c in self.cases],
            "team": [t.as_dict() for t in self.team],
            "equipment": list(self.equipment),
            "process": list(self.process),
            "before_after": [{"before": a, "after": b} for a, b in self.before_after_pairs],
            "knowledge": [k.as_dict() for k in self.knowledge],
            "trust": [t.as_dict() for t in self.trust],
            "timeline": [e.as_dict() for e in self.timeline],
            "gallery_roles": list(self.gallery_roles),
            "media_truth_rule": self.media_truth_rule,
            "disclaimer": self.disclaimer,
            "fingerprint": self.fingerprint,
            "blocks": [
                "portfolio",
                "team",
                "equipment",
                "process",
                "before_after",
                "knowledge",
                "trust",
                "timeline",
            ],
        }


_NICHE_REP: dict[str, dict[str, Any]] = {
    "handwerk": {
        "cases": (
            {
                "title": "Badrenovierung Berlin-Mitte",
                "city": "Berlin",
                "task": "Fliesen, Armaturen, Silikon — bewohnte Wohnung",
                "duration": "4 Arbeitstage",
                "works": ("Demontage", "Fliesen", "Armaturen", "Fotodoku"),
                "before": "Abgenutztes Bad",
                "after": "Frisch verfugt & dicht",
            },
            {
                "title": "IKEA-Küche Montage Prenzlauer Berg",
                "city": "Berlin",
                "task": "Komplette Küche inkl. Geräte-Anschluss-Check",
                "duration": "2 Arbeitstage",
                "works": ("Aufbau", "Ausrichten", "Griffe", "Übergabe"),
                "before": "Kartons & Platten",
                "after": "Fertige Küche",
            },
            {
                "title": "Wohnung streichen 78 m²",
                "city": "Berlin",
                "task": "Wände + Decke, Abdeckung, Endreinigung",
                "duration": "3 Arbeitstage",
                "works": ("Abkleben", "Grundierung", "Anstrich", "Reinigung"),
                "before": "Vergilbte Wände",
                "after": "Gleichmäßiger Anstrich",
            },
            {
                "title": "Vinylboden Kreuzberg",
                "city": "Berlin",
                "task": "Altboden raus, neuer Vinyl inkl. Sockelleisten",
                "duration": "2 Arbeitstage",
                "works": ("Demontage", "Untergrund", "Verlegen", "Leisten"),
                "before": "Abgenutzter Belag",
                "after": "Neuer Boden",
            },
            {
                "title": "Büro-Auffrischung Friedrichshain",
                "city": "Berlin",
                "task": "Streichen, Regale, Beleuchtung",
                "duration": "3 Arbeitstage",
                "works": ("Malerarbeiten", "Montage", "Lampen", "Übergabe"),
                "before": "Abgenutztes Büro",
                "after": "Frischer Arbeitsraum",
            },
        ),
        "team": (
            ("Tom Berger", "Meister", "Leitung & Qualitätskontrolle"),
            ("Mira Schulz", "Monteurin", "Küche & Möbel"),
            ("Jonas Krämer", "Maler", "Anstrich & Tapezieren"),
            ("Lea Vogt", "Disposition", "Termine & WhatsApp"),
        ),
        "equipment": (
            "VW Caddy mit Firmenlogo (Demo)",
            "Bosch / Makita Akkuschrauber",
            "Milwaukee Bohrhammer",
            "Laser-Wasserwaage",
            "Professionelle Abdecksysteme",
        ),
        "process": (
            "Anfrage",
            "Kurz-Check / Fotos",
            "Festpreis",
            "Termin",
            "Durchführung",
            "Fotodoku",
            "Übergabe",
        ),
        "ba_pairs": (
            ("Altes Bad", "Frisch saniert"),
            ("Kartons Küche", "Montierte Küche"),
            ("Vergilbte Wand", "Neuer Anstrich"),
        ),
        "knowledge": (
            (
                "Was kostet ein Meister pro Stunde?",
                "Transparent nach Aufwand — oft Festpreis nach Aufmaß statt "
                "offener Stundenrechnung.",
            ),
            (
                "IKEA-Montage selbst oder Profi?",
                "Bei großen Küchen spart der Profi Zeit und Nacharbeit — "
                "wir dokumentieren die Übergabe.",
            ),
            (
                "Wie schnell kommen Sie?",
                "Viele Einsätze in Berlin innerhalb von 24–48 Stunden — "
                "je nach Auftragslage.",
            ),
        ),
        "trust": (
            ("Haftpflicht", "Betriebshaftpflicht — Demo-Hinweis"),
            ("Festpreis", "Schriftlich vor Start"),
            ("Fotodoku", "Vorher/Nachher zu jedem Auftrag"),
            ("Sauberkeit", "Abdeckung & Endreinigung"),
            ("WhatsApp", "Koordination ohne Warteschleife"),
            ("Lokal", "Berlin und Umland"),
        ),
        "timeline": (
            ("2019", "Gründung", "Start als Meister-Service auf Abruf"),
            ("2021", "Team wächst", "Montage + Maler (Demo)"),
            ("2024", "Fokus Berlin", "Stundenweise + Festpreis-Projekte"),
            ("2026", "Digitaler Auftritt", "Website mit Projektreferenzen"),
        ),
        "gallery_roles": (
            "Badrenovierung",
            "Küchenmontage",
            "Anstrich",
            "Boden & Übergabe",
        ),
    },
    "dachreinigung": {
        "cases": (
            {
                "title": "Haus in Nürnberg-Nord",
                "city": "Nürnberg",
                "task": "Stark vermooste Dachfläche, abflussschwache Rinne",
                "duration": "1 Arbeitstag",
                "works": ("Dachreinigung", "Moosentfernung", "Dachrinne", "Fotodoku"),
                "before": "Moos & Ablagerungen",
                "after": "Klare Dachfläche",
            },
            {
                "title": "Familienhaus in Fürth",
                "city": "Fürth",
                "task": "Pflege + Imprägnierung nach Regenperiode",
                "duration": "1–2 Tage",
                "works": ("Reinigung", "Imprägnierung", "Inspektion"),
                "before": "Stumpfe Oberfläche",
                "after": "Geschützte Fläche",
            },
            {
                "title": "Villa in Erlangen",
                "city": "Erlangen",
                "task": "Großfläche mit Höhenarbeit und Dokumentation",
                "duration": "2 Arbeitstage",
                "works": ("Inspektion", "Reinigung", "Sicherungsplanung", "Bericht"),
                "before": "Ungleichmäßige Patina",
                "after": "Einheitliches Ergebnis",
            },
            {
                "title": "Townhouse in Schwabach",
                "city": "Schwabach",
                "task": "Reihenhaus — enge Zufahrt, präzise Terminplanung",
                "duration": "1 Arbeitstag",
                "works": ("Dachreinigung", "Rinne", "Nachbarabstimmung"),
                "before": "Verstopfte Rinne",
                "after": "Freier Ablauf",
            },
        ),
        "team": (
            ("Jonas Weber", "Gründer", "Leitung & Qualitätskontrolle"),
            ("Anna Becker", "Dachreinigung", "Reinigung & Imprägnierung"),
            ("Lukas Hoffmann", "Höhenarbeiten", "Sicherung & Arbeitsbühne"),
            ("Michael Koch", "Kundenservice", "Termine & Festpreis-Angebote"),
        ),
        "equipment": (
            "Mercedes Sprinter",
            "Kärcher Professional",
            "Sicherheitsgurte / Auffangsysteme",
            "DJI Drohne (Inspektion)",
            "Arbeitsbühne",
        ),
        "process": (
            "Anfrage",
            "Vor-Ort Besichtigung",
            "Festpreis Angebot",
            "Termin",
            "Durchführung",
            "Fotodokumentation",
            "Garantie",
        ),
        "ba_pairs": (
            ("Moosbedecktes Dach", "Frisch gereinigte Fläche"),
            ("Verstopfte Dachrinne", "Freier Wasserablauf"),
            ("Matte Ziegel", "Gepflegte Optik"),
        ),
        "knowledge": (
            (
                "Wann sollte ein Dach gereinigt werden?",
                "Meist nach starker Moosbildung oder vor der Imprägnierung — "
                "nicht erst wenn Schäden sichtbar sind.",
            ),
            (
                "Moos entfernen oder nicht?",
                "Moos hält Feuchtigkeit. Entfernung schützt die Substanz — "
                "richtig ausgeführt und dokumentiert.",
            ),
            (
                "Wie lange hält eine Imprägnierung?",
                "Je nach Lage und Witterung typischerweise mehrere Jahre — "
                "wir erklären die Pflegeintervalle transparent.",
            ),
            (
                "Dachrinne selbst reinigen?",
                "Bei erreichbaren Höhen möglich. Ab steilen Dächern empfehlen "
                "wir professionelle Sicherung.",
            ),
        ),
        "trust": (
            ("Versicherung", "Betriebshaftpflicht — Demo-Hinweis"),
            ("Sicherheitsstandards", "Höhenarbeit mit Sicherung — Demo"),
            ("Dokumentation", "Vorher/Nachher-Fotos zu jedem Auftrag"),
            ("Festpreis", "Klarer Preis vor dem Termin"),
            ("Garantie", "Nacharbeitsfenster nach Leistung (Demo)"),
            ("Lokaler Service", "Nürnberg und Region — Ansprechpartner vor Ort"),
        ),
        "timeline": (
            ("2022", "Unternehmen gegründet", "Start als lokales Dachpflege-Team"),
            ("2023", "100 Aufträge (Demo)", "Erste feste Routinen & Dokumentation"),
            ("2024", "Imprägnierung als Service", "Erweiterung des Leistungsportfolios"),
            ("2025", "Team erweitert", "Höhenarbeit & Kundenservice ausgebaut"),
            ("2026", "Region Nürnberg", "Einsatzgebiet über die Stadtgrenze hinaus"),
        ),
        "gallery_roles": (
            "Arbeit auf dem Dach",
            "Reinigung",
            "Imprägnierung",
            "Inspektion",
            "Drohne",
        ),
    },
    "zaunbau": {
        "cases": (
            {
                "title": "Grundstück Erlangen",
                "city": "Erlangen",
                "task": "Metallzaun mit Tor und klarer Linie",
                "duration": "3 Tage",
                "works": ("Vermessung", "Pfosten", "Tor", "Abnahme"),
                "before": "Offene Grenze",
                "after": "Klarer Zaun",
            },
            {
                "title": "Garten Nürnberg",
                "city": "Nürnberg",
                "task": "Holzlattenzaun — Sichtschutz",
                "duration": "2 Tage",
                "works": ("Materialwahl", "Montage", "Tor"),
                "before": "Unebene Grenze",
                "after": "Saubere Lattenlinie",
            },
        ),
        "team": (
            ("Markus Klein", "Gründer", "Montageleitung"),
            ("Sara Vogel", "Planung", "Aufmaß & Angebot"),
            ("Tim Braun", "Montage", "Tore & Pfosten"),
            ("Nina Hart", "Kundenservice", "Termine"),
        ),
        "equipment": ("Transporter", "Anhänger", "Schweißgerät", "Schraubtechnik"),
        "process": (
            "Anfrage",
            "Aufmaß vor Ort",
            "Festpreis Angebot",
            "Termin",
            "Montage",
            "Abnahme",
            "Garantie",
        ),
        "ba_pairs": (("Offene Grenze", "Fertiger Zaun"), ("Altes Tor", "Neues Tor")),
        "knowledge": (
            ("Welcher Zaun hält länger?", "Material und Untergrund entscheiden."),
            ("Brauche ich eine Genehmigung?", "Je nach Höhe und Lage — wir klären das."),
        ),
        "trust": (
            ("Versicherung", "Demo"),
            ("Festpreis", "Vor Montage"),
            ("Lokaler Service", "Metropolregion Nürnberg"),
            ("Dokumentation", "Abnahmeprotokoll (Demo)"),
        ),
        "timeline": (
            ("2019", "Gegründet", "Erste Montagen"),
            ("2022", "Werkstatt erweitert", "Demo"),
            ("2026", "Region aktiv", "Demo"),
        ),
        "gallery_roles": ("Pfosten", "Tor", "Werkstatt", "Montage"),
    },
    "gartenpflege": {
        "cases": (
            {
                "title": "Villengarten Erlangen",
                "city": "Erlangen",
                "task": "Hecke + Rasen in Form bringen",
                "duration": "1 Tag",
                "works": ("Heckenschnitt", "Rasenpflege", "Abfuhr"),
                "before": "Überwachsene Hecke",
                "after": "Klare Linie",
            },
            {
                "title": "Reihenhausgarten Fürth",
                "city": "Fürth",
                "task": "Beete und Saisonschnitt",
                "duration": "Halber Tag",
                "works": ("Beete", "Schnitt", "Laub"),
                "before": "Unruhige Beete",
                "after": "Gepflegte Struktur",
            },
        ),
        "team": (
            ("Elena Roth", "Gründerin", "Gartenplanung"),
            ("Tom Berger", "Schnitt", "Hecken & Bäume"),
            ("Mia Lang", "Pflege", "Rasen & Beete"),
            ("Paul Stein", "Kundenservice", "Jahrespläne"),
        ),
        "equipment": ("Kleiner Transporter", "Geräteanhänger", "Profi-Schnittgeräte"),
        "process": (
            "Anfrage",
            "Gartenbegehung",
            "Pflegeplan",
            "Termin",
            "Durchführung",
            "Fotodoku",
            "Saisonpflege",
        ),
        "ba_pairs": (("Überwachsene Hecke", "Klare Linie"), ("Wilder Rasen", "Gepflegter Rasen")),
        "knowledge": (
            ("Wann Hecke schneiden?", "Außerhalb der Brutzeiten — wir planen mit."),
            ("Rasenpflege im Herbst?", "Laub und Schnitt entscheiden über den Frühling."),
        ),
        "trust": (
            ("Lokaler Service", "Nürnberg und Umland"),
            ("Festpreis", "Pro Termin klar"),
            ("Dokumentation", "Vorher/Nachher (Demo)"),
            ("Jahresplan", "Demo"),
        ),
        "timeline": (
            ("2018", "Gegründet", "Erste Gärten"),
            ("2023", "Jahresverträge", "Demo"),
            ("2026", "Region aktiv", "Demo"),
        ),
        "gallery_roles": ("Hecke", "Rasen", "Beete", "Werkzeug"),
    },
}


def niche_wants_reputation(niche_id: str) -> bool:
    """Reputation Pack ships for every site — demo-labeled proof is the product."""
    return bool((niche_id or "generic").strip())


def inject_reputation_into_order(order: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Place reputation after services (proof after offer)."""
    keys = [k for k in order if k]
    if "reputation" in keys:
        return tuple(keys)
    if "services" in keys:
        i = keys.index("services") + 1
        keys.insert(i, "reputation")
    elif "process" in keys:
        i = keys.index("process") + 1
        keys.insert(i, "reputation")
    else:
        keys.insert(min(2, len(keys)), "reputation")
    return tuple(keys)


def build_reputation_pack(book: BrandBook) -> ReputationPack:
    niche = book.niche_id
    raw = _NICHE_REP.get(niche)
    if not raw:
        raw = {
            "cases": (
                {
                    "title": f"Projekt {book.city_hint or 'Lokal'}",
                    "city": book.city_hint or "DE",
                    "task": "Demonstrative Referenzarbeit",
                    "duration": "1–2 Tage",
                    "works": ("Beratung", "Umsetzung", "Dokumentation"),
                    "before": "Ausgangslage",
                    "after": "Ergebnis",
                },
            ),
            "team": (
                ("Alex Müller", "Leitung", "Qualität"),
                ("Sam Keller", "Fachkraft", "Umsetzung"),
                ("Lea Hoffmann", "Service", "Kundenkontakt"),
                ("Chris Berg", "Organisation", "Termine"),
            ),
            "equipment": ("Einsatzfahrzeug", "Fachwerkzeug", "Dokumentation"),
            "process": (
                "Anfrage",
                "Beratung",
                "Angebot",
                "Termin",
                "Durchführung",
                "Dokumentation",
                "Nachsorge",
            ),
            "ba_pairs": (("Vorher", "Nachher"),),
            "knowledge": (
                ("Worauf Sie achten sollten", "Kurzer Demo-Fachartikel zur Orientierung."),
                ("Ablauf verständlich erklärt", "So arbeiten wir — transparent und lokal."),
            ),
            "trust": (
                ("Versicherung", "Demo"),
                ("Dokumentation", "Demo"),
                ("Festpreis", "Demo"),
                ("Lokaler Service", "Demo"),
            ),
            "timeline": (
                ("2022", "Start", "Demo"),
                ("2024", "Wachstum", "Demo"),
                ("2026", "Region", "Demo"),
            ),
            "gallery_roles": tuple(book.media_dna.required[:4])
            if getattr(book, "media_dna", None)
            else ("Arbeit", "Ergebnis"),
        }

    cases = tuple(
        DemoCase(
            title=c["title"],
            city=c["city"],
            task=c["task"],
            duration=c["duration"],
            works=tuple(c["works"]),
            before_label=c.get("before", "Vorher"),
            after_label=c.get("after", "Nachher"),
        )
        for c in raw["cases"]
    )
    team = tuple(
        DemoPerson(name=n, role=r, focus=f) for n, r, f in raw["team"]
    )
    knowledge = tuple(
        KnowledgeArticle(title=t, teaser=s) for t, s in raw["knowledge"]
    )
    trust = tuple(TrustPillar(title=t, detail=d) for t, d in raw["trust"])
    timeline = tuple(
        TimelineEvent(year=y, title=t, detail=d) for y, t, d in raw["timeline"]
    )
    ba = tuple((a, b) for a, b in raw["ba_pairs"])
    fp = hashlib.sha256(
        f"{book.fingerprint}|reputation|v2|{niche}".encode()
    ).hexdigest()[:24]
    return ReputationPack(
        brand_name=book.brand_name,
        niche_id=niche,
        package_id=book.package_id,
        cases=cases,
        team=team,
        equipment=tuple(raw["equipment"]),
        process=tuple(raw["process"]),
        before_after_pairs=ba,
        knowledge=knowledge,
        trust=trust,
        timeline=timeline,
        gallery_roles=tuple(
            raw.get("gallery_roles")
            or (
                tuple(book.media_dna.required[:4])
                if getattr(book, "media_dna", None)
                else ("Arbeit", "Detail", "Ergebnis", "Team")
            )
        ),
        media_truth_rule=(
            "No media ships without profession + brand + story proof. "
            "Beauty alone is REBUILD."
        ),
        fingerprint=fp,
    )


def reputation_pack_css() -> str:
    return """
/* ——— Reputation Pack ——— */
.reputation-pack { position: relative; }
.reputation-pack .rep-demo-banner {
  display: inline-block;
  margin: 0 0 1.25rem;
  padding: .35rem .75rem;
  font-size: .72rem;
  letter-spacing: .04em;
  text-transform: uppercase;
  border: 1px solid color-mix(in srgb, currentColor 28%, transparent);
  border-radius: 2px;
  opacity: .85;
}
.reputation-pack .rep-block { margin: 2.5rem 0 0; }
.reputation-pack .rep-block:first-of-type { margin-top: 1rem; }
.reputation-pack .rep-kicker {
  font-size: .75rem;
  letter-spacing: .12em;
  text-transform: uppercase;
  opacity: .7;
  margin: 0 0 .35rem;
}
.reputation-pack .rep-block h3 {
  margin: 0 0 1rem;
  font-size: clamp(1.35rem, 2.4vw, 1.85rem);
  font-weight: 600;
}
.rep-case-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 1.1rem;
}
.rep-case {
  border: 1px solid color-mix(in srgb, currentColor 16%, transparent);
  padding: 0;
  overflow: hidden;
  background: color-mix(in srgb, #0b1220 55%, transparent);
}
.rep-case-ba {
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 110px;
}
.rep-case-ba .ba-side {
  display: flex;
  align-items: flex-end;
  padding: .65rem;
  font-size: .7rem;
  letter-spacing: .06em;
  text-transform: uppercase;
  min-height: 110px;
  background-size: cover;
  background-position: center;
}
.rep-case-ba .ba-before {
  background-color: #1c2420;
  background-image: linear-gradient(160deg, rgba(58,69,56,.55), rgba(28,36,32,.75));
  color: #d7e0d4;
}
.rep-case-ba .ba-after {
  background-color: #2a3a48;
  background-image: linear-gradient(160deg, rgba(106,138,154,.45), rgba(42,58,72,.7));
  color: #e8f0f4;
}
.rep-case-body { padding: 1rem 1.05rem 1.15rem; }
.rep-case-body h4 { margin: 0 0 .35rem; font-size: 1.05rem; }
.rep-case-body .rep-meta { font-size: .82rem; opacity: .75; margin: 0 0 .55rem; }
.rep-case-body ul { margin: .4rem 0 0; padding: 0 0 0 1rem; font-size: .86rem; }
.rep-demo-chip {
  display: inline-block;
  font-size: .65rem;
  letter-spacing: .05em;
  text-transform: uppercase;
  opacity: .65;
  margin-bottom: .4rem;
}
.rep-team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 1rem;
}
.rep-person {
  text-align: center;
  padding: 1rem .75rem;
  border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
}
.rep-avatar {
  width: 72px; height: 72px;
  margin: 0 auto .75rem;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  background:
    radial-gradient(circle at 35% 30%, color-mix(in srgb, var(--accent, #7a9aab) 55%, #fff), transparent 55%),
    linear-gradient(145deg, #2a3540, #1a222a);
  border: 2px solid color-mix(in srgb, currentColor 20%, transparent);
}
.rep-person h4 { margin: 0; font-size: .98rem; }
.rep-person .role { margin: .2rem 0 0; font-size: .8rem; opacity: .75; }
.rep-person .focus { margin: .35rem 0 0; font-size: .75rem; opacity: .6; }
.rep-equip {
  display: flex;
  flex-wrap: wrap;
  gap: .55rem;
}
.rep-equip span {
  padding: .45rem .8rem;
  border: 1px solid color-mix(in srgb, currentColor 20%, transparent);
  font-size: .85rem;
  background: color-mix(in srgb, #0b1220 40%, transparent);
}
.rep-process-flow {
  display: flex;
  flex-direction: column;
  gap: 0;
  max-width: 28rem;
}
.rep-process-step {
  display: grid;
  grid-template-columns: 2rem 1fr;
  gap: .75rem;
  align-items: start;
  padding: .55rem 0;
}
.rep-process-step .dot {
  width: 1.35rem; height: 1.35rem;
  border-radius: 50%;
  border: 2px solid color-mix(in srgb, var(--accent, #7a9aab) 80%, #fff);
  display: flex; align-items: center; justify-content: center;
  font-size: .65rem;
  margin-top: .1rem;
}
.rep-process-arrow {
  padding: 0 0 0 2.75rem;
  font-size: .85rem;
  opacity: .45;
  line-height: 1;
}
.rep-ba-stage { margin-top: .5rem; }
.rep-ba-tabs {
  display: flex; flex-wrap: wrap; gap: .4rem; margin-bottom: .85rem;
}
.rep-ba-tabs button {
  appearance: none;
  border: 1px solid color-mix(in srgb, currentColor 22%, transparent);
  background: transparent;
  color: inherit;
  padding: .4rem .7rem;
  font: inherit;
  font-size: .8rem;
  cursor: pointer;
  opacity: .7;
}
.rep-ba-tabs button[aria-selected="true"] {
  opacity: 1;
  border-color: color-mix(in srgb, var(--accent, #7a9aab) 70%, currentColor);
}
.rep-ba-slider {
  position: relative;
  height: min(42vw, 320px);
  min-height: 200px;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, currentColor 16%, transparent);
  user-select: none;
  touch-action: none;
}
.rep-ba-slider .layer {
  position: absolute; inset: 0;
  display: flex; align-items: flex-end; padding: 1rem;
  font-size: .75rem; letter-spacing: .08em; text-transform: uppercase;
  background-size: cover;
  background-position: center;
}
.rep-ba-slider .layer-before {
  background-color: #1a221c;
  background-image: linear-gradient(145deg, rgba(61,74,60,.5), rgba(26,34,28,.65));
  clip-path: inset(0 50% 0 0);
  z-index: 2;
}
.rep-ba-slider .layer-after {
  background-color: #243440;
  background-image: linear-gradient(145deg, rgba(107,143,160,.45), rgba(36,52,64,.6));
  z-index: 1;
}
.rep-ba-slider .layer .ba-label {
  padding: .35rem .55rem;
  background: rgba(0,0,0,.45);
  border-radius: 2px;
}
.rep-ba-slider .handle {
  position: absolute; top: 0; bottom: 0; left: 50%;
  width: 3px;
  background: #fff;
  z-index: 3;
  transform: translateX(-50%);
  box-shadow: 0 0 0 1px rgba(0,0,0,.25);
}
.rep-ba-slider .handle::after {
  content: "";
  position: absolute;
  top: 50%; left: 50%;
  width: 28px; height: 28px;
  margin: -14px 0 0 -14px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,.35);
}
.rep-know-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}
.rep-know {
  padding: 1.1rem;
  border-left: 3px solid color-mix(in srgb, var(--accent, #7a9aab) 70%, transparent);
  background: color-mix(in srgb, #0b1220 35%, transparent);
}
.rep-know h4 { margin: 0 0 .45rem; font-size: 1rem; }
.rep-know p { margin: 0; font-size: .88rem; opacity: .82; line-height: 1.45; }
.rep-trust-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: .85rem;
}
.rep-trust {
  padding: 1rem;
  border: 1px solid color-mix(in srgb, currentColor 14%, transparent);
}
.rep-trust h4 { margin: 0 0 .35rem; font-size: .95rem; }
.rep-trust p { margin: 0; font-size: .82rem; opacity: .78; }
.rep-timeline {
  display: grid;
  gap: 0;
  border-left: 2px solid color-mix(in srgb, var(--accent, #7a9aab) 55%, transparent);
  padding-left: 1.25rem;
  margin-left: .4rem;
}
.rep-tl-item {
  position: relative;
  padding: 0 0 1.35rem;
}
.rep-tl-item::before {
  content: "";
  position: absolute;
  left: -1.55rem; top: .35rem;
  width: .65rem; height: .65rem;
  border-radius: 50%;
  background: var(--accent, #7a9aab);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--accent, #7a9aab) 25%, transparent);
}
.rep-tl-item .year {
  font-size: .75rem;
  letter-spacing: .1em;
  text-transform: uppercase;
  opacity: .65;
}
.rep-tl-item h4 { margin: .15rem 0 .25rem; font-size: 1.05rem; }
.rep-tl-item p { margin: 0; font-size: .86rem; opacity: .78; }
@media (max-width: 640px) {
  .rep-ba-slider { height: 220px; }
}
"""


def reputation_pack_js() -> str:
    return """
<script>
(function () {
  var root = document.getElementById('reputation');
  if (!root) return;
  var stage = root.querySelector('.rep-ba-slider');
  var tabs = root.querySelectorAll('.rep-ba-tabs button');
  var pairs = [];
  try {
    pairs = JSON.parse(root.getAttribute('data-ba-pairs') || '[]');
  } catch (e) { pairs = []; }
  function setPair(i) {
    if (!stage || !pairs.length) return;
    var p = pairs[Math.max(0, Math.min(i, pairs.length - 1))];
    var before = stage.querySelector('.layer-before');
    var after = stage.querySelector('.layer-after');
    var bLabel = (p && p[0]) || 'Vorher';
    var aLabel = (p && p[1]) || 'Nachher';
    var bImg = (p && p[2]) || '';
    var aImg = (p && p[3]) || '';
    if (before) {
      var bl = before.querySelector('.ba-label');
      if (bl) bl.textContent = bLabel;
      if (bImg) before.style.backgroundImage = 'url(\"' + bImg + '\")';
    }
    if (after) {
      var al = after.querySelector('.ba-label');
      if (al) al.textContent = aLabel;
      if (aImg) after.style.backgroundImage = 'url(\"' + aImg + '\")';
    }
    tabs.forEach(function (btn, idx) {
      btn.setAttribute('aria-selected', idx === i ? 'true' : 'false');
    });
  }
  tabs.forEach(function (btn, idx) {
    btn.addEventListener('click', function () { setPair(idx); });
  });
  if (tabs.length) setPair(0);
  function setSplit(clientX) {
    if (!stage) return;
    var rect = stage.getBoundingClientRect();
    var x = Math.max(0.08, Math.min(0.92, (clientX - rect.left) / rect.width));
    var pct = (x * 100).toFixed(2) + '%';
    var before = stage.querySelector('.layer-before');
    var handle = stage.querySelector('.handle');
    if (before) before.style.clipPath = 'inset(0 ' + (100 - x * 100).toFixed(2) + '% 0 0)';
    if (handle) handle.style.left = pct;
  }
  if (stage) {
    var dragging = false;
    stage.addEventListener('pointerdown', function (e) {
      dragging = true;
      stage.setPointerCapture(e.pointerId);
      setSplit(e.clientX);
    });
    stage.addEventListener('pointermove', function (e) {
      if (!dragging) return;
      setSplit(e.clientX);
    });
    stage.addEventListener('pointerup', function () { dragging = false; });
    stage.addEventListener('pointercancel', function () { dragging = false; });
  }
})();
</script>
"""


def materialize_reputation_media(
    product_dir: Path,
    pack: ReputationPack,
    *,
    book: BrandBook | None = None,
) -> dict[str, str]:
    """Write real demo JPEG pairs under assets/reputation/. Never leave empty slots."""
    from app.factory.niche_scene_media import write_niche_scene

    assets = product_dir / "assets" / "reputation"
    assets.mkdir(parents=True, exist_ok=True)
    metaphor = (book.visual_metaphor if book else "") or ""
    accent = book.palette.accent_hex if book and book.palette else None
    written: dict[str, str] = {}

    for i, case in enumerate(pack.cases):
        before = assets / f"case_{i}_before.jpg"
        after = assets / f"case_{i}_after.jpg"
        write_niche_scene(
            before,
            niche_id=pack.niche_id,
            seed=f"rep|before|{pack.fingerprint}|{i}|{case.title}",
            role="gallery",
            size=(800, 520),
            metaphor=f"{metaphor} before moss dirty {case.before_label}",
            accent_hex=accent,
            label="Vorher · Demo",
        )
        write_niche_scene(
            after,
            niche_id=pack.niche_id,
            seed=f"rep|after|{pack.fingerprint}|{i}|{case.title}",
            role="gallery",
            size=(800, 520),
            metaphor=f"{metaphor} after clean rain {case.after_label}",
            accent_hex=accent,
            label="Nachher · Demo",
        )
        written[f"case_{i}_before"] = f"assets/reputation/case_{i}_before.jpg"
        written[f"case_{i}_after"] = f"assets/reputation/case_{i}_after.jpg"

    for i, (b_lab, a_lab) in enumerate(pack.before_after_pairs):
        # Reuse case images when available (same visual story)
        if i < len(pack.cases):
            written[f"ba_{i}_before"] = written[f"case_{i}_before"]
            written[f"ba_{i}_after"] = written[f"case_{i}_after"]
            continue
        before = assets / f"ba_{i}_before.jpg"
        after = assets / f"ba_{i}_after.jpg"
        write_niche_scene(
            before,
            niche_id=pack.niche_id,
            seed=f"rep|ba|before|{pack.fingerprint}|{i}",
            role="banner",
            size=(1200, 680),
            metaphor=f"{metaphor} before {b_lab}",
            accent_hex=accent,
            label="Vorher · Demo",
        )
        write_niche_scene(
            after,
            niche_id=pack.niche_id,
            seed=f"rep|ba|after|{pack.fingerprint}|{i}",
            role="banner",
            size=(1200, 680),
            metaphor=f"{metaphor} after {a_lab}",
            accent_hex=accent,
            label="Nachher · Demo",
        )
        written[f"ba_{i}_before"] = f"assets/reputation/ba_{i}_before.jpg"
        written[f"ba_{i}_after"] = f"assets/reputation/ba_{i}_after.jpg"

    # Team avatars as small niche stills (demo, not stock faces)
    for i, person in enumerate(pack.team):
        dest = assets / f"team_{i}.jpg"
        write_niche_scene(
            dest,
            niche_id=pack.niche_id,
            seed=f"rep|team|{pack.fingerprint}|{i}|{person.name}",
            role="product",
            size=(320, 320),
            metaphor=metaphor,
            accent_hex=accent,
            label=person.role[:24],
        )
        written[f"team_{i}"] = f"assets/reputation/team_{i}.jpg"

    (assets / "manifest.json").write_text(
        json.dumps({"files": written, "demo": True}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return written


def render_reputation_html(
    pack: ReputationPack,
    *,
    section_class: str = "section",
    media: dict[str, str] | None = None,
) -> str:
    """Full Reputation Pack as one landing section (7 blocks + timeline)."""
    media = media or {}
    ba_payload = []
    for i, (b_lab, a_lab) in enumerate(pack.before_after_pairs):
        ba_payload.append(
            [
                b_lab,
                a_lab,
                media.get(f"ba_{i}_before")
                or media.get(f"case_{i}_before")
                or "",
                media.get(f"ba_{i}_after")
                or media.get(f"case_{i}_after")
                or "",
            ]
        )
    ba_json = _esc(json.dumps(ba_payload, ensure_ascii=False))

    cases_html = []
    for i, c in enumerate(pack.cases):
        works = "".join(f"<li>{_esc(w)}</li>" for w in c.works)
        b_src = media.get(f"case_{i}_before", "")
        a_src = media.get(f"case_{i}_after", "")
        b_style = f' style="background-image:url(\'{_esc(b_src)}\')"' if b_src else ""
        a_style = f' style="background-image:url(\'{_esc(a_src)}\')"' if a_src else ""
        cases_html.append(
            f"""
<article class="rep-case">
  <div class="rep-case-ba" aria-hidden="true">
    <div class="ba-side ba-before"{b_style}>{_esc(c.before_label)}</div>
    <div class="ba-side ba-after"{a_style}>{_esc(c.after_label)}</div>
  </div>
  <div class="rep-case-body">
    <span class="rep-demo-chip">{_esc(c.demo_label)}</span>
    <h4>{_esc(c.title)}</h4>
    <p class="rep-meta">{_esc(c.city)} · {_esc(c.duration)}</p>
    <p>{_esc(c.task)}</p>
    <ul>{works}</ul>
  </div>
</article>"""
        )

    team_html = []
    for i, p in enumerate(pack.team):
        hue = 200 + (i * 28) % 80
        avatar = media.get(f"team_{i}", "")
        if avatar:
            av = (
                f'<img class="rep-avatar" src="{_esc(avatar)}" alt="" '
                f'width="72" height="72" loading="lazy" '
                f'onerror="this.style.display=\'none\'">'
            )
        else:
            av = (
                f'<div class="rep-avatar" style="--accent:hsl({hue},28%,48%)" '
                f'aria-hidden="true"></div>'
            )
        team_html.append(
            f"""
<article class="rep-person">
  {av}
  <span class="rep-demo-chip">{_esc(p.demo_label)}</span>
  <h4>{_esc(p.name)}</h4>
  <p class="role">{_esc(p.role)}</p>
  <p class="focus">{_esc(p.focus)}</p>
</article>"""
        )

    equip = "".join(f"<span>{_esc(e)}</span>" for e in pack.equipment)

    process_rows = []
    for i, step in enumerate(pack.process, start=1):
        process_rows.append(
            f"""
<div class="rep-process-step">
  <div class="dot">{i}</div>
  <div><strong>{_esc(step)}</strong></div>
</div>"""
        )
        if i < len(pack.process):
            process_rows.append(
                '<div class="rep-process-arrow" aria-hidden="true">↓</div>'
            )

    ba_tabs = "".join(
        f'<button type="button" aria-selected="{"true" if i == 0 else "false"}">'
        f"{_esc(pack.cases[i].city if i < len(pack.cases) else f'Objekt {i + 1}')}"
        f"</button>"
        for i in range(len(pack.before_after_pairs))
    )
    first = ba_payload[0] if ba_payload else ["Vorher", "Nachher", "", ""]
    b0_style = (
        f' style="background-image:url(\'{_esc(first[2])}\')"' if first[2] else ""
    )
    a0_style = (
        f' style="background-image:url(\'{_esc(first[3])}\')"' if first[3] else ""
    )

    know_html = []
    for k in pack.knowledge:
        know_html.append(
            f"""
<article class="rep-know">
  <span class="rep-demo-chip">{_esc(k.demo_label)}</span>
  <h4>{_esc(k.title)}</h4>
  <p>{_esc(k.teaser)}</p>
</article>"""
        )

    trust_html = []
    for t in pack.trust:
        trust_html.append(
            f"""
<article class="rep-trust">
  <span class="rep-demo-chip">{_esc(t.demo_label)}</span>
  <h4>{_esc(t.title)}</h4>
  <p>{_esc(t.detail)}</p>
</article>"""
        )

    tl_html = []
    for e in pack.timeline:
        tl_html.append(
            f"""
<div class="rep-tl-item">
  <div class="year">{_esc(e.year)} · {_esc(e.demo_label)}</div>
  <h4>{_esc(e.title)}</h4>
  <p>{_esc(e.detail)}</p>
</div>"""
        )

    # If BA media missing entirely — hide interactive block (never broken imgs)
    ba_block = ""
    if any(p[2] and p[3] for p in ba_payload):
        ba_block = f"""
    <div class="rep-block" id="rep-before-after">
      <p class="rep-kicker">05 · Before / After</p>
      <h3>Ergebnis, das man sieht</h3>
      <div class="rep-ba-stage">
        <div class="rep-ba-tabs" role="tablist">{ba_tabs}</div>
        <div class="rep-ba-slider" role="img" aria-label="Vorher Nachher Vergleich Demo">
          <div class="layer layer-after"{a0_style}><span class="ba-label">{_esc(first[1])}</span></div>
          <div class="layer layer-before"{b0_style}><span class="ba-label">{_esc(first[0])}</span></div>
          <div class="handle" aria-hidden="true"></div>
        </div>
      </div>
    </div>"""
    else:
        ba_block = """
    <div class="rep-block" id="rep-before-after" hidden>
      <p class="rep-demo-chip">Before/After wird geladen · Demo</p>
    </div>"""

    return f"""
  <section class="{_esc(section_class)} reputation-pack" id="reputation" data-ba-pairs="{ba_json}">
    <p class="rep-demo-banner">{_esc(pack.disclaimer)}</p>
    <p class="rep-kicker">Reputation</p>
    <h2>Nachweis statt Versprechen</h2>
    <p class="muted">Warum {_esc(pack.brand_name)} wie ein reales Unternehmen wirkt — mit klarer Demo-Kennzeichnung.</p>

    <div class="rep-block" id="rep-portfolio">
      <p class="rep-kicker">01 · Portfolio</p>
      <h3>Referenzprojekte</h3>
      <div class="rep-case-grid">{"".join(cases_html)}</div>
    </div>

    <div class="rep-block" id="rep-team">
      <p class="rep-kicker">02 · Team</p>
      <h3>Menschen hinter dem Handwerk</h3>
      <div class="rep-team-grid">{"".join(team_html)}</div>
    </div>

    <div class="rep-block" id="rep-equipment">
      <p class="rep-kicker">03 · Equipment</p>
      <h3>Ausrüstung, die Vertrauen schafft</h3>
      <div class="rep-equip">{equip}</div>
    </div>

    <div class="rep-block" id="rep-process">
      <p class="rep-kicker">04 · Process</p>
      <h3>So läuft Ihr Auftrag</h3>
      <div class="rep-process-flow">{"".join(process_rows)}</div>
    </div>
{ba_block}

    <div class="rep-block" id="rep-knowledge">
      <p class="rep-kicker">06 · Knowledge</p>
      <h3>Fachwissen statt Floskeln</h3>
      <div class="rep-know-grid">{"".join(know_html)}</div>
    </div>

    <div class="rep-block" id="rep-trust">
      <p class="rep-kicker">07 · Trust</p>
      <h3>Worauf Sie sich verlassen können</h3>
      <div class="rep-trust-grid">{"".join(trust_html)}</div>
    </div>

    <div class="rep-block" id="rep-timeline">
      <p class="rep-kicker">Timeline</p>
      <h3>Entwicklung über Jahre</h3>
      <div class="rep-timeline">{"".join(tl_html)}</div>
    </div>
  </section>
"""


def write_reputation_pack(
    product_dir: Path,
    *,
    business_name: str,
    niche_id: str,
    package_id: str = "business",
    diversity_salt: str = "",
    city: str = "",
) -> ReputationPack:
    """Persist reputation_pack.json + enforce Media Truth on assets."""
    book = resolve_brand_book(
        business_name=business_name,
        niche_id=niche_id,
        package_id=package_id,
        diversity_salt=diversity_salt,
        city=city,
    )
    pack = build_reputation_pack(book)
    product_dir.mkdir(parents=True, exist_ok=True)
    media = materialize_reputation_media(product_dir, pack, book=book)
    payload = pack.as_dict()
    payload["media"] = media
    (product_dir / "reputation_pack.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    enforce_media_truth_on_product(
        product_dir,
        niche_id=niche_id,
        business_name=business_name,
        package_id=package_id,
    )
    return pack


__all__ = [
    "DEMO_DISCLAIMER",
    "DemoCase",
    "DemoPerson",
    "KnowledgeArticle",
    "ReputationPack",
    "TimelineEvent",
    "TrustPillar",
    "build_reputation_pack",
    "inject_reputation_into_order",
    "materialize_reputation_media",
    "niche_wants_reputation",
    "render_reputation_html",
    "reputation_pack_css",
    "reputation_pack_js",
    "write_reputation_pack",
]
