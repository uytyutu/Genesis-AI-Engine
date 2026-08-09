"""Business Generation — invent a believable company, not a niche template.

Commercial Owner FAIL: sites felt like one template with swapped niches.
Factory must create a company that could have existed for 5 years.

Demo reviews MUST be labeled as demonstration content.
Real client orders: only when contacts.fabricate_company / demo_gallery is set.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from app.factory.analyzer import AnalysisResult


COMMERCIAL_REVIEW_STATUS = "FAIL"
COMMERCIAL_REVIEW_NOTE = (
    "Commercial Owner FAIL — generation still reads as niche templates, "
    "not living companies. Goal: invent a ready business (name, legend, "
    "services, team, FAQ, demo-labeled reviews). "
    "Would a stranger believe this company is 5 years old? If no → FAIL."
)

DEMO_REVIEW_LABEL_DE = "Demo-Bewertung — kein echter Kundenname"
DEMO_REVIEW_LABEL_EN = "Demo review — not a real customer"


@dataclass(frozen=True)
class FabricatedCompany:
    """A complete invented business ready for site/store export."""

    legal_name: str
    brand_name: str
    slogan: str
    mission: str
    history: str
    values: tuple[str, ...]
    approach: str
    founded_year: int
    city: str
    niche_id: str
    services: tuple[tuple[str, str, str], ...]  # title, description, price_label
    advantages: tuple[str, ...]
    team: tuple[tuple[str, str, str], ...]  # name, role, blurb
    faq: tuple[tuple[str, str], ...]
    reviews: tuple[tuple[str, str], ...]  # quote, cite (demo-labeled)
    process_steps: tuple[str, ...]
    blog_titles: tuple[str, ...]
    certificates: tuple[str, ...]
    hours: str
    phone: str
    email: str
    social: tuple[str, ...]
    fingerprint: str
    demo_content: bool = True

    def about_long(self) -> str:
        team_line = "; ".join(f"{n} ({r})" for n, r, _ in self.team[:4])
        values = ", ".join(self.values[:4])
        return (
            f"{self.brand_name} wurde {self.founded_year} in {self.city} gegründet. "
            f"{self.history} "
            f"Unsere Mission: {self.mission} "
            f"Werte: {values}. "
            f"Ansatz: {self.approach} "
            f"Team: {team_line}."
        )

    def headline(self) -> str:
        return f"{self.brand_name} — {self.slogan}"

    def service_titles(self) -> list[str]:
        return [t for t, _, _ in self.services]

    def service_descriptions(self) -> tuple[str, ...]:
        return tuple(
            f"{desc} · {price}" if price else desc for _, desc, price in self.services
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Niche company name seeds (German market demos)
_NAME_PARTS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
    "restaurant": (
        ("Trattoria", "Brasserie", "Atelier", "Haus", "Küche"),
        ("Luna", "Nord", "Feuer", "Olive", "Stein"),
    ),
    "beauty": (
        ("Salon", "Studio", "Atelier", "Maison", "Raum"),
        ("Mira", "Lumen", "Vera", "Nova", "Clara"),
    ),
    "auto": (
        ("Werkstatt", "Autohaus", "Service", "Garage", "Nord"),
        ("Klar", "Präzision", "Direkt", "Meister", "Fahr"),
    ),
    "psychology": (
        ("Praxis", "Institut", "Raum", "Zentrum", "Atelier"),
        ("Klarheit", "Ruhe", "Anker", "Licht", "Hafen"),
    ),
    "dental": (
        ("Zahnarztpraxis", "Dental", "Smile", "Klinik", "Studio"),
        ("Präzision", "Nord", "Klar", "Vista", "Form"),
    ),
    "law": (
        ("Kanzlei", "Rechtsanwälte", "Bureau", "Partner"),
        ("Bergmann", "Stein", "Adler", "Hoff", "Neumann"),
    ),
    "fitness": (
        ("Studio", "Athletik", "Training", "Form"),
        ("Nord", "Pulse", "Kraft", "Focus"),
    ),
    "handwerk": (
        ("Werkstatt", "Meisterbetrieb", "Handwerk"),
        ("Holz", "Stein", "Nord", "Klar"),
    ),
    "dachreinigung": (
        ("DachKlar", "Dach", "First", "Firstklar"),
        ("Service", "Profi", "Nord", "Werk"),
    ),
    "zaunbau": (
        ("ZaunWerk", "Zaun", "Sicht", "Tor"),
        ("Süd", "Nord", "Werk", "Bau"),
    ),
    "gartenpflege": (
        ("Grünzeit", "Garten", "Grün", "Ernte"),
        ("Pflege", "Zeit", "Nord", "Hof"),
    ),
    "fashion": (
        ("Atelier", "Maison", "Label", "Haus"),
        ("Noir", "Linen", "Form", "Aura"),
    ),
    "electronics": (
        ("Tech", "Signal", "Circuit", "Nova"),
        ("Lab", "Store", "Haus", "Point"),
    ),
    "furniture": (
        ("Wohn", "Raum", "Atelier", "Haus"),
        ("Eiche", "Linen", "Form", "Nord"),
    ),
    "food": (
        ("FeinKost", "Markt", "Delikatessen", "Küche"),
        ("Berlin", "Nord", "Heim", "Ernte"),
    ),
    "accessories": (
        ("Zeitstück", "Atelier", "Maison", "Form"),
        ("Gold", "Noir", "Line", "Aura"),
    ),
    "generic": (
        ("Studio", "Haus", "Atelier", "Nord"),
        ("Klar", "Form", "Licht", "Anker"),
    ),
}

_SERVICES: dict[str, tuple[tuple[str, str, str], ...]] = {
    "restaurant": (
        ("Mittagstisch", "Saisonaler Mittag mit klarer Karte", "ab 14 €"),
        ("Abendkarte", "Abendmenü mit Weinbegleitung", "ab 38 €"),
        ("Wochenkarte", "Frisch geplant — jeden Montag neu", "ab 18 €"),
        ("Reservierung", "Tischreservierung mit Bestätigung", "kostenlos"),
        ("Events", "Private Tische & Firmenessen", "auf Anfrage"),
        ("Weinprobe", "Kuratiertes Flight mit Sommelier", "ab 45 €"),
        ("Catering", "Büro & Feiern — gleiche Küche", "ab 22 €/Pers."),
        ("Brunch", "Sonntagsbrunch mit Live-Atmosphäre", "ab 29 €"),
        ("Allergene klar", "Transparente Allergen-Info an jedem Gericht", "inkl."),
        ("Take-away", "Ausgewählte Gerichte zum Mitnehmen", "ab 12 €"),
    ),
    "beauty": (
        ("Balayage", "Natürlich verlaufende Coloration", "ab 145 €"),
        ("Damenhaarschnitt", "Schnitt mit Beratung & Finish", "ab 58 €"),
        ("Pflegebehandlung", "Intensive Kur für strapaziertes Haar", "ab 42 €"),
        ("Styling", "Event- & Alltag-Styling", "ab 35 €"),
        ("Herrenschnitt", "Präziser Schnitt mit Kontur", "ab 32 €"),
        ("Glossing", "Glanz ohne harte Chemie", "ab 48 €"),
        ("Olaplex-Kur", "Reparatur für blondiertes Haar", "ab 55 €"),
        ("Brautstyling", "Probe + Hochzeitstag", "ab 180 €"),
        ("Augenbrauen", "Form & Farbe", "ab 28 €"),
        ("Beratung", "Farb- & Formberatung ohne Termin-Druck", "kostenlos"),
    ),
    "auto": (
        ("Diagnose", "Fehlerdiagnose mit Festpreis-Angebot", "ab 79 €"),
        ("Inspektion", "Herstellernahe Inspektion", "ab 189 €"),
        ("Ölwechsel", "inkl. Filter & Entsorgung", "ab 89 €"),
        ("Reifenwechsel", "Einlagerung möglich", "ab 49 €"),
        ("Bremsen", "Beläge & Scheiben mit Garantie", "ab 129 €"),
        ("Klimaservice", "Prüfung & Befüllung", "ab 99 €"),
        ("HU/AU Vorbereitung", "Check vor der Prüfung", "ab 69 €"),
        ("Batterie", "Test & Tausch", "ab 119 €"),
        ("Unfallreparatur", "Karosserie & Lack", "auf Anfrage"),
        ("Shuttle", "Abholung im Stadtgebiet", "inkl. bei Auftrag"),
    ),
    "psychology": (
        ("Erstgespräch", "45 Min. Kennenlernen & Orientierung", "95 €"),
        ("Einzeltherapie", "Wöchentliche Sitzung", "110 €"),
        ("Online-Beratung", "Verschlüsselte Videositzung", "100 €"),
        ("Paartherapie", "Gemeinsame Sitzung", "140 €"),
        ("Burnout-Prävention", "Strukturiertes 6-Wochen-Programm", "ab 480 €"),
        ("Coaching", "Berufliche Klarheit", "120 €"),
        ("Krisenintervention", "Kurzfristige Termine", "auf Anfrage"),
        ("Gruppenangebot", "Kleine Gruppe, geschützter Rahmen", "ab 45 €"),
        ("Supervision", "Für Fachkräfte", "130 €"),
        ("Elternberatung", "Familiäre Konflikte", "115 €"),
    ),
    "dental": (
        ("Prophylaxe", "Professionelle Zahnreinigung", "ab 89 €"),
        ("Füllungen", "Zahnfarbene Composite-Füllungen", "ab 75 €"),
        ("Implantate", "Beratung & Planung", "ab 1.200 €"),
        ("Bleaching", "Schonende Aufhellung", "ab 299 €"),
        ("Invisalign", "Unsichtbare Zahnkorrektur", "auf Anfrage"),
        ("Wurzelbehandlung", "Moderne Endodontie", "ab 350 €"),
        ("Parodontitis", "Therapie & Nachsorge", "ab 180 €"),
        ("Kinderzahnheilkunde", "Ruhige Behandlung für Kinder", "ab 55 €"),
        ("Notdienst", "Schmerzbehandlung", "auf Anfrage"),
        ("Ästhetik", "Veneers & Formkorrektur", "auf Anfrage"),
    ),
    "law": (
        ("Erstberatung", "60 Min. mit schriftlicher Einschätzung", "190 €"),
        ("Vertragsprüfung", "AGB, Miet- & Kaufverträge", "ab 250 €"),
        ("Gesellschaftsrecht", "Gründung & Gesellschafter", "auf Anfrage"),
        ("Arbeitsrecht", "Abmahnung, Kündigung, Vertrag", "ab 280 €"),
        ("Vertretung", "Außergerichtlich & vor Gericht", "nach RVG"),
        ("Verhandlungen", "Vergleich & Mediation", "ab 220 €/Std."),
        ("Markenrecht", "Anmeldung & Abwehr", "auf Anfrage"),
        ("Datenschutz", "DSGVO-Check für KMU", "ab 490 €"),
        ("Mahnwesen", "Forderungseinzug", "ab 120 €"),
        ("Compliance", "Interne Richtlinien", "auf Anfrage"),
    ),
    "dachreinigung": (
        ("Dachreinigung", "Schonende Reinigung der Dachfläche", "ab 890 €"),
        ("Moosentfernung", "Moos & Algen ohne Ziegelschäden", "ab 490 €"),
        ("Fassadenwäsche", "Fassade und Sockel säubern", "ab 650 €"),
        ("Dachrinne reinigen", "Laub & Ablagerungen entfernen", "ab 180 €"),
        ("Imprägnierung", "Schutz gegen schnellen Wiederbewuchs", "ab 420 €"),
        ("Dachinspektion", "Zustandscheck mit Fotodoku", "ab 120 €"),
        ("Notdienst Rinne", "Verstopfte Abläufe", "auf Anfrage"),
        ("Jahreswartung", "Jährlicher Pflegevertrag", "ab 390 €/Jahr"),
        ("Vorher/Nachher", "Fotodokumentation inkl.", "inkl."),
        ("Sicherheitscheck", "Begehung mit Sicherung", "inkl. bei Auftrag"),
    ),
    "zaunbau": (
        ("Zaunbau", "Planung & Montage Zaunsystem", "ab 89 €/m"),
        ("Sichtschutz", "Paneele & Streifen", "ab 45 €/m"),
        ("Gartentor", "Tor passend zum Zaun", "ab 390 €"),
        ("Einfahrtstor", "Einfahrt inkl. Beschlag", "ab 1.200 €"),
        ("Reparatur", "Pfosten, Latten, Beschläge", "ab 95 €"),
        ("Aufmaß", "Kostenloses Aufmaß vor Ort", "kostenlos"),
        ("Doppelstabmatte", "8/6/8 Systeme", "ab 72 €/m"),
        ("Holzlattenzaun", "Lärche / Fichte", "ab 95 €/m"),
        ("Gabionen", "Steinkörbe als Sichtschutz", "ab 180 €/m"),
        ("Torantrieb", "Automatisierung Starter", "ab 890 €"),
    ),
    "gartenpflege": (
        ("Rasenschnitt", "Regelmäßiger Schnitt mit Kanten", "ab 45 €"),
        ("Heckenschnitt", "Form- und Pflegeschnitt", "ab 65 €"),
        ("Beetpflege", "Jäten, Mulchen, Nachsetzen", "ab 55 €"),
        ("Laubentsorgung", "Herbstlaub inkl. Abfuhr", "ab 80 €"),
        ("Jahresvertrag", "Fester Pflegeplan", "ab 89 €/Monat"),
        ("Baumschnitt", "Obst- & Ziergehölze", "ab 95 €"),
        ("Rasenpflege", "Düngen & Vertikutieren", "ab 120 €"),
        ("Neuanlage Beet", "Planung & Bepflanzung", "auf Anfrage"),
        ("Winterdienst Garten", "Schutz & Schnitt", "auf Anfrage"),
        ("Beratung vor Ort", "Pflegeplan für Ihr Grundstück", "kostenlos"),
    ),
}

_DEFAULT_SERVICES = (
    ("Beratung", "Individuelle Erstberatung", "auf Anfrage"),
    ("Analyse", "Bestandsaufnahme & Empfehlung", "ab 99 €"),
    ("Umsetzung", "Umsetzung mit klaren Meilensteinen", "auf Anfrage"),
    ("Betreuung", "Laufende Begleitung", "Monatsabo"),
    ("Workshop", "Team-Workshop vor Ort", "ab 490 €"),
    ("Audit", "Qualitäts- & Prozesscheck", "ab 290 €"),
    ("Support", "Priorisierter Support", "inkl."),
    ("Dokumentation", "Transparente Unterlagen", "inkl."),
)


def _pick(seed: str, options: tuple[str, ...] | list[str]) -> str:
    if not options:
        return ""
    h = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    return options[h % len(options)]


def invent_company_name(*, niche_id: str, city: str, salt: str) -> tuple[str, str]:
    niche = (niche_id or "generic").strip().lower()
    prefixes, suffixes = _NAME_PARTS.get(niche, _NAME_PARTS["generic"])
    p = _pick(f"{salt}|{city}|pre", prefixes)
    s = _pick(f"{salt}|{city}|suf", suffixes)
    brand = f"{p} {s}".strip()
    legal = f"{brand} GmbH" if niche not in ("psychology", "law", "dental") else brand
    if niche == "law":
        legal = f"{brand}"
    return brand, legal


def fabricate_company(
    *,
    niche_id: str,
    city: str = "München",
    package_id: str = "business",
    diversity_salt: str = "",
    language: str = "de",
    phone: str = "",
    email: str = "",
    prefer_name: str = "",
) -> FabricatedCompany:
    """Invent a 5-year-old-feeling company for THIS brief."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    city_n = (city or "München").strip() or "München"
    salt = (diversity_salt or f"{niche}|{city_n}|{package_id}").strip()
    lang = (language or "de").strip().lower()

    if prefer_name.strip():
        brand = prefer_name.strip()
        legal = brand
    else:
        brand, legal = invent_company_name(niche_id=niche, city=city_n, salt=salt)

    h = int(hashlib.sha256(f"{salt}|year".encode()).hexdigest()[:6], 16)
    founded = 2016 + (h % 7)  # 2016–2022 → feels established

    slogans = {
        "restaurant": (
            "Ein Abend im italienischen Hof.",
            "Feuer, Produkt, Gastfreundschaft",
        ),
        "beauty": (
            "Ein Ritual der Schönheit — kein Salon.",
            "Schönheit mit Haltung",
        ),
        "auto": ("Ehrliche Diagnose. Klare Preise.", "Technik ohne Theater"),
        "psychology": (
            "Ein Ort, an dem es ruhiger wird.",
            "Zuhören, das trägt",
        ),
        "dental": ("Präzision, die Ruhe gibt", "Zähne. Vertrauen. Klarheit."),
        "law": ("Stille. Ordnung. Kontrolle.", "Klarheit vor Dramatik"),
        "dachreinigung": (
            "Nach dem Regen sieht das Dach wieder neu aus.",
            "Sauber vom First bis zur Rinne",
        ),
        "zaunbau": ("Grenze mit Haltung", "Zaun, der Jahre hält"),
        "gartenpflege": ("Garten in ruhigem Rhythmus", "Pflege ohne Chaos"),
        "handwerk": ("Handwerk mit Festpreis", "Sauber. Pünktlich. Klar."),
    }
    slogan = _pick(f"{salt}|slogan", slogans.get(niche, ("Klar. Menschlich. Präzise.", "Qualität ohne Show")))

    missions = {
        "restaurant": f"Gäste in {city_n} sollen den Abend länger erinnern als die Rechnung.",
        "beauty": f"Jeder Look soll im Alltag von {city_n} funktionieren — nicht nur im Spiegel.",
        "auto": f"Autobesitzer in {city_n} verdienen Diagnose ohne Verkaufsdruck.",
        "psychology": f"Menschen in {city_n} einen geschützten Raum geben, in dem Veränderung möglich ist.",
        "dental": f"Zahnmedizin in {city_n}, die Angst nimmt und Kosten klar macht.",
        "law": f"Mandanten in {city_n} Orientierung geben, bevor Konflikte eskalieren.",
        "dachreinigung": f"Hausbesitzer in {city_n} verdienen ein sauberes Dach ohne Überraschungen beim Preis.",
        "zaunbau": f"Grundstücke in {city_n} brauchen klare Grenzen — sauber montiert, fair kalkuliert.",
        "gartenpflege": f"Gärten in {city_n} sollen gepflegt bleiben, ohne dass Termine zum Stress werden.",
        "handwerk": f"Bauherren in {city_n} verdienen Festpreis und pünktliche Übergabe.",
    }
    mission = missions.get(niche, f"Kunden in {city_n} spürbar besser bedienen als gestern.")

    history = (
        f"Was als kleines Vorhaben in {city_n} begann, ist über die Jahre zu einem "
        f"festen Ort mit Stammgästen und klarer Handschrift geworden. "
        f"Seit {founded} wächst {brand} bewusst — Qualität vor Tempo."
    )
    approach = {
        "restaurant": "Saisonale Karte, kurze Wege zur Küche, Gast als Mensch — nicht als Ticket.",
        "beauty": "Beratung zuerst, Technik danach. Keine Trends ohne Haltbarkeit.",
        "auto": "Festpreis nach Diagnose. Keine Überraschungen auf der Rechnung.",
        "psychology": "Tempo des Menschen. Keine Methodenfabrik.",
        "dental": "Aufklärung vor Bohrer. Digitale Planung, ruhige Behandlung.",
        "law": "Schriftliche Einschätzung nach dem Erstgespräch. Keine leeren Versprechen.",
    }.get(niche, "Klarheit, Handwerk, langfristige Beziehung.")

    values = (
        "Präzision",
        "Menschlichkeit",
        "Transparenz",
        "Verlässlichkeit",
        "Handwerk",
    )

    services_pool = _SERVICES.get(niche, _DEFAULT_SERVICES)
    # 8–12 services depending on package
    n_svc = 8 if package_id == "basic" else (10 if package_id == "business" else 12)
    offset = int(hashlib.sha256(f"{salt}|svc".encode()).hexdigest()[:4], 16)
    rotated = list(services_pool[offset % len(services_pool) :]) + list(
        services_pool[: offset % len(services_pool)]
    )
    services = tuple(rotated[:n_svc])

    advantages = (
        f"Seit {founded} in {city_n}",
        "Transparente Preise",
        "Feste Ansprechpartner",
        "Termine mit Bestätigung",
        "Nachvollziehbarer Ablauf",
    )

    # Team
    first_names = ("Anna", "Jonas", "Mila", "Erik", "Sofia", "Noah", "Lea", "Max", "Clara", "Felix")
    roles = {
        "restaurant": ("Küchenchef/in", "Serviceleitung", "Sommelier", "Gastgeber/in"),
        "beauty": ("Creative Director", "Color Specialist", "Stylist/in", "Salonleitung"),
        "auto": ("Meister/in", "Diagnose-Techniker/in", "Serviceberater/in", "Lager"),
        "psychology": ("Psychologische/r Psychotherapeut/in", "Berater/in", "Praxisleitung", "Assistenz"),
        "dental": ("Zahnarzt/Zahnärztin", "Prophylaxe", "ZFA", "Praxisleitung"),
        "law": ("Rechtsanwalt/anwältin", "Associate", "Fachangestellte/r", "Partner/in"),
    }.get(niche, ("Leitung", "Spezialist/in", "Beratung", "Assistenz"))
    team = []
    for i in range(4):
        fn = _pick(f"{salt}|team|{i}", first_names)
        role = roles[i % len(roles)]
        team.append(
            (
                f"{fn} {_pick(f'{salt}|ln|{i}', ('Keller', 'Hoffmann', 'Weber', 'Schulz', 'Becker'))}",
                role,
                f"{role} bei {brand} — Fokus auf Qualität und ruhige Abläufe.",
            )
        )

    faq = (
        (
            f"Wie vereinbare ich einen Termin bei {brand}?",
            "Über das Kontaktformular, telefonisch oder per E-Mail. Sie erhalten eine Bestätigung.",
        ),
        (
            "Wie transparent sind die Kosten?",
            "Vor Beginn erhalten Sie eine klare Einschätzung. Keine versteckten Positionen.",
        ),
        (
            f"Seit wann gibt es {brand}?",
            f"Seit {founded} in {city_n} — gewachsen mit Stammkunden und klarer Handschrift.",
        ),
        (
            "Gibt es Parkplätze / Anreise?",
            f"Zentral in {city_n}. Details zur Anreise senden wir mit der Terminbestätigung.",
        ),
        (
            "Arbeitet ihr auch online / hybrid?",
            "Wo sinnvoll ja — Details klären wir im Erstkontakt.",
        ),
    )

    demo_tag = DEMO_REVIEW_LABEL_DE if lang.startswith("de") else DEMO_REVIEW_LABEL_EN
    review_bodies = {
        "restaurant": (
            "Endlich ein Abend, an den man sich erinnert — ruhig, präzise, herzlich.",
            "Karte kurz, Geschmack groß. Wir kommen wieder.",
            "Service ohne Theater. Genau richtig.",
        ),
        "beauty": (
            "Beratung ehrlich, Ergebnis alltagstauglich. Selten so zufrieden.",
            "Farbe hält, Schnitt sitzt. Endlich kein Trend-Opfer.",
            "Ruhiger Salon, klare Preise, starke Hands.",
        ),
        "auto": (
            "Diagnose klar, Preis gehalten. Selten erlebt.",
            "Keine Upselling-Show — nur das Nötige.",
            "Shuttle hat den Tag gerettet. Werkstatt mit Haltung.",
        ),
        "psychology": (
            "Endlich Raum zum Atmen. Professionell und menschlich.",
            "Klare Struktur, ohne Druck. Hat mir sehr geholfen.",
            "Vertrauensvoll von der ersten Minute.",
        ),
    }.get(
        niche,
        (
            "Seriös, klar, ohne Show. Weiterzuempfehlen.",
            "Fühlt sich nach echtem Handwerk an — nicht nach Vorlage.",
            "Transparente Kommunikation. Genau das wollte ich.",
        ),
    )
    reviews = tuple(
        (body, f"{_pick(f'{salt}|rev|{i}', first_names)} · {demo_tag}")
        for i, body in enumerate(review_bodies)
    )

    process = (
        "Kennenlernen & Bedarf",
        "Klare Empfehlung & Preis",
        "Umsetzung mit Abstimmung",
        "Nachsorge & Feedback",
    )

    blog = (
        f"Warum {brand} anders arbeitet",
        f"3 Dinge, die Kunden in {city_n} uns am häufigsten fragen",
        f"Hinter den Kulissen: Qualität statt Tempo",
        f"So bereiten Sie Ihren ersten Termin vor",
    )

    certs = {
        "restaurant": ("Hygiene-Konzept", "Allergenkennzeichnung", "Regionale Partner"),
        "beauty": ("Fortbildungen Color", "Premium-Produkte", "Ersthelfer vor Ort"),
        "auto": ("Meisterbetrieb", "Diagnose-Geräte aktuell", "Entsorgung zertifiziert"),
        "psychology": ("Approbation / Fachkunde", "Schweigepflicht", "Fortbildung"),
        "dental": ("Prophylaxe-Konzept", "Digitale Abformung", "Strahlenschutz"),
        "law": ("Fachanwaltschaft / Schwerpunkt", "DSGVO-Praxis", "Fortbildung"),
    }.get(niche, ("Qualitätsversprechen", "Transparente Prozesse", "Versicherungsschutz"))

    phone_n = phone.strip() or f"+49 { _pick(f'{salt}|ph', ('89', '40', '30', '221', '69')) } {1000000 + (h % 8000000)}"
    email_n = email.strip() or f"kontakt@{brand.lower().replace(' ', '-').replace('ä','ae').replace('ö','oe').replace('ü','ue')[:24]}.example.de"

    fp = hashlib.sha256(f"{brand}|{niche}|{city_n}|{founded}|{salt}".encode()).hexdigest()[:16]

    return FabricatedCompany(
        legal_name=legal,
        brand_name=brand,
        slogan=slogan,
        mission=mission,
        history=history,
        values=values,
        approach=approach,
        founded_year=founded,
        city=city_n,
        niche_id=niche,
        services=services,
        advantages=advantages,
        team=tuple(team),
        faq=faq,
        reviews=reviews,
        process_steps=process,
        blog_titles=blog,
        certificates=certs,
        hours="Mo–Fr 09:00–18:00 · Sa nach Vereinbarung",
        phone=phone_n,
        email=email_n,
        social=(f"instagram.com/{brand.lower().replace(' ', '')}.demo", f"linkedin.com/company/{brand.lower().replace(' ', '-')}-demo"),
        fingerprint=fp,
        demo_content=True,
    )


