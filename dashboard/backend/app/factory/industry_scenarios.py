"""Industry scenario packs — journey, FAQ seeds, layout bias per niche."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IndustryScenario:
    niche_id: str
    journey: str  # booking | repair | consult | dine | shop | service
    layout_bias: tuple[str, ...]
    faq_seeds: tuple[tuple[str, str], ...]
    process_steps: tuple[str, ...]
    emotional_tone: str
    cta_voice: str


_SCENARIOS: dict[str, IndustryScenario] = {
    "beauty": IndustryScenario(
        "beauty",
        "booking",
        ("L3", "L6", "L1"),
        (
            ("Wie buche ich einen Termin?", "Online oder telefonisch — wir bestätigen Ihren Slot."),
            ("Welche Leistungen bieten Sie an?", "Schnitt, Farbe, Pflege und mehr — siehe Leistungen."),
            ("Brauche ich eine Beratung vorher?", "Gerne kurz vor dem Termin — besonders bei Farbe."),
        ),
        ("Anfrage", "Beratung", "Termin", "Nachpflege"),
        "elegant_warm",
        "Termin buchen",
    ),
    "dental": IndustryScenario(
        "dental",
        "booking",
        ("L2", "L6", "L1"),
        (
            ("Nehmen Sie neue Patienten auf?", "Ja — vereinbaren Sie einen Ersttermin."),
            ("Tut eine Behandlung weh?", "Wir erklären jeden Schritt und arbeiten möglichst schmerzarm."),
            ("Was kostet eine Kontrolle?", "Transparente Kostenschätzung vor der Behandlung."),
        ),
        ("Erstkontakt", "Diagnose", "Therapieplan", "Nachsorge"),
        "calm_trust",
        "Termin buchen",
    ),
    "auto": IndustryScenario(
        "auto",
        "repair",
        ("L4", "L5", "L1"),
        (
            ("Kann ich einen Kostenvoranschlag bekommen?", "Ja — nach Diagnose schriftlich und klar."),
            ("Wie lange dauert eine Inspektion?", "Je nach Fahrzeug — wir nennen Ihnen einen Zeitrahmen."),
            ("Gibt es einen Ersatzwagen?", "Auf Anfrage — bitte frühzeitig Bescheid geben."),
        ),
        ("Diagnose", "Angebot", "Reparatur", "Abholung"),
        "industrial_confident",
        "Termin vereinbaren",
    ),
    "law": IndustryScenario(
        "law",
        "consult",
        ("L2", "L6", "L1"),
        (
            ("Ist das Erstgespräch verbindlich?", "Wir klären den Rahmen transparent vorab."),
            ("Welche Unterlagen brauche ich?", "Wir nennen Ihnen die nötigen Dokumente nach dem Kontakt."),
            ("Arbeiten Sie auch remote?", "Je nach Mandat — digital und vor Ort möglich."),
        ),
        ("Kontakt", "Erstberatung", "Strategie", "Vertretung"),
        "strict_premium",
        "Beratung anfragen",
    ),
    "restaurant": IndustryScenario(
        "restaurant",
        "dine",
        ("L5", "L3", "L6"),
        (
            ("Kann ich einen Tisch reservieren?", "Ja — per Formular oder Telefon."),
            ("Gibt es Allergenkennzeichnung?", "Auf der Karte und auf Nachfrage beim Service."),
            ("Habt ihr Takeaway?", "Je nach Angebot — siehe Speisekarte / Kontakt."),
        ),
        ("Reservierung", "Empfang", "Menü", "Empfehlung"),
        "appetite_visual",
        "Tisch reservieren",
    ),
    "fashion": IndustryScenario(
        "fashion",
        "shop",
        ("L3", "L6", "L1"),
        (
            ("Kann ich online bestellen?", "Click & Collect oder Versand — je nach Verfügbarkeit."),
            ("Gibt es Größenberatung?", "Ja — vor Ort oder kurz per Nachricht."),
            ("Wie sind die Öffnungszeiten?", "Siehe Kontaktbereich auf dieser Seite."),
        ),
        ("Entdecken", "Beratung", "Anprobe", "Kauf"),
        "editorial_bold",
        "Kollektion ansehen",
    ),
    "accounting": IndustryScenario(
        "accounting",
        "consult",
        ("L2", "L1", "L6"),
        (
            ("Was kostet die Erstberatung?", "Wir nennen das Honorar vorab — transparent."),
            ("Arbeiten Sie digital?", "Ja — Belege und Austausch auch digital möglich."),
            ("Welche Fristen gelten?", "Wir erinnern Sie rechtzeitig an wichtige Termine."),
        ),
        ("Kontakt", "Unterlagen", "Umsetzung", "Fristen"),
        "calm_trust",
        "Beratung anfragen",
    ),
    "photography": IndustryScenario(
        "photography",
        "booking",
        ("L3", "L6", "L1"),
        (
            ("Wie läuft ein Shooting ab?", "Briefing, Shoot, Auswahl — klar und ruhig."),
            ("Wann bekomme ich die Bilder?", "Nach dem Shoot mit vereinbartem Zeitfenster."),
            ("Gibt es Pakete?", "Ja — feste Pakete ohne Überraschungen."),
        ),
        ("Anfrage", "Briefing", "Shoot", "Galerie"),
        "editorial_bold",
        "Shoot anfragen",
    ),
    "fitness": IndustryScenario(
        "fitness",
        "booking",
        ("L5", "L1", "L4"),
        (
            ("Kann ich Probe trainieren?", "Ja — Probe-Training vor dem Abo."),
            ("Brauche ich Vorkenntnisse?", "Nein — wir starten auf Ihrem Niveau."),
            ("Welche Kurszeiten gibt es?", "Siehe Kursplan und Kontakt."),
        ),
        ("Probe", "Plan", "Training", "Fortschritt"),
        "industrial_confident",
        "Probe-Training buchen",
    ),
    "realestate": IndustryScenario(
        "realestate",
        "consult",
        ("L2", "L5", "L1"),
        (
            ("Was kostet eine Bewertung?", "Ersteinschätzung klar kommuniziert — ohne Druck."),
            ("Wie lange dauert ein Verkauf?", "Abhängig vom Objekt — mit Meilensteinplan."),
            ("Betreuen Sie auch Vermietung?", "Ja — Exposé und Interessentenfilter inklusive."),
        ),
        ("Bewertung", "Exposé", "Besichtigung", "Abschluss"),
        "strict_premium",
        "Bewertung anfragen",
    ),
}


def resolve_scenario(niche_id: str) -> IndustryScenario | None:
    key = (niche_id or "generic").strip().lower()
    return _SCENARIOS.get(key)


def scenario_faq_for(niche_id: str, *, business: str, city: str, service: str) -> list[dict[str, str]]:
    sc = resolve_scenario(niche_id)
    if not sc:
        return []
    out: list[dict[str, str]] = []
    for q, a in sc.faq_seeds:
        ans = a
        if business:
            ans = ans  # keep neutral — no invented claims
        if city and "vor Ort" not in ans and niche_id in ("beauty", "dental", "auto"):
            ans = f"{ans} Standort: {city}."
        if service and "{service}" in a:
            ans = a.replace("{service}", service)
        out.append({"q": q, "a": ans})
    return out
