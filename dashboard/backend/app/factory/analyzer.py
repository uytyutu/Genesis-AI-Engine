"""Analyze owner request and pick landing template niche."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AnalysisResult:
    niche: str
    template_id: str
    business_name: str
    headline: str
    subtitle: str
    services: list[str]
    service_descriptions: tuple[str, ...]
    cta_label: str
    trust_points: tuple[str, ...]
    about_text: str
    benefits: tuple[str, ...]
    hours: str
    phone: str
    email: str


_NICHE_KEYWORDS = {
    # Specific niches first — dict order = match order.
    # Roof / fence / garden BEFORE generic "reinigung" (cleaning)
    "dachreinigung": (
        "dachreinigung",
        "dachreinigen",
        "dachwäsche",
        "dachwasche",
        "moosentfernung",
        "dachrinne",
        "dach klar",
        "roof cleaning",
        "roof clean",
        "чистка крыш",
        "очистка крыш",
    ),
    "zaunbau": (
        "zaunbau",
        "zaunbau",
        "sichtschutz",
        "doppelstab",
        "gartentor",
        "zaunmontage",
        "fence",
        "fencing",
        "заборы",
        "забор",
    ),
    "gartenpflege": (
        "gartenpflege",
        "rasenschnitt",
        "heckenschnitt",
        "laubentsorgung",
        "gärtner",
        "gartner",
        "landscape maintenance",
        "уход за садом",
        "сад и участок",
    ),
    "cleaning": (
        "reinigung",
        "reinigungsfirma",
        "gebäudereinigung",
        "gebaeudereinigung",
        "büroreinigung",
        "bueroreinigung",
        "unterhaltsreinigung",
        "putzfirma",
        "putzservice",
        "cleaning",
        "cleaner",
        "housekeeping",
        "уборк",
        "клининг",
    ),
    "auto_ankauf": (
        "autoankauf",
        "auto ankauf",
        "pkw ankauf",
        "fahrzeugankauf",
        "fahrzeug ankauf",
        "wir kaufen ihr auto",
        "auto verkaufen",
        "pkw verkaufen",
        "car buying",
        "sell your car",
        "автовыкуп",
        "выкуп авто",
        "сдать авто",
    ),
    # Before dental — "Praxis" alone must not steal psychologist practices
    "psychology": (
        "psycholog",
        "psychotherapie",
        "psychotherapeut",
        "therapeutische praxis",
        "counseling",
        "counsellor",
        "burnout",
        "achtsamkeit",
        "meditation",
        "paartherapie",
        "traumatherapie",
        "психолог",
        "психотерап",
    ),
    "dental": (
        "стоматолог",
        "dental",
        "зуб",
        "имплант",
        "ортодонт",
        "zahnarzt",
        "zahnmedizin",
        "zahnheilkunde",
        "zahn",
        "arztpraxis",
        "hausarzt",
        "врач",
        "поликлин",
        # "praxis" alone is too broad (Psychology Praxis) — require dental context via other words
    ),
    "computer": (
        "pc-reparatur",
        "pc reparatur",
        "pc-service",
        "pc service",
        "computerreparatur",
        "computer reparatur",
        "computer",
        "laptop",
        "notebook",
        "it-service",
        "it service",
        "handy reparatur",
        "smartphone reparatur",
        "datenrettung",
        "компьютер",
        "ноутбук",
    ),
    "appliance": (
        "hausgeräte",
        "hausgeraete",
        "weißware",
        "weissware",
        "waschmaschine",
        "kühlschrank",
        "kuehlschrank",
        "geschirrspüler",
        "geschirrspueler",
        "elektrogerät",
        "elektrogeraet",
        "бытовой техник",
        "холодильник",
        "стиральн",
    ),
    "elektro": (
        "elektroinstallation",
        "elektriker",
        "sicherungskasten",
        "e-check",
        "stromwerk",
        "smart home",
    ),
    "sanitaer": (
        "sanitär",
        "sanitaer",
        "badsanierung",
        "klempner",
        "heizungswartung",
        "wasserklar",
    ),
    "maler": (
        "malermeister",
        "maler ",
        "innenanstrich",
        "fassadenanstrich",
        "tapezier",
        "farbraum",
    ),
    "family_psychology": (
        "familienpraxis",
        "familientherapie",
        "paarberatung",
        "elterncoaching",
        "nestklar",
    ),
    "car_dealership": (
        "autohaus",
        "neuwagen",
        "gebrauchtwagen",
        "probefahrt",
        "nordlicht",
    ),
    "handwerk": (
        "elektriker",
        "elektroinstallation",
        "elektro ",
        "handwerker",
        "hausmeister",
        "allrounder",
        "alles aus einer hand",
        "meister auf alle",
        "renovierung",
        "montage service",
        "kleinreparatur",
        "fliesenleger",
        "maler und",
        "sanitär",
        "sanitaer",
        "мастер на все",
        "муж на час",
    ),
    "auto": (
        "автосервис",
        "авто",
        "autowerkstatt",
        "werkstatt",
        "машин",
        "ремонт авто",
        "шиномонтаж",
        "car service",
        "car repair",
        "repair shop",
        "garage",
        "kfz",
    ),
    "law": (
        "юрист",
        "адвокат",
        "rechtsanwalt",
        "kanzlei",
        "law office",
        "immigration",
        "иммиграц",
        "семейн",
        "family law",
        "business law",
        "anwalt",
    ),
    "accounting": (
        "steuerberater",
        "steuerberatung",
        "steuerkanzlei",
        "steuerbüro",
        "steuerbuero",
        "buchhaltung",
        "lohnbuchhaltung",
        "tax advisor",
        "бухгалтер",
        "налогов",
        "jahresabschluss",
        "lohnabrechnung",
    ),
    "photography": (
        "fotograf",
        "fotografin",
        "photography",
        "photographer",
        "portrait",
        "hochzeitsfoto",
        "фотограф",
        "фотостуд",
        "studio licht",
    ),
    "fitness": (
        "fitness",
        "fitnessstudio",
        "gym",
        "personal training",
        "personaltrainer",
        "фитнес",
        "трениров",
        "sportstudio",
    ),
    "realestate": (
        "immobilien",
        "immobilienmakler",
        "makler",
        "vermietung",
        "hausverkauf",
        "недвижим",
        "риелтор",
        "real estate",
        "realtor",
    ),
    "beauty": (
        "салон",
        "salon",
        "friseur",
        "frisör",
        "frisoer",
        "haarschnitt",
        "haarfarbe",
        "красот",
        "spa",
        "маникюр",
        "парикмахер",
        "ресниц",
        "wimper",
        "lash",
        "eyelash",
        "beauty",
        "nail",
        "brow",
        "kosmetik",
    ),
    "fashion": (
        "одежд",
        "бутик",
        "мода",
        "fashion",
        "kleidung",
        "boutique",
        "mode",
        "atelier",
        "second hand",
        "комисси",
        "wardrobe",
        "streetwear",
        "коллекц",
        "collection",
        "магазин одежды",
        "bekleidung",
        "damenmode",
        "herrenmode",
    ),
    "energy": ("солнечн", "solar", "панел", "фотоэлект", "энерг", "photovolta"),
    "green": (
        "озеленен",
        "ландшафт",
        "садов",
        "газон",
        "озелен",
        "garten",
        "gartenpflege",
        "rasen",
        "hecke",
        "hecken",
        "landschaft",
        "gardening",
        "landscape",
    ),
    "restaurant": (
        "restaurant",
        "resto",
        "bistro",
        "café",
        "cafe",
        "gastronomie",
        "gaststätte",
        "gaststaette",
        "pizzeria",
        "ресторан",
        "кафе",
        "кухн",
    ),
}


def analyze(description: str, *, niche_hint: str | None = None) -> AnalysisResult:
    text = description.strip()
    lower = text.lower()

    hint = (niche_hint or "").strip().lower()
    niche = "generic"
    for name, words in _NICHE_KEYWORDS.items():
        if any(w in lower for w in words):
            niche = name
            break

    # Explicit order / Commercial Gallery niche wins when it is a known profile
    known = set(_NICHE_KEYWORDS) | {
        "psychology",
        "family_psychology",
        "generic",
        "fashion",
        "beauty",
        "energy",
        "green",
        "restaurant",
        "law",
        "accounting",
        "photography",
        "fitness",
        "realestate",
        "dachreinigung",
        "zaunbau",
        "gartenpflege",
        "handwerk",
        "cleaning",
        "dental",
        "auto",
        "elektro",
        "sanitaer",
        "maler",
        "car_dealership",
        "orthodontics",
        "auto_detailing",
        "it_support",
        "computer",
    }
    if hint and hint in known and hint != "generic":
        niche = hint
    else:
        # Media Gate / DE gallery SSOT: garden-care auto-detect collapses to "green".
        # Explicit niche_hint="gartenpflege" stays specific for Handwerk demos.
        niche = {"gartenpflege": "green"}.get(niche, niche)

    business_name = _extract_business_name(text, niche)
    template_id = f"landing-{niche}-v1"
    cta_label = _detect_cta_label(lower)

    presets = {
        "cleaning": _preset_cleaning(business_name, template_id, cta_label, text),
        "auto_ankauf": _preset_auto_ankauf(business_name, template_id, cta_label, text),
        "psychology": _preset_psychology(business_name, template_id, cta_label, text),
        "dental": _preset_dental(business_name, template_id, cta_label, text),
        "computer": _preset_computer(business_name, template_id, cta_label, text),
        "appliance": _preset_appliance(business_name, template_id, cta_label, text),
        "handwerk": _preset_handwerk(business_name, template_id, cta_label, text),
        "auto": _preset_auto(business_name, template_id, cta_label, text),
        "law": _preset_law(business_name, template_id, cta_label, text),
        "accounting": _preset_accounting(business_name, template_id, cta_label, text),
        "photography": _preset_photography(business_name, template_id, cta_label, text),
        "fitness": _preset_fitness(business_name, template_id, cta_label, text),
        "realestate": _preset_realestate(business_name, template_id, cta_label, text),
        "beauty": _preset_beauty(business_name, template_id, cta_label, text),
        "fashion": _preset_fashion(business_name, template_id, cta_label, text),
        "energy": _preset_energy(business_name, template_id, cta_label, text),
        "green": _preset_green(business_name, template_id, cta_label, text),
        "restaurant": _preset_restaurant(business_name, template_id, cta_label, text),
        "dachreinigung": _preset_dachreinigung(business_name, template_id, cta_label, text),
        "zaunbau": _preset_zaunbau(business_name, template_id, cta_label, text),
        "gartenpflege": _preset_gartenpflege(business_name, template_id, cta_label, text),
    }

    if niche in presets:
        return presets[niche]

    result = _preset_generic(business_name, cta_label, text)
    # Keep explicit / keyword niche when no dedicated preset exists
    if niche and niche != "generic" and result.niche == "generic":
        from dataclasses import replace

        result = replace(
            result,
            niche=niche,
            template_id=template_id,
        )
    return result


def _preset_cleaning(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "reinigung")
    cta = "Kostenloses Angebot" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="cleaning",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — professionelle Reinigung",
        subtitle="Unterhalt, Büro und Grundreinigung — zuverlässig, versichert und mit klarem Angebot.",
        services=[
            "Unterhaltsreinigung",
            "Büroreinigung",
            "Grundreinigung",
            "Fenster & Glas",
        ],
        service_descriptions=(
            "Regelmäßige Pflege für Wohnungen und Häuser.",
            "Saubere Arbeitsplätze ohne Störung des Betriebs.",
            "Tiefenreinigung nach Umzug oder Renovierung.",
            "Streifenfreie Fenster innen und außen.",
        ),
        cta_label=cta,
        trust_points=("Versichert", "Geprüftes Personal", "Flexible Termine"),
        about_text=(
            f"{business_name} liefert saubere Ergebnisse mit festen Ansprechpartnern — "
            "ohne Überraschungen bei Preis und Termin."
        ),
        benefits=("Kostenloses Angebot in 24h", "Festpreis nach Begehung", "Ersatz bei Ausfall"),
        hours="Mo–Fr 7:00–18:00 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_dachreinigung(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "dach")
    cta = "Kostenloses Angebot" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="dachreinigung",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Dachreinigung & Fassade",
        subtitle=(
            "Moosentfernung, Dachwäsche, Dachrinne und Imprägnierung — "
            "Festpreis vor Ort, versichert, mit Vorher/Nachher."
        ),
        services=[
            "Dachreinigung",
            "Moosentfernung",
            "Fassadenwäsche",
            "Dachrinne reinigen",
            "Imprägnierung",
        ],
        service_descriptions=(
            "Schonende Hochdruck-/Niederdruckreinigung der Dachfläche.",
            "Moos und Algen entfernen ohne die Ziegel zu beschädigen.",
            "Fassade und Sockel von Schmutz und Bewuchs befreien.",
            "Laub und Ablagerungen aus der Rinne, Ablauf prüfen.",
            "Schutzanstrich gegen schnellen Wiederbewuchs.",
        ),
        cta_label=cta,
        trust_points=("Versichert & zertifiziert", "Festpreis vor Ort", "Vorher/Nachher Fotos"),
        about_text=(
            f"{business_name} reinigt Dächer und Fassaden für Einfamilienhäuser — "
            "klar kalkuliert, sauber hinterlassen, mit fester Ansprechperson."
        ),
        benefits=("Festpreisangebot", "Versichert auf dem Dach", "Termine mit Bestätigung"),
        hours="Mo–Fr 08:00–17:00 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_zaunbau(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "zaun")
    cta = "Kostenloses Angebot" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="zaunbau",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Zaunbau & Tore",
        subtitle="Doppelstab, Sichtschutz, Gartentore — Aufmaß kostenlos, Montage und Reparatur.",
        services=["Zaunbau", "Sichtschutz", "Gartentore", "Reparatur", "Beratung vor Ort"],
        service_descriptions=(
            "Planung und Montage von Zaunsystemen für Grundstück und Garten.",
            "Sichtschutzstreifen und Paneele für mehr Privatsphäre.",
            "Gartentore und Einfahrten passend zum Zaun.",
            "Reparatur und Nachrüstung bestehender Anlagen.",
            "Kostenloses Aufmaß und Materialberatung vor Ort.",
        ),
        cta_label=cta,
        trust_points=("Aufmaß kostenlos", "Deutsche Qualität", "Saubere Montage"),
        about_text=(
            f"{business_name} baut Zäune und Tore mit klaren Angeboten — "
            "vom Aufmaß bis zur fertigen Montage."
        ),
        benefits=("Festpreis nach Aufmaß", "Pünktliche Montage", "Saubere Baustelle"),
        hours="Mo–Fr 08:00–17:00",
        phone=phone,
        email=email,
    )


def _preset_gartenpflege(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "garten")
    cta = "Kostenloses Angebot" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="gartenpflege",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Gartenpflege",
        subtitle="Rasenschnitt, Hecke, Beete und Laub — zuverlässige Termine, ökologische Pflege.",
        services=["Rasenschnitt", "Heckenschnitt", "Beetpflege", "Laubentsorgung", "Jahresvertrag"],
        service_descriptions=(
            "Regelmäßiger Rasenschnitt mit sauberem Abschluss.",
            "Form- und Pflegeschnitt für Hecken und Gehölze.",
            "Beete jäten, mulchen und saisonal nachsetzen.",
            "Laubentsorgung im Herbst mit klaren Terminen.",
            "Jahresvertrag mit festem Pflegeplan für Privathäuser.",
        ),
        cta_label=cta,
        trust_points=("Zuverlässige Termine", "Ökologische Pflege", "Klarer Jahresplan"),
        about_text=(
            f"{business_name} pflegt Gärten mit ruhigem Rhythmus — "
            "damit der Garten gepflegt bleibt, ohne dass Sie jeden Termin selbst organisieren."
        ),
        benefits=("Feste Ansprechpartner", "Transparente Preise", "Jahresvertrag möglich"),
        hours="Mo–Fr 07:30–16:30 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_auto_ankauf(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "ankauf")
    cta = "Kostenlose Bewertung" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="auto_ankauf",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Autoankauf mit fairer Bewertung",
        subtitle="Kostenlose Einschätzung, transparentes Angebot und schnelle Abwicklung — auch mit Mängeln.",
        services=[
            "Kostenlose Bewertung",
            "Sofortankauf",
            "Abholung vor Ort",
            "Vertragsabwicklung",
        ],
        service_descriptions=(
            "Marktgerechte Einschätzung ohne Verpflichtung.",
            "Auszahlung nach Vereinbarung — oft noch am selben Tag.",
            "Wir holen Ihr Fahrzeug ab, wenn gewünscht.",
            "Klare Unterlagen und Abmeldung-Hilfe.",
        ),
        cta_label=cta,
        trust_points=("Faire Preise", "Schnelle Abwicklung", "Ohne Verpflichtung"),
        about_text=(
            f"{business_name} kauft PKW und Nutzfahrzeuge an — mit ehrlicher Bewertung "
            "statt Druckverkauf."
        ),
        benefits=("Bewertung in Minuten", "Auch Unfall- und Bastlerfahrzeuge", "Bar oder Überweisung"),
        hours="Mo–Sa 9:00–18:00",
        phone=phone,
        email=email,
    )


def _preset_auto(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "werkstatt")
    return AnalysisResult(
        niche="auto",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Werkstatt mit Festpreis-Diagnose",
        subtitle="Transparente Kostenvoranschläge, moderne Diagnose und Garantie auf alle Arbeiten.",
        services=[
            "Computer-Diagnose",
            "Motor & Getriebe",
            "Inspektion & Ölwechsel",
            "Reifen & Einlagerung",
        ],
        service_descriptions=(
            "Fehlerspeicher auslesen und Ursache in 30 Minuten erklären.",
            "Reparatur mit schriftlicher Garantie — ohne versteckte Posten.",
            "Herstellerkonformes Service nach Plan — nur was wirklich nötig ist.",
            "Wechsel, Auswuchten und saisonale Einlagerung unter einem Dach.",
        ),
        cta_label="Termin vereinbaren" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Meisterbetrieb", "Festpreis vor Start", "Garantie auf Arbeit"),
        about_text=(
            f"{business_name} ist Ihre Werkstatt für alle Marken — von der schnellen Diagnose "
            "bis zur umfassenden Reparatur. Wir erklären jeden Schritt, bevor Sie zustimmen."
        ),
        benefits=(
            "Kostenklarheit vor Reparaturbeginn",
            "Ersatzwagen auf Anfrage",
            "Digitale Servicehistorie für Ihr Fahrzeug",
        ),
        hours="Mo–Fr 8:00–18:00 · Sa 9:00–14:00",
        phone=phone,
        email=email,
    )


def _preset_computer(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "pcservice")
    return AnalysisResult(
        niche="computer",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — PC- & Laptop-Reparatur vor Ort",
        subtitle="Schnelle Diagnose, transparente Preise und Datenrettung — für Privat und Gewerbe.",
        services=[
            "PC- & Laptop-Reparatur",
            "Virus- und Performance-Check",
            "Datenrettung",
            "Netzwerk & Setup",
        ],
        service_descriptions=(
            "Hardware- und Softwarefehler finden und beheben — oft noch am selben Tag.",
            "Aufräumen, Updates und Schutz ohne unnötige Zusatzverkäufe.",
            "Wiederherstellung von Fotos und Dokumenten, wenn möglich.",
            "WLAN, Drucker und Arbeitsplatz-PCs zuverlässig einrichten.",
        ),
        cta_label="Termin anfragen" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Festpreis-Diagnose", "Datenschutz", "Vor-Ort möglich"),
        about_text=(
            f"{business_name} repariert Computer, Laptops und Smartphones mit klaren "
            "Kostenvoranschlägen. Ihre Daten bleiben bei uns vertraulich."
        ),
        benefits=(
            "Kostenvoranschlag vor dem Start",
            "Ersatzgerät nach Absprache",
            "Abholung und Rückgabe möglich",
        ),
        hours="Mo–Fr 9:00–18:00 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_appliance(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "hausgeraete")
    return AnalysisResult(
        niche="appliance",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Hausgeräte-Reparatur mit Festpreis",
        subtitle="Waschmaschine, Kühlschrank, Spülmaschine — Diagnose vor Ort und ehrliche Empfehlung.",
        services=[
            "Waschmaschinen-Service",
            "Kühl- und Gefriergeräte",
            "Geschirrspüler & Herde",
            "Ersatzteile & Wartung",
        ],
        service_descriptions=(
            "Fehler finden und beheben — oft noch beim ersten Termin.",
            "Kühlkette sichern und Lecks rechtzeitig stoppen.",
            "Pumpen, Heizungen und Elektronik fachgerecht tauschen.",
            "Original- und Qualitätsersatzteile mit Garantie auf die Arbeit.",
        ),
        cta_label="Reparatur anfragen" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Vor-Ort-Service", "Festpreis nach Diagnose", "Garantie"),
        about_text=(
            f"{business_name} repariert Weißware und Elektrogeräte für Haushalte und "
            "kleine Betriebe — klar, erreichbar und ohne Überraschungen."
        ),
        benefits=(
            "Anfahrt und Diagnose transparent kalkuliert",
            "Reparatur statt Neukauf, wenn sinnvoll",
            "Termine auch außerhalb der Kernzeit nach Absprache",
        ),
        hours="Mo–Fr 8:00–17:30 · Notfall nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_handwerk(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "handwerk")
    return AnalysisResult(
        niche="handwerk",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Handwerk aus einer Hand",
        subtitle="Montage, Kleinreparaturen und Renovierung — zuverlässig, pünktlich und fair kalkuliert.",
        services=[
            "Montage & Aufbau",
            "Kleinreparaturen",
            "Renovierung & Ausbessern",
            "Hausmeister-Service",
        ],
        service_descriptions=(
            "Möbel, Regale, Lampen und Geräte fachgerecht montieren.",
            "Tür, Fenster, Wasserhahn und Alltagsdefekte schnell beheben.",
            "Streichen, Fliesen ausbessern und kleine Umbauten.",
            "Regelmäßige Checks und Einsätze für Haus und Wohnung.",
        ),
        cta_label="Auftrag anfragen" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Pünktlich", "Festpreis-Angebot", "Versichert"),
        about_text=(
            f"{business_name} ist Ihr Allround-Handwerker vor Ort — von der kleinen "
            "Reparatur bis zur geplanten Renovierung, mit klarer Absprache."
        ),
        benefits=(
            "Ein Ansprechpartner für viele Gewerke",
            "Schriftliches Angebot vor dem Start",
            "Saubere Baustelle und termintreue Übergabe",
        ),
        hours="Mo–Fr 7:30–17:00 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_psychology(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "praxis")
    cta = "Erstgespräch buchen" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="psychology",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Raum für Klarheit und Vertrauen",
        subtitle=(
            "Ruhige Gespräche, transparente Honorare — online und vor Ort. "
            "Der erste Schritt darf leicht sein."
        ),
        services=[
            "Einzeltherapie",
            "Erstgespräch",
            "Online-Beratung",
            "Paartherapie",
            "Burnout-Prävention",
            "Achtsamkeit",
        ],
        service_descriptions=(
            "Geschützter Raum für Ihre Themen — in Ihrem Tempo.",
            "Kennenlernen ohne Druck: Anliegen, Rahmen und nächste Schritte.",
            "Sichere Video-Termine, wenn Sie von zu Hause aus starten möchten.",
            "Begleitung für Paare mit klaren Gesprächsstrukturen.",
            "Prävention und Erholung bei Erschöpfung und Überlastung.",
            "Praktische Übungen für Alltag und innere Ruhe.",
        ),
        cta_label=cta,
        trust_points=("Schweigepflicht", "Online & vor Ort", "Transparente Honorare"),
        about_text=(
            f"In der {business_name} steht der Mensch im Mittelpunkt — nicht Effekte. "
            "Wir schaffen einen geschützten Rahmen für Einzeltherapie, Erstgespräch und "
            "Online-Beratung: Sicherheit, Klarheit und professionelle Begleitung in Ihrem Tempo. "
            "Honorare und Ablauf besprechen wir transparent, bevor Sie sich entscheiden."
        ),
        benefits=(
            "Erstgespräch mit klarem Rahmen",
            "Flexible Termine — auch online",
            "Vertraulichkeit und ruhige Atmosphäre",
        ),
        hours="Mo–Fr 9:00–19:00 · Sa nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_dental(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "praxis")
    lower = raw.lower()
    hausarzt = any(
        k in lower for k in ("hausarzt", "allgemeinmed", "врач", "arztpraxis")
    ) and "zahn" not in lower
    if hausarzt:
        return AnalysisResult(
            niche="dental",
            template_id=template_id,
            business_name=business_name,
            headline=f"{business_name} — Hausarztpraxis mit klaren Terminen",
            subtitle="Vorsorge, Impfungen und Beratung — verständlich und ohne Hektik.",
            services=[
                "Vorsorge & Check-up",
                "Impfungen",
                "Akutsprechstunde",
                "Online-Termin",
            ],
            service_descriptions=(
                "Regelmäßige Untersuchungen und individuelle Gesundheitspläne.",
                "Schutzimpfungen nach aktuellen Empfehlungen.",
                "Schnelle Hilfe bei akuten Beschwerden — nach Kapazität.",
                "Termin online oder telefonisch — ohne lange Warteschleife.",
            ),
            cta_label="Termin buchen" if cta_label == "Kontakt aufnehmen" else cta_label,
            trust_points=("Kassen & Privat", "Digitale Rezepte", "Nachbarschaftspraxis"),
            about_text=(
                f"In der {business_name} nehmen wir uns Zeit für Ihre Fragen. "
                "Jeder Schritt wird erklärt — ruhig und verständlich."
            ),
            benefits=(
                "Kurze Wege und klare Erreichbarkeit",
                "Transparente Abläufe vor jeder Maßnahme",
                "Termine auch für Berufstätige",
            ),
            hours="Mo–Fr 8:00–18:00 · Sa nach Vereinbarung",
            phone=phone,
            email=email,
        )
    return AnalysisResult(
        niche="dental",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Zahnmedizin ohne versteckte Kosten",
        subtitle="Sanfte Behandlung, klare Therapiepläne und moderne Technik für Ihr Lächeln.",
        services=[
            "Prophylaxe & Kontrolle",
            "Ästhetische Zahnheilkunde",
            "Implantate & Prothetik",
            "Online-Termin",
        ],
        service_descriptions=(
            "Professionelle Reinigung und Früherkennung — entspannt und schmerzarm.",
            "Veneers, Bleaching und Formkorrektur mit natürlichem Ergebnis.",
            "Feste Zähne mit Plan und transparenter Kostenübersicht.",
            "Termin in zwei Minuten — ohne Warteschleife am Telefon.",
        ),
        cta_label="Termin buchen" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Angstfreie Behandlung", "Transparente Kosten", "Moderne Praxis"),
        about_text=(
            f"In der {business_name} verbinden wir moderne Zahnmedizin mit Zeit für Ihre Fragen. "
            "Jeder Behandlungsplan wird vorab besprochen — ohne Druck."
        ),
        benefits=(
            "Angstfreie Behandlung mit erklärenden Abläufen",
            "Festpreis-Optionen für größere Maßnahmen",
            "Familienfreundliche Termine am Nachmittag",
        ),
        hours="Mo–Do 8:00–19:00 · Fr 8:00–15:00",
        phone=phone,
        email=email,
    )


def _preset_law(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "kanzlei")
    lower = raw.lower()
    steuer = any(
        k in lower
        for k in (
            "steuerberater",
            "steuerberatung",
            "steuerkanzlei",
            "buchhaltung",
            "tax advisor",
            "налогов",
            "бухгалтер",
        )
    )
    if steuer:
        return _preset_accounting(business_name, template_id, cta_label, raw)
    focus = "Wirtschaftsrecht"
    if re.search(r"семейн|family", raw, re.I):
        focus = "Familienrecht"
    elif re.search(r"immigration|миграц", raw, re.I):
        focus = "Migrationsrecht"
    return AnalysisResult(
        niche="law",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Kanzlei für {focus}",
        subtitle="Klare Beratung, feste Ansprechpartner und verständliche nächste Schritte.",
        services=[
            "Erstberatung",
            "Vertragsprüfung",
            "Vertretung vor Behörden",
            "Begleitung bei Verhandlungen",
        ],
        service_descriptions=(
            "30 Minuten Orientierung — Sie wissen, was sinnvoll ist und was nicht.",
            "Verträge und AGB verständlich erklärt, bevor Sie unterschreiben.",
            "Strukturierte Anträge und Fristen — ohne Formular-Stress.",
            "Diskret und vorbereitet — wir vertreten Ihre Position klar.",
        ),
        cta_label="Beratung anfragen" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Zertifizierte Anwälte", "Vertraulich", "Deutsch & Englisch"),
        about_text=(
            f"{business_name} unterstützt Mandanten im {focus} mit pragmatischen Lösungen. "
            "Wir erklären Risiken und Chancen in klarer Sprache — ohne Juristenlatein."
        ),
        benefits=(
            "Feste Ansprechpartner statt Callcenter",
            "Transparente Honorarstruktur nach Erstgespräch",
            "Digitale Dokumentenablage für schnelle Rückfragen",
        ),
        hours="Mo–Fr 9:00–18:00 · Termine nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_accounting(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "steuer")
    cta = "Beratung anfragen" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="accounting",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Steuerberatung mit klaren Zahlen",
        subtitle="Buchhaltung, Jahresabschluss und Fristen — verständlich und termintreu.",
        services=["Steuererklärung", "Buchhaltung", "Jahresabschluss", "Lohnabrechnung"],
        service_descriptions=(
            "Privat und Gewerbe — fristgerecht.",
            "Laufende Buchführung ohne Chaos.",
            "Abschluss mit Erklärung der Kennzahlen.",
            "Lohnabrechnung und Meldungen.",
        ),
        cta_label=cta,
        trust_points=("Vertraulich", "Digitale Belege", "Feste Ansprechpartner"),
        about_text=(
            f"{business_name} begleitet Mandanten bei Steuern und Finanzen — "
            "ohne Fachchinesisch, mit klaren nächsten Schritten."
        ),
        benefits=("Unverbindliches Erstgespräch", "Transparente Honorare", "Erinnerung an Fristen"),
        hours="Mo–Fr 9:00–17:30",
        phone=phone,
        email=email,
    )


def _preset_photography(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "foto")
    cta = (
        "Shoot anfragen"
        if cta_label in ("Kontakt aufnehmen", "Kollektion ansehen")
        else cta_label
    )
    return AnalysisResult(
        niche="photography",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Fotografie mit Haltung",
        subtitle="Portraits, Hochzeit und Business — natürliche Bilder, klare Absprache.",
        services=["Portraits", "Hochzeitsfotografie", "Business-Portraits", "Studio"],
        service_descriptions=(
            "Authentische Portraits ohne Stress.",
            "Hochzeitstage dokumentiert.",
            "Bilder für Website und LinkedIn.",
            "Studio oder Outdoor — je nach Konzept.",
        ),
        cta_label=cta,
        trust_points=("Echte Referenzen", "Klare Pakete", "Schnelle Auswahl"),
        about_text=f"{business_name} fotografiert Menschen und Momente — mit ruhigem Ablauf.",
        benefits=("Probe-Shoot möglich", "Digitale Galerie", "Nutzungsrechte klar"),
        hours="Termine nach Vereinbarung",
        phone=phone,
        email=email,
    )


def _preset_fitness(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "fit")
    cta = "Probe-Training buchen" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="fitness",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Training mit Plan",
        subtitle="Personal Training, Kurse und Fortschritt — ohne leere Versprechen.",
        services=["Personal Training", "Gruppenskurse", "Probe-Training", "Ernährungscoaching"],
        service_descriptions=(
            "Individuelle Pläne nach Ziel.",
            "Kleine Gruppen mit klarer Anleitung.",
            "Unverbindlich testen — vor dem Abo.",
            "Alltagsnahe Tipps.",
        ),
        cta_label=cta,
        trust_points=("Trainer vor Ort", "Klare Mitgliedschaft", "Flexible Zeiten"),
        about_text=f"{business_name} ist Ihr Studio für nachhaltiges Training.",
        benefits=("Probe-Training", "Flexible Zeiten", "Transparente Preise"),
        hours="Mo–Fr 6:00–22:00",
        phone=phone,
        email=email,
    )


def _preset_realestate(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "immo")
    cta = "Bewertung anfragen" if cta_label == "Kontakt aufnehmen" else cta_label
    return AnalysisResult(
        niche="realestate",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Immobilien mit klarer Beratung",
        subtitle="Verkauf, Vermietung und Bewertung — lokal, transparent, ohne Druck.",
        services=["Immobilienbewertung", "Verkauf", "Vermietung", "Besichtigung"],
        service_descriptions=(
            "Marktgerechte Einschätzung.",
            "Verkaufsprozess mit klaren Meilensteinen.",
            "Vermietung inkl. Exposé.",
            "Termin für Besichtigung.",
        ),
        cta_label=cta,
        trust_points=("Lokale Marktkenntnis", "Transparente Provision", "Schnelle Rückmeldung"),
        about_text=f"{business_name} begleitet Eigentümer und Suchende — ehrliche Einschätzung.",
        benefits=("Kostenlose Ersteinschätzung", "Digitale Exposés", "Begleitung bis Übergabe"),
        hours="Mo–Fr 9:00–18:00",
        phone=phone,
        email=email,
    )


def _preset_fashion(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "mode")
    return AnalysisResult(
        niche="fashion",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Mode mit Charakter",
        subtitle=(
            "Neue Kollektionen, ausgewählte Stücke und Looks für den Alltag — "
            "kein generisches Agentur-Template."
        ),
        services=[
            "Neue Kollektionen",
            "Kuratierte Auswahl",
            "Styling-Beratung",
            "Click & Collect / Versand",
        ],
        service_descriptions=(
            "Aktuelle Drops und saisonale Capsule-Looks.",
            "Weniger, aber besser — Stücke mit Wiedererkennungswert.",
            "Passform und Stil in wenigen Minuten klären.",
            "Abholung vor Ort oder Lieferung nach Hause.",
        ),
        cta_label=cta_label if cta_label != "Kontakt aufnehmen" else "Kollektion ansehen",
        trust_points=("Echte Fotos der Ware", "Klare Größeninfos", "Schnelle Antwort"),
        about_text=(
            f"{business_name} ist Ihr Mode-Atelier / Boutique — "
            "Atmosphäre und Auswahl statt leerer Schaufenster-Vorlage."
        ),
        benefits=("Instagram-ready Looks", "Persönliche Beratung", "Lokale Abholung"),
        hours="Mo–Sa 10:00–19:00",
        phone=phone,
        email=email,
    )


def _preset_beauty(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "salon")
    lower = raw.lower()
    lashes = any(k in lower for k in ("ресниц", "wimper", "lash", "eyelash"))
    if lashes:
        return AnalysisResult(
            niche="beauty",
            template_id=template_id,
            business_name=business_name,
            headline=f"{business_name} — Wimpern & Brow Studio",
            subtitle="Natürliche Volumen-Looks, saubere Hygiene und Termine ohne Wartechaos.",
            services=[
                "1:1 Wimpernverlängerung",
                "Volumen & Mega Volume",
                "Brow Lamination",
                "Auffüllen / Remover",
            ],
            service_descriptions=(
                "Einzelwimpern für einen weichen Alltagsblick.",
                "Dichte Looks mit leichter Traegung — individuell abgestimmt.",
                "Form und Farbe der Brauen fuer einen klaren Rahmen.",
                "Auffrischen oder schonendes Entfernen alter Extensions.",
            ),
            cta_label=cta_label if cta_label != "Kontakt aufnehmen" else "Termin buchen",
            trust_points=("Patch-Test möglich", "Hygienestandard", "Feste Slot-Zeiten"),
            about_text=(
                f"{business_name} ist Ihr Studio fuer Wimpern und Brauen — "
                "klare Beratung, ruhige Atmosphaere, Ergebnis das im Alltag haelt."
            ),
            benefits=("Online-Buchung", "Vorher-Nachher Beratung", "Transparente Preise"),
            hours="Di–Sa 10:00–19:00",
            phone=phone,
            email=email,
        )
    return AnalysisResult(
        niche="beauty",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Stil, der zu Ihnen passt",
        subtitle="Erfahrene Stylisten, Premium-Produkte und entspannte Atmosphäre.",
        services=["Schnitt & Styling", "Coloration", "Maniküre", "Gesichtsbehandlung"],
        service_descriptions=(
            "Beratung, Schnitt und Finish — abgestimmt auf Ihren Alltag.",
            "Farbe und Strähnen mit Premium-Produkten.",
            "Hygienische Abläufe und langlebige Ergebnisse.",
            "Individuelle Pflegepläne für empfindliche Haut.",
        ),
        cta_label=cta_label if cta_label != "Kontakt aufnehmen" else "Termin buchen",
        trust_points=("Premium-Produkte", "Erfahrene Stylisten", "Entspannte Atmosphäre"),
        about_text=f"{business_name} ist Ihr Salon für Looks, die im Alltag funktionieren.",
        benefits=("Online-Termine", "Individuelle Beratung", "Fair kalkulierte Preise"),
        hours="Di–Sa 9:00–19:00",
        phone=phone,
        email=email,
    )


def _preset_energy(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "solar")
    return AnalysisResult(
        niche="energy",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Solar für Ihr Zuhause",
        subtitle="Ertrag berechnen, Anlage planen und montieren — alles aus einer Hand.",
        services=[
            "PV-Planung",
            "Wirtschaftlichkeitsrechnung",
            "Montage & Netzanschluss",
            "Wartung & Monitoring",
        ],
        service_descriptions=(
            "Dachprüfung und Modulauslegung passend zu Ihrem Verbrauch.",
            "Transparente Amortisation vor der Bestellung.",
            "Zertifizierte Monteure und saubere Übergabe.",
            "Monitoring und Serviceverträge optional.",
        ),
        cta_label="Angebot anfordern" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Deutschland", "Transparente Angebote", "Support vor Ort"),
        about_text=f"{business_name} plant Photovoltaik so, dass Zahlen und Realität zusammenpassen.",
        benefits=("Förderberatung", "Festes Projektteam", "Langfristiger Service"),
        hours="Mo–Fr 8:00–17:00",
        phone=phone,
        email=email,
    )


def _preset_green(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "garten")
    return AnalysisResult(
        niche="green",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Gärten, die gepflegt wirken",
        subtitle="Planung, Pflanzung und saisonale Pflege — termintreu und sauber.",
        services=[
            "Gartenplanung",
            "Bepflanzung",
            "Rasen & Schnitt",
            "Objektpflege",
        ],
        service_descriptions=(
            "Konzept und Pflanzenauswahl für Ihr Grundstück.",
            "Lieferung und fachgerechte Pflanzung.",
            "Rasen, Hecken und saisonale Schnitte.",
            "Regelmäßige Pflege für Firmen und Privat.",
        ),
        cta_label="Angebot anfordern" if cta_label == "Kontakt aufnehmen" else cta_label,
        trust_points=("Erfahrenes Team", "Klare Termine", "Schriftliche Angebote"),
        about_text=f"{business_name} gestaltet Außenbereiche, die langfristig gepflegt bleiben.",
        benefits=("Kostenlose Erstbegehung", "Festpreis-Angebote", "Saubere Baustellen"),
        hours="Mo–Fr 7:00–16:00",
        phone=phone,
        email=email,
    )


def _preset_restaurant(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "tisch")
    return AnalysisResult(
        niche="restaurant",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Küche mit Charakter",
        subtitle="Frische Gerichte, warme Atmosphäre und Reservierung ohne Umwege.",
        services=["Mittagstisch", "Abendkarte", "Events", "Takeaway"],
        service_descriptions=(
            "Saisonale Gerichte — klar kalkuliert und gut erklärt.",
            "Abendkarte mit Fokus auf Qualität statt Masse.",
            "Private Feiern und Firmenevents nach Absprache.",
            "Abholung und Lieferung in der Nachbarschaft.",
        ),
        cta_label=cta_label or "Tisch reservieren",
        trust_points=("Frische Zutaten", "Lokale Gäste", "Klare Allergene"),
        about_text=(
            f"{business_name} kocht für Gäste, die Wert auf ehrliche Küche legen. "
            "Reservieren Sie online oder telefonisch — wir bestätigen zeitnah."
        ),
        benefits=(
            "Speisekarte ohne Überraschungen",
            "Reservierung mit Bestätigung",
            "Barrierefreie Informationen zu Allergenen",
        ),
        hours="Di–So 11:30–14:00 · 17:30–22:00",
        phone=phone,
        email=email,
    )


def _preset_generic(business_name: str, cta_label: str, raw: str) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "info")
    brief = business_brief_for_site(raw)
    services, descriptions = _generic_services(raw)
    headline_tail = _headline_tail_from_services(services, brief)
    subtitle = brief or (
        f"{services[0]} · {services[1]} · {services[2]}"
        if len(services) >= 3
        else "Konkrete Leistungen, klare Ansprechpartner, schnelle Rückmeldung."
    )
    return AnalysisResult(
        niche="generic",
        template_id="landing-generic-v1",
        business_name=business_name,
        headline=f"{business_name} — {headline_tail}",
        subtitle=subtitle[:160],
        services=services,
        service_descriptions=descriptions,
        cta_label=cta_label if cta_label != "Kontakt aufnehmen" else "Anfrage senden",
        trust_points=("Schnelle Antwort", "Faire Preise", "Persönlicher Service"),
        about_text=(
            f"{business_name} arbeitet mit klaren Leistungen und erreichbaren Ansprechpartnern. "
            + (
                f"Schwerpunkt: {', '.join(services[:3])}."
                if services
                else "Wir melden uns zeitnah und halten Zusagen ein."
            )
        ),
        benefits=(
            f"Fokus auf {services[0]}" if services else "Klare Leistungspakete",
            "Angebote mit nachvollziehbaren Positionen",
            "Erreichbarkeit in der Kernzeit",
        ),
        hours="Mo–Fr 9:00–18:00",
        phone=phone,
        email=email,
    )


def _headline_tail_from_services(services: list[str], brief: str) -> str:
    if services:
        return services[0][:48]
    if brief:
        return brief.split(".")[0][:48].strip() or "klare Leistungen vor Ort"
    return "klare Leistungen vor Ort"


def _generic_services(raw: str) -> tuple[list[str], tuple[str, ...]]:
    lower = raw.lower()
    if any(w in lower for w in ("солнечн", "solar", "панел")):
        return (
            ["PV-Planung", "Montage", "Ertragscheck", "Wartung"],
            (
                "Auslegung nach Verbrauch und Dach.",
                "Montage durch zertifiziertes Team.",
                "Wirtschaftlichkeit und Fördercheck.",
                "Monitoring und Service nach Inbetriebnahme.",
            ),
        )
    if any(w in lower for w in ("озеленен", "ландшафт", "garten")):
        return (
            ["Gartenplanung", "Pflanzung", "Saisonpflege", "Erstbegehung"],
            (
                "Konzept für Ihr Grundstück.",
                "Lieferung und Pflanzung.",
                "Saisonale Pflege.",
                "Kostenlose Erstbegehung.",
            ),
        )
    # Never ship universal filler (Beratung / Umsetzung / Support) — derive from brief tokens.
    tokens = [
        t.strip(" .,;:")
        for t in re.split(r"[,;\n/|·•]+", raw)
        if 2 < len(t.strip(" .,;:")) < 40
    ]
    skip = {
        "website",
        "landing",
        "сайт",
        "лендинг",
        "für",
        "для",
        "und",
        "and",
        "the",
        "mit",
        "von",
    }
    crafted: list[str] = []
    for tok in tokens:
        low = tok.lower()
        if low in skip or low.startswith("http"):
            continue
        if any(w in low for w in ("gmbh", "ug ", "ltd", "@", "http")):
            continue
        if tok[:1].islower() and " " not in tok:
            continue
        title = tok[0].upper() + tok[1:] if tok else tok
        if title not in crafted:
            crafted.append(title)
        if len(crafted) >= 4:
            break
    if len(crafted) >= 2:
        descs = tuple(f"{s} — auf Anfrage detailliert." for s in crafted)
        return crafted, descs
    return (
        ["Erstgespräch", "Leistungsangebot", "Umsetzung vor Ort", "Nachbetreuung"],
        (
            "Ziele und Rahmen in einem kurzen Gespräch klären.",
            "Schriftliches Angebot mit klaren Positionen.",
            "Umsetzung mit vereinbarten Meilensteinen.",
            "Erreichbar für Rückfragen nach Abschluss.",
        ),
    )


def _contact_defaults(business_name: str, slug_hint: str) -> tuple[str, str]:
    slug = re.sub(r"[^a-z0-9]+", "", business_name.lower())[:24] or slug_hint
    phone = "+49 40 123 456 78"
    email = f"kontakt@{slug}.de"
    return phone, email


def _detect_cta_label(lower: str) -> str:
    if re.search(r"заявк", lower):
        return "Anfrage senden"
    if re.search(r"консультац", lower):
        return "Beratung anfragen"
    if re.search(r"запис", lower):
        return "Termin buchen"
    if re.search(r"позвон", lower):
        return "Jetzt anrufen"
    if re.search(r"купить|заказ", lower):
        return "Bestellen"
    return "Kontakt aufnehmen"


def _merge_trust_points(default: tuple[str, ...], raw: str) -> tuple[str, ...]:
    extra: list[str] = []
    lower = raw.lower()
    if any(w in lower for w in ("германи", "germany", "deutschland", "berlin")):
        extra.append("Deutschland")
    if any(w in lower for w in ("росси", "russia", "москв")):
        extra.append("Russland")
    if not extra:
        return default
    merged = list(default)
    for item in extra:
        if item not in merged:
            merged.insert(0, item)
    return tuple(merged[:3])


def _extract_business_name(text: str, niche: str) -> str:
    cleaned = re.sub(r"\s+", " ", text).strip()
    # "Firma Name — Beschreibung" → Firma Name
    lead = re.match(r"^([^—\n]{2,64}?)\s+[—–\-]\s+", cleaned)
    if lead:
        candidate = lead.group(1).strip()
        if not _looks_like_user_intent(candidate):
            return candidate
    # Word-boundary: avoid matching "praxis" inside "Arztpraxis"
    company = re.search(
        r"(?:компани[яи]|фирм[аы]|бренд|\bkanzlei|\bpraxis|\bwerkstatt)\s+"
        r"([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\.\-]+)?)",
        cleaned,
        re.IGNORECASE,
    )
    if company:
        return company.group(1).strip()
    for prefix in (
        "website for ",
        "мне нужен сайт для ",
        "хочу лендинг для ",
        "сайт для ",
        "лендинг для ",
    ):
        if cleaned.lower().startswith(prefix):
            cleaned = cleaned[len(prefix) :].strip(" .")
            break
    # "Auto Müller car repair" → Auto Müller
    name_match = re.match(
        r"^([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\.\-]+)?)",
        cleaned,
    )
    if name_match and not _looks_like_user_intent(name_match.group(1)):
        return name_match.group(1).strip()
    first_sentence = re.split(r"[.!?\n]", cleaned, maxsplit=1)[0].strip()
    if first_sentence and len(first_sentence) <= 48 and not _looks_like_user_intent(first_sentence):
        return first_sentence[0].upper() + first_sentence[1:]
    if len(cleaned) > 48:
        cleaned = cleaned[:45] + "…"
    if not cleaned or _looks_like_user_intent(cleaned):
        defaults = {
            "dental": "Zahnarztpraxis Weber",
            "auto": "Auto Müller",
            "auto_ankauf": "Auto Ankauf Nord",
            "cleaning": "Clean Profi",
            "computer": "PC Service Schmidt",
            "appliance": "Hausgeräte Schneider",
            "handwerk": "Handwerk Fischer",
            "law": "Kanzlei Schmidt",
            "beauty": "Salon Belle",
            "energy": "Solar Nord",
            "green": "Garten Profi",
        }
        return defaults.get(niche, business_name_fallback(niche))
    return cleaned[0].upper() + cleaned[1:]


def business_name_fallback(niche: str) -> str:
    return {
        "dental": "Zahnarztpraxis Weber",
        "auto": "Auto Müller",
        "auto_ankauf": "Auto Ankauf Nord",
        "cleaning": "Clean Profi",
        "computer": "PC Service Schmidt",
        "appliance": "Hausgeräte Schneider",
        "handwerk": "Handwerk Fischer",
        "law": "Kanzlei Schmidt",
        "beauty": "Salon Belle",
        "energy": "Solar Nord",
        "green": "Garten Profi",
    }.get(niche, "Ihr Unternehmen")


def _looks_like_user_intent(text: str) -> bool:
    lower = text.lower()
    return bool(
        re.search(
            r"(?:хочу|нужен|создай|создать|сделай|сайт|лендинг|website|landing|"
            r"компани[яи]\s+(?:моей|своей|нашей)|car repair|dental clinic|law office)",
            lower,
        )
    )


_META_BRIEF_DROP = re.compile(
    r"(?:хочу|нужен|создай|создать|сделай|убери|убрать|измени|правк|внести|описани[ея]\s+на\s+сайт|"
    r"сайт\s+для\s+(?:своей|моей|нашей)\s+компани|лендинг|landing|website|law office|dental clinic|"
    r"car repair|auto repair)",
    re.IGNORECASE,
)


def business_brief_for_site(raw: str) -> str:
    """Strip chat/meta instructions — keep business facts for site copy."""
    text = (raw or "").strip()
    if not text:
        return ""
    parts: list[str] = []
    for chunk in re.split(r"[\n.!?]+", text):
        line = chunk.strip()
        if len(line) < 8:
            continue
        if _META_BRIEF_DROP.search(line):
            continue
        if re.search(r"компани[яи]\s+[A-ZА-ЯЁ]", line, re.I) or re.search(
            r"(?:solar|панел|германи|заявк|консультац|установ|immigration|family law)", line, re.I
        ):
            parts.append(line)
    if parts:
        return ". ".join(parts)[:220]
    for chunk in re.split(r"[\n.!?]+", text):
        line = chunk.strip()
        if len(line) >= 12 and not _META_BRIEF_DROP.search(line):
            return line[:160]
    return ""
