"""Commercial UI: never ship empty Hero fields; niche CTA beats market appointment chrome."""

from __future__ import annotations

from dataclasses import replace

from app.factory.analyzer import AnalysisResult

# Market-profile appointment chrome — OK for dental/beauty, wrong for cleaning / ankauf / solar.
_APPOINTMENT_CTAS = frozenset(
    {
        "termin buchen",
        "termin vereinbaren",
        "book now",
        "book appointment",
        "prendre rendez-vous",
        "afspraak maken",
        "pedir cita",
        "umów wizytę",
        "записаться",
        "записаться на приём",
        "записаться на прием",
    }
)

_WEAK_CTAS = _APPOINTMENT_CTAS | frozenset(
    {
        "",
        "kontakt aufnehmen",
        "contact us",
        "get quote",  # US market chrome — niche should prefer specific
        "зв’язатися",
        "отправить",
    }
)

# Primary CTA per niche (DE — Path A factory default language).
NICHE_DEFAULT_CTA: dict[str, str] = {
    "cleaning": "Kostenloses Angebot",
    "auto_ankauf": "Kostenlose Bewertung",
    "auto": "Termin vereinbaren",
    "dental": "Termin buchen",
    "beauty": "Termin buchen",
    "law": "Beratung anfragen",
    "energy": "Angebot anfordern",
    "green": "Angebot anfordern",
    "computer": "Reparatur anfragen",
    "appliance": "Reparatur anfragen",
    "handwerk": "Auftrag anfragen",
    "restaurant": "Tisch reservieren",
    "generic": "Anfrage senden",
}

# Niches where market "Termin buchen" is acceptable if analyzer left a weak CTA.
_APPOINTMENT_OK_NICHES = frozenset({"dental", "beauty", "restaurant"})

_NICHE_SERVICE_FALLBACK: dict[str, tuple[str, ...]] = {
    "cleaning": ("Unterhaltsreinigung", "Büroreinigung", "Grundreinigung", "Fenster"),
    "auto_ankauf": ("Kostenlose Bewertung", "Sofortankauf", "Abholung", "Vertragsabwicklung"),
    "auto": ("Diagnose", "Inspektion", "Reifen", "Ölwechsel"),
    "law": ("Erstberatung", "Vertragsprüfung", "Vertretung", "Verhandlungen"),
    "energy": ("PV-Planung", "Montage", "Service", "Monitoring"),
    "green": ("Gartenpflege", "Heckenschnitt", "Rasensanierung", "Saisonpflege"),
    "dental": ("Prophylaxe", "Füllungen", "Implantate", "Ästhetik"),
    "beauty": ("Schnitt & Styling", "Coloration", "Maniküre", "Gesichtsbehandlung"),
    "computer": ("PC-Reparatur", "Notebook-Service", "Datenrettung", "Netzwerk"),
    "appliance": ("Reparatur", "Ersatzteile", "Wartung", "Notdienst"),
    "handwerk": ("Rohbau", "Sanierung", "Ausbau", "Renovierung"),
    "restaurant": ("Mittagstisch", "Abendkarte", "Events", "Takeaway"),
    "generic": ("Beratung", "Umsetzung", "Support", "Angebot"),
}

_NICHE_HERO_FALLBACK: dict[str, tuple[str, str]] = {
    "cleaning": (
        "{name} — professionelle Reinigung",
        "Zuverlässige Reinigung für Privat und Gewerbe — klares Angebot, feste Termine.",
    ),
    "auto_ankauf": (
        "{name} — Autoankauf ohne Stress",
        "Kostenlose Bewertung, faires Angebot und schnelle Abwicklung vor Ort.",
    ),
    "auto": (
        "{name} — Werkstatt mit klarer Diagnose",
        "Transparente Kostenvoranschläge und moderne Diagnose.",
    ),
    "law": (
        "{name} — klare Beratung",
        "Verständliche nächste Schritte und feste Ansprechpartner.",
    ),
    "energy": (
        "{name} — Solar für Ihr Zuhause",
        "Planung, Ertragsrechnung und Montage aus einer Hand.",
    ),
    "green": (
        "{name} — Gärten, die gepflegt wirken",
        "Planung, Pflanzung und saisonale Pflege — termintreu.",
    ),
    "dental": (
        "{name} — moderne Zahnmedizin",
        "Klare Therapiepläne und ruhige Betreuung.",
    ),
    "beauty": (
        "{name} — Stil, der zu Ihnen passt",
        "Erfahrene Stylisten und entspannte Atmosphäre.",
    ),
    "computer": (
        "{name} — schneller PC-Service",
        "Diagnose, Reparatur und Datenrettung mit klaren Preisen.",
    ),
    "appliance": (
        "{name} — Hausgeräte-Service",
        "Reparatur vor Ort und ehrliche Empfehlung.",
    ),
    "handwerk": (
        "{name} — Handwerk mit Festpreis",
        "Montage und Renovierung — pünktlich und fair kalkuliert.",
    ),
    "restaurant": (
        "{name} — Küche mit Charakter",
        "Frische Gerichte und Reservierung ohne Umwege.",
    ),
    "generic": (
        "{name} — lokal und erreichbar",
        "Klares Angebot, schneller Kontakt, professionelle Umsetzung.",
    ),
}


