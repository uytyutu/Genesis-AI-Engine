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
    "dental": ("стоматолог", "dental", "зуб", "клиник", "имплант", "ортодонт", "zahnarzt", "zahn"),
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
    ),
    "beauty": ("салон", "красот", "spa", "маникюр", "парикмахер"),
    "energy": ("солнечн", "solar", "панел", "фотоэлект", "энерг", "photovolta"),
    "green": ("озеленен", "ландшафт", "садов", "газон", "озелен"),
}


def analyze(description: str) -> AnalysisResult:
    text = description.strip()
    lower = text.lower()

    niche = "generic"
    for name, words in _NICHE_KEYWORDS.items():
        if any(w in lower for w in words):
            niche = name
            break

    business_name = _extract_business_name(text, niche)
    template_id = f"landing-{niche}-v1"
    cta_label = _detect_cta_label(lower)

    presets = {
        "dental": _preset_dental(business_name, template_id, cta_label, text),
        "auto": _preset_auto(business_name, template_id, cta_label, text),
        "law": _preset_law(business_name, template_id, cta_label, text),
        "beauty": _preset_beauty(business_name, template_id, cta_label, text),
        "energy": _preset_energy(business_name, template_id, cta_label, text),
        "green": _preset_green(business_name, template_id, cta_label, text),
    }

    if niche in presets:
        return presets[niche]

    return _preset_generic(business_name, cta_label, text)


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
        cta_label="Termin vereinbaren" if cta_label == "Связаться с нами" else cta_label,
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


def _preset_dental(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "praxis")
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
        cta_label="Termin buchen" if cta_label == "Связаться с нами" else cta_label,
        trust_points=("Erfahrene Ärzte", "Digitales Röntgen", "Garantie auf Arbeit"),
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
    focus = "Migrations- und Wirtschaftsrecht"
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
        cta_label="Beratung anfragen" if cta_label == "Связаться с нами" else cta_label,
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


def _preset_beauty(
    business_name: str, template_id: str, cta_label: str, raw: str
) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "salon")
    return AnalysisResult(
        niche="beauty",
        template_id=template_id,
        business_name=business_name,
        headline=f"{business_name} — Stil, der zu Ihnen passt",
        subtitle="Erfahrene Stylisten, Premium-Produkte und entspannte Atmosphäre.",
        services=["Schnitt & Styling", "Maniküre", "Gesichtspflege", "Gutscheine"],
        service_descriptions=(
            "Beratung, Schnitt und Finish — abgestimmt auf Ihren Alltag.",
            "Hygienische Abläufe und langlebige Ergebnisse.",
            "Individuelle Pflegepläne für empfindliche Haut.",
            "Geschenke, die wirklich Freude machen.",
        ),
        cta_label=cta_label if cta_label != "Связаться с нами" else "Termin buchen",
        trust_points=("Sterile Tools", "Premium-Marken", "Ruhige Atmosphäre"),
        about_text=f"{business_name} ist Ihr Salon für Looks, die im Alltag funktionieren.",
        benefits=("Online-Termine", "Stammstylist auf Wunsch", "Fair kalkulierte Preise"),
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
        cta_label=cta_label,
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
        cta_label=cta_label,
        trust_points=("Erfahrenes Team", "Klare Termine", "Schriftliche Angebote"),
        about_text=f"{business_name} gestaltet Außenbereiche, die langfristig gepflegt bleiben.",
        benefits=("Kostenlose Erstbegehung", "Festpreis-Angebote", "Saubere Baustellen"),
        hours="Mo–Fr 7:00–16:00",
        phone=phone,
        email=email,
    )


def _preset_generic(business_name: str, cta_label: str, raw: str) -> AnalysisResult:
    phone, email = _contact_defaults(business_name, "info")
    brief = business_brief_for_site(raw)
    subtitle = brief or "Professioneller Auftritt — klar, vertrauenswürdig und mobil optimiert."
    services, descriptions = _generic_services(raw)
    return AnalysisResult(
        niche="generic",
        template_id="landing-generic-v1",
        business_name=business_name,
        headline=f"{business_name} — Ihr Partner vor Ort",
        subtitle=subtitle[:160],
        services=services,
        service_descriptions=descriptions,
        cta_label=cta_label,
        trust_points=("Schnelle Antwort", "Faire Preise", "Persönlicher Service"),
        about_text=(
            f"{business_name} unterstützt Kunden mit klaren Angeboten und erreichbaren Ansprechpartnern. "
            "Wir melden uns zeitnah und halten Zusagen ein."
        ),
        benefits=(
            "Verständliche Kommunikation ohne Fachchinesisch",
            "Angebote mit klaren Leistungen",
            "Erreichbarkeit in der Kernzeit",
        ),
        hours="Mo–Fr 9:00–18:00",
        phone=phone,
        email=email,
    )


def _generic_services(raw: str) -> tuple[list[str], tuple[str, ...]]:
    lower = raw.lower()
    if any(w in lower for w in ("солнечн", "solar", "панел")):
        return (
            ["PV-Planung", "Montage", "Service", "Beratung"],
            (
                "Auslegung nach Verbrauch und Dach.",
                "Montage durch zertifiziertes Team.",
                "Wartung und Monitoring.",
                "Förder- und Wirtschaftlichkeitscheck.",
            ),
        )
    if any(w in lower for w in ("озеленен", "ландшафт", "garten")):
        return (
            ["Planung", "Pflanzung", "Pflege", "Beratung vor Ort"],
            (
                "Konzept für Ihr Grundstück.",
                "Lieferung und Pflanzung.",
                "Saisonale Pflege.",
                "Kostenlose Erstbegehung.",
            ),
        )
    return (
        ["Beratung", "Umsetzung", "Support", "Angebot anfordern"],
        (
            "Wir klären Ziele und nächste Schritte in einem Gespräch.",
            "Umsetzung mit festen Meilensteinen.",
            "Erreichbar, wenn Fragen auftauchen.",
            "Unverbindliches Angebot innerhalb von 48 Stunden.",
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
    return "Связаться с нами"


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
    company = re.search(
        r"(?:компани[яи]|фирм[аы]|бренд|kanzlei|praxis|werkstatt)\s+([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\-]+)?)",
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
        r"^([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\-]+)?)",
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
        "law": "Kanzlei Schmidt",
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