def apply_fabricated_company(
    analysis: AnalysisResult,
    contacts: dict[str, Any],
) -> tuple[AnalysisResult, dict[str, Any], FabricatedCompany]:
    """Merge invented company into analysis + contacts (demo / fabricate flag)."""
    contacts = dict(contacts)
    niche = str(contacts.get("niche") or analysis.niche or "generic")
    city = str(contacts.get("city") or "München")
    pkg = str(contacts.get("package_id") or "business")
    salt = str(contacts.get("diversity_salt") or "")
    # Prefer inventing a distinctive name for demos; keep order/gallery name when provided
    prefer = ""
    if contacts.get("keep_business_name") or contacts.get("demo_gallery"):
        prefer = str(contacts.get("business_name") or analysis.business_name or "")

    company = fabricate_company(
        niche_id=niche,
        city=city,
        package_id=pkg,
        diversity_salt=salt,
        language=str(contacts.get("ui_lang") or contacts.get("language") or "de"),
        phone=str(contacts.get("phone") or analysis.phone or ""),
        email=str(contacts.get("email") or analysis.email or ""),
        prefer_name=prefer,
    )

    analysis = replace(
        analysis,
        business_name=company.brand_name,
        headline=company.headline(),
        subtitle=company.mission,
        services=company.service_titles(),
        service_descriptions=company.service_descriptions(),
        about_text=company.about_long(),
        benefits=company.advantages,
        trust_points=company.advantages[:4],
        hours=company.hours,
        phone=company.phone,
        email=company.email,
        cta_label=analysis.cta_label or "Termin anfragen",
    )

    # Commercial Reality → First Impression Generation (client story owns H1)
    try:
        from app.factory.first_impression import (
            apply_first_impression_to_analysis,
            assert_first_impression,
            resolve_first_impression,
        )

        fi = resolve_first_impression(niche_id=niche, contacts=contacts)
        assert_first_impression(fi, package_id=pkg, hard=False)
        analysis = apply_first_impression_to_analysis(analysis, fi)
        contacts["client_story"] = fi.story
        contacts["problem_before"] = fi.problem_before
        contacts["first_impression"] = fi.as_dict()
        contacts["commercial_idea"] = fi.idea
        contacts["who_is_company"] = contacts.get("who_is_company") or fi.offer
    except Exception:
        pass

    contacts["business_name"] = company.brand_name
    contacts["phone"] = company.phone
    contacts["email"] = company.email
    contacts["whatsapp"] = company.phone
    contacts["services_list"] = company.service_titles()
    contacts["advantages"] = list(company.advantages)
    contacts["fabricated_company"] = company.as_dict()
    contacts["faq_override"] = [{"q": q, "a": a} for q, a in company.faq]
    contacts["team"] = [
        {"name": n, "role": r, "blurb": b} for n, r, b in company.team
    ]
    contacts["blog_titles"] = list(company.blog_titles)
    contacts["process_steps"] = list(company.process_steps)
    contacts["slogan"] = company.slogan
    contacts["mission"] = company.mission
    contacts["founded_year"] = company.founded_year
    # Demo-labeled reviews → TrustEvidence path (allowed as client_trust payload)
    contacts["trust"] = {
        "reviews": [[q, c] for q, c in company.reviews],
        "certificates": list(company.certificates),
        "guarantees": ["Transparente Preise", "Terminbestätigung", "Fester Ansprechpartner"],
        "faq": [{"q": q, "a": a} for q, a in company.faq],
        "demo_content": True,
        "demo_label": DEMO_REVIEW_LABEL_DE,
    }
    contacts["demo_content_notice"] = (
        "Demonstrationsunternehmen — erfunden für Virtus Core Preview. "
        "Bewertungen sind Demo-Inhalte, keine echten Kundenstimmen."
    )
    return analysis, contacts, company
