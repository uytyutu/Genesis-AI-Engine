"""Business Language Engine — niche voice after Business Intelligence.

Law: Factory does not use one generic AI copywriter for every site.
After niche is known, copy must sound like a German specialist for that industry.

Pipeline: Interview → Business Intelligence → Industry → Country → Business Language → Website
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# Words that scream "website generator" on a beauty / local service site
FORBIDDEN_GENERIC_TOKENS: frozenset[str] = frozenset(
    {
        "audit",
        "analysis",
        "analyse",
        "support",
        "documentation",
        "dokumentation",
        "execution",
        "umsetzung",  # as service title alone
        "workshop",
        "betreuung",  # alone as beauty service title
        "implementation",
        "delivery",
        "onboarding",
        "stakeholder",
        "synergie",
        "synergy",
        "holistisch",  # overused AI filler in DE marketing
    }
)

FORBIDDEN_GENERIC_PHRASES: tuple[str, ...] = (
    "wir bieten qualitativ",
    "qualität und zuverlässigkeit",
    "individueller ansatz",
    "individuellen ansatz",
    "individueller ansatz zu jedem",
    "wir arbeiten mit liebe",
    "wir wurden 20",
    "gegründet. was als",
    "präzision, menschlichkeit, transparenz",
    "qualität vor tempo",
    "kunden spürbar besser bedienen",
    "nicht nur stichworte",
    "qualitative dienstleistungen",
    "höchste standards",
    "ihre zufriedenheit steht",
    "maßgeschneiderte lösungen",
    "ganzheitliche betreuung",
)


@dataclass(frozen=True)
class IndustryVoice:
    """Copy DNA for one industry — not a translation layer."""

    industry_id: str
    tone: tuple[str, ...]
    lexicon: tuple[str, ...]
    forbidden_extra: tuple[str, ...] = ()
    hero_patterns: tuple[str, ...] = ()
    about_patterns: tuple[str, ...] = ()
    service_examples: tuple[tuple[str, str], ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "industry_id": self.industry_id,
            "tone": list(self.tone),
            "lexicon": list(self.lexicon),
            "forbidden_extra": list(self.forbidden_extra),
            "hero_patterns": list(self.hero_patterns),
            "about_patterns": list(self.about_patterns),
            "service_examples": [
                {"title": t, "blurb": b} for t, b in self.service_examples
            ],
        }


VOICE_PACKS: dict[str, IndustryVoice] = {
    "beauty_nail_brow_massage": IndustryVoice(
        industry_id="beauty_nail_brow_massage",
        tone=("emotional", "premium", "beruhigend", "weiblich-elegant"),
        lexicon=(
            "Entspannung",
            "Schönheit",
            "Wohlbefinden",
            "Perfektion",
            "Natürlich",
            "Pflege",
            "Eleganz",
            "Maniküre",
            "Augenbrauen",
            "Wimpern",
            "Massage",
        ),
        forbidden_extra=("audit", "workshop", "analyse", "support", "dokumentation"),
        hero_patterns=(
            "Schönheit beginnt bei den Details.",
            "Perfekte Nägel, natürliche Augenbrauen und entspannende Massagen – alles an einem Ort.",
        ),
        about_patterns=(
            "Hier kommen Menschen hin, um für eine Stunde den Alltag hinter sich zu lassen.",
        ),
        service_examples=(
            ("Maniküre & Pediküre", "Saubere Form, gepflegte Haut, lackiert so, wie es zu Ihnen passt."),
            ("Augenbrauen-Architektur", "Zeichnung, Färbung und Form – natürlich und präzise."),
            ("Wimpernverlängerung & Lifting", "Offener Blick, ohne dass es künstlich wirkt."),
            ("Entspannungsmassage", "Druck, der löst – Zeit, die Ihnen gehört."),
            ("Gesichts- & Hautpflege", "Ruhige Routinen mit Produkten, die wir selbst nutzen."),
            ("Geschenkgutscheine", "Für jemanden, dem Sie echte Auszeit schenken wollen."),
        ),
    ),
    "dental": IndustryVoice(
        industry_id="dental",
        tone=("vertrauensvoll", "ruhig", "medizinisch-modern"),
        lexicon=(
            "Moderne Zahnmedizin",
            "Schmerzarm",
            "Präzision",
            "Implantologie",
            "Vorsorge",
            "Gesundheit",
        ),
        service_examples=(
            ("Prophylaxe", "Saubere Vorsorge ohne Drama."),
            ("Füllungen & Zahnersatz", "Haltbar, unauffällig, erklärt vor dem Bohren."),
            ("Implantate", "Planung mit Bildern, die Sie verstehen."),
        ),
    ),
    "handwerk": IndustryVoice(
        industry_id="handwerk",
        tone=("nüchtern", "verbindlich", "festpreis"),
        lexicon=("Festpreis", "Pünktlich", "Saubere Arbeit", "Meisterbetrieb", "Garantie"),
        service_examples=(
            ("Festpreis-Angebot", "Schriftlich, bevor wir anfangen."),
            ("Termintreue", "Wir kommen, wenn wir gesagt haben."),
        ),
    ),
    "autohaus": IndustryVoice(
        industry_id="autohaus",
        tone=("sicher", "transparent", "verkaufsstark"),
        lexicon=(
            "Geprüfte Fahrzeuge",
            "Finanzierung",
            "Garantie",
            "Probefahrt",
            "Sofort verfügbar",
        ),
    ),
    "auto_repair": IndustryVoice(
        industry_id="auto_repair",
        tone=("technisch", "klar", "ohne Showroom-Floskeln"),
        lexicon=("Diagnose", "Inspektion", "Bremsen", "Ölwechsel", "TÜV", "Reparatur"),
    ),
    "restaurant": IndustryVoice(
        industry_id="restaurant",
        tone=("einladend", "sinnlich", "gastlich"),
        lexicon=("Frisch", "Hausgemacht", "Reservieren", "Regional", "Küche"),
    ),
    "cleaning": IndustryVoice(
        industry_id="cleaning",
        tone=("zuverlässig", "diskret", "pünktlich"),
        lexicon=("Sauberkeit", "Pünktlichkeit", "Vertrauen", "Schlüsselübergabe"),
    ),
    "it_repair": IndustryVoice(
        industry_id="it_repair",
        tone=("klar", "schnell", "technisch ehrlich"),
        lexicon=("Diagnose", "Datenrettung", "Reparatur", "Schutz", "Termin"),
    ),
}


# Map Factory niche / subniche ids → voice pack
_NICHE_ALIASES: dict[str, str] = {
    "nail_studio": "beauty_nail_brow_massage",
    "beauty": "beauty_nail_brow_massage",
    "nail": "beauty_nail_brow_massage",
    "brow": "beauty_nail_brow_massage",
    "massage": "beauty_nail_brow_massage",
    "spa": "beauty_nail_brow_massage",
    "dental": "dental",
    "dentist": "dental",
    "zahnarzt": "dental",
    "handwerk": "handwerk",
    "craftsman": "handwerk",
    "autohaus": "autohaus",
    "car_dealer": "autohaus",
    "auto_repair": "auto_repair",
    "werkstatt": "auto_repair",
    "restaurant": "restaurant",
    "cleaning": "cleaning",
    "reinigung": "cleaning",
    "it_repair": "it_repair",
    "computer_repair": "it_repair",
}


@dataclass
class BusinessLanguageBrief:
    """Ready-to-use copy brief for renderers."""

    industry_id: str
    market: str
    company_name: str
    city: str
    voice: IndustryVoice
    hero_headline: str
    hero_sub: str
    about_lead: str
    about_body: str
    services: list[dict[str, str]] = field(default_factory=list)
    cta: str = "Termin anfragen"
    flags: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "industry_id": self.industry_id,
            "market": self.market,
            "company_name": self.company_name,
            "city": self.city,
            "voice": self.voice.as_dict(),
            "hero_headline": self.hero_headline,
            "hero_sub": self.hero_sub,
            "about_lead": self.about_lead,
            "about_body": self.about_body,
            "services": self.services,
            "cta": self.cta,
            "flags": self.flags,
        }


def resolve_voice(niche_id: str, subniche_id: str = "") -> IndustryVoice:
    key = (subniche_id or niche_id or "").strip().lower()
    pack_id = _NICHE_ALIASES.get(key) or _NICHE_ALIASES.get(niche_id.strip().lower())
    if pack_id and pack_id in VOICE_PACKS:
        return VOICE_PACKS[pack_id]
    # Fallback: handwerk-neutral, never beauty-generic for unknown
    return VOICE_PACKS.get("handwerk") or next(iter(VOICE_PACKS.values()))


def find_forbidden_hits(text: str) -> list[str]:
    low = (text or "").lower()
    hits: list[str] = []
    for phrase in FORBIDDEN_GENERIC_PHRASES:
        if phrase in low:
            hits.append(phrase)
    for tok in FORBIDDEN_GENERIC_TOKENS:
        # word-ish boundary
        if f" {tok} " in f" {low} " or low.startswith(tok + " ") or low.endswith(" " + tok):
            hits.append(tok)
    return sorted(set(hits))


def assert_niche_language(text: str, niche_id: str) -> list[str]:
    """Return FAIL reasons if copy still sounds like a generator."""
    reasons: list[str] = []
    hits = find_forbidden_hits(text)
    voice = resolve_voice(niche_id)
    for extra in voice.forbidden_extra:
        if extra.lower() in (text or "").lower():
            hits.append(extra)
    if hits:
        reasons.append("forbidden_generic:" + ",".join(sorted(set(hits))[:12]))
    return reasons


def build_beauty_lumia_brief(
    *,
    company_name: str = "Studio LUMIA",
    city: str = "München",
    founder: str = "Olena Melnyk",
) -> BusinessLanguageBrief:
    """Owner-demo brief — German beauty agency voice, not AI filler."""
    voice = VOICE_PACKS["beauty_nail_brow_massage"]
    services = [
        {"title": t, "blurb": b} for t, b in voice.service_examples
    ]
    return BusinessLanguageBrief(
        industry_id=voice.industry_id,
        market="DE",
        company_name=company_name,
        city=city,
        voice=voice,
        hero_headline="Schönheit beginnt bei den Details.",
        hero_sub=(
            "Maniküre, Augenbrauen, Wimpern und entspannende Massage in einem Atelier – "
            "mit festen Terminen, ruhigem Tempo und Aufmerksamkeit für Sie."
        ),
        about_lead=(
            "Wir haben einen Ort geschaffen, an den man nicht nur wegen schöner Nägel "
            "oder klarer Brauen kommt."
        ),
        about_body=(
            f"Bei {company_name} in {city} gönnen Sie sich eine Stunde ohne Termindruck. "
            f"{founder} und das Team arbeiten präzise – und lassen Sie den Alltag draußen. "
            "Sie gehen mit dem Gefühl, Zeit für sich genommen zu haben: gepflegte Hände, "
            "natürliche Augenpartie, entspannter Nacken. Produkte, die wir selbst tragen. "
            "Termine mit Bestätigung. WhatsApp, wenn etwas dazwischenkommt."
        ),
        services=services,
        cta="Termin anfragen",
        flags=["german_business_standard", "no_generic_ai_phrases"],
    )


def german_market_checklist(is_store: bool = False) -> list[str]:
    """Legal / trust surfaces every DE site must carry (Factory law)."""
    base = [
        "impressum",
        "datenschutz",
        "kontakt",
        "cookie_banner_if_needed",
        "whatsapp",
        "oeffnungszeiten",
        "telefon",
        "email",
        "termin_buchen",
        "faq",
        "dsgvo_form_hint",
    ]
    if is_store:
        base.extend(["widerruf", "versand", "zahlung", "agb"])
    return base