def _norm(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


def niche_default_cta(niche: str) -> str:
    return NICHE_DEFAULT_CTA.get((niche or "generic").lower(), NICHE_DEFAULT_CTA["generic"])


def resolve_delivery_cta(
    *,
    niche: str,
    analysis_cta: str,
    market_default_cta: str = "",
) -> str:
    """Niche CTA wins for service niches; market chrome localizes appointment niches."""
    niche_key = (niche or "generic").lower()
    niche_cta = niche_default_cta(niche_key)
    current = (analysis_cta or "").strip()
    market = (market_default_cta or "").strip()
    current_n = _norm(current)
    market_n = _norm(market)

    # Cleaning / Ankauf / Solar / Handwerk… — never ship «Termin buchen» chrome.
    if niche_key not in _APPOINTMENT_OK_NICHES:
        if current and current_n not in _WEAK_CTAS and current_n not in _APPOINTMENT_CTAS:
            return current
        return niche_cta or market or "Anfrage senden"

    # Dental / beauty / restaurant — market chrome may localize the appointment CTA.
    if current and current_n not in _WEAK_CTAS:
        if market and market_n and market_n != current_n and current_n in _APPOINTMENT_CTAS:
            return market
        return current
    return market or niche_cta or "Anfrage senden"


def ensure_analysis_hero(analysis: AnalysisResult) -> AnalysisResult:
    """Fill empty headline / subtitle / CTA / services so Hero never renders blank."""
    niche = (analysis.niche or "generic").lower()
    name = (analysis.business_name or "").strip() or "Ihr Unternehmen"
    hl_tpl, sub_tpl = _NICHE_HERO_FALLBACK.get(niche, _NICHE_HERO_FALLBACK["generic"])

    headline = (analysis.headline or "").strip() or hl_tpl.format(name=name)
    subtitle = (analysis.subtitle or "").strip() or sub_tpl
    cta = resolve_delivery_cta(
        niche=niche,
        analysis_cta=analysis.cta_label or "",
        market_default_cta="",
    )

    services = [s for s in (analysis.services or []) if str(s).strip()]
    descriptions = [d for d in (analysis.service_descriptions or ()) if str(d).strip()]
    if not services:
        services = list(
            _NICHE_SERVICE_FALLBACK.get(
                niche, ("Beratung", "Umsetzung", "Support", "Angebot")
            )
        )
    while len(descriptions) < len(services):
        descriptions.append(services[len(descriptions)])

    benefits = tuple(b for b in (analysis.benefits or ()) if str(b).strip())
    trust = tuple(t for t in (analysis.trust_points or ()) if str(t).strip())
    about = (analysis.about_text or "").strip() or f"{name} — lokaler Partner mit klarem Angebot."

    return replace(
        analysis,
        headline=headline,
        subtitle=subtitle,
        cta_label=cta,
        services=services,
        service_descriptions=tuple(descriptions[: len(services)]),
        benefits=benefits or ("Klare Kommunikation", "Faire Preise", "Erreichbar"),
        trust_points=trust or ("Lokal", "Transparent", "Zuverlässig"),
        about_text=about,
    )


def hero_html_has_empty_blocks(html: str) -> list[str]:
    """Detect empty <h1>, empty hero lead, empty CTA — for commercial audit tests."""
    import re

    issues: list[str] = []
    if re.search(r"<h1[^>]*>\s*</h1>", html, re.I):
        issues.append("empty_h1")
    if re.search(r"<p[^>]*class=\"[^\"]*lead[^\"]*\"[^>]*>\s*</p>", html, re.I):
        issues.append("empty_subtitle")
    if re.search(r'href="#contact"[^>]*>\s*</a>', html, re.I):
        issues.append("empty_cta")
    # Visible filler only — ignore HTML attribute placeholder="…"
    body = re.sub(r"<[^>]+>", " ", html)
    if re.search(r"\b(TODO|lorem ipsum|\[your )\b", body, re.I):
        issues.append("placeholder_text")
    return issues
