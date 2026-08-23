"""Solution catalog — ready digital solutions by business (not template types)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Literal

SolutionKind = Literal[
    "website",
    "store",
    "automation",
    "chatbot",
    "marketing",
]


@dataclass(frozen=True)
class SolutionEntry:
    id: str
    kind: SolutionKind
    label_de: str
    label_en: str
    niche_id: str  # factory niche / store niche
    blurb: str
    available: bool = True

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# —— Business websites (DE market focus) ——
# Order = Owner niche rotation first (Beauty → Cleaning → IT → Dental → Restaurant), then rest.
WEBSITE_SOLUTIONS: tuple[SolutionEntry, ...] = (
    SolutionEntry(
        "kosmetikstudio",
        "website",
        "Nail · Brow · Lash · Massage",
        "Nail Brow Lash Massage Studio",
        "beauty",
        "Maniküre, Augenbrauen, Wimpern, Massage — Atelier-Atmosphäre",
    ),
    SolutionEntry("friseur", "website", "Friseur", "Hair Salon", "beauty", "Looks, Terminbuchung, Studio"),
    SolutionEntry("reinigung", "website", "Reinigung", "Cleaning Service", "cleaning", "Privat & Gewerbe — sichtbar sauber, pünktlich, vertrauenswürdig"),
    SolutionEntry(
        "it_service",
        "website",
        "Computer-Reparatur",
        "Computer Repair",
        "computer",
        "Diagnose, Reparatur, Datenrettung, Vor-Ort",
    ),
    SolutionEntry("zahnarzt", "website", "Zahnarzt", "Dentist", "dental", "Moderne Zahnmedizin, Vorsorge, Termin"),
    SolutionEntry("hausarzt", "website", "Hausarzt", "GP Practice", "dental", "Praxis, Öffnungszeiten, Termin"),
    SolutionEntry("restaurant", "website", "Restaurant", "Restaurant", "restaurant", "Menü, Reservierung, Atmosphäre"),
    SolutionEntry("cafe", "website", "Café", "Café", "restaurant", "Kaffee, Speisekarte, Lokal"),
    SolutionEntry("pizzeria", "website", "Pizzeria", "Pizzeria", "restaurant", "Ofen, Lieferung, Menü"),
    SolutionEntry("handwerk", "website", "Handwerk & Renovierung", "Crafts & Renovation", "handwerk", "Meister vor Ort — Projekte, Team, Vorher/Nachher"),
    SolutionEntry("elektriker", "website", "Elektriker", "Electrician", "handwerk", "Installationen, Notdienst, Zertifikate"),
    SolutionEntry("sanitaer", "website", "Sanitär & Heizung", "Plumbing & Heating", "handwerk", "Bad, Heizung, Notdienst"),
    SolutionEntry("dachreinigung", "website", "Dachreinigung", "Roof Cleaning", "dachreinigung", "Dach, Rinne, Imprägnierung mit Beweis"),
    SolutionEntry("gartenbau", "website", "Gartenbau", "Garden & Landscaping", "gartenpflege", "Gartenpflege, Hecke, Gestaltung"),
    SolutionEntry("autowerkstatt", "website", "Autowerkstatt", "Auto Workshop", "auto", "Diagnose, Inspektion, Bremsen, TÜV"),
    SolutionEntry("abschleppdienst", "website", "Abschleppdienst", "Towing Service", "auto", "24h Hilfe, Einsatzgebiet"),
    SolutionEntry("autohaus", "website", "Autohaus", "Car Dealership", "auto", "Fahrzeuge, Finanzierung, Probefahrt"),
    SolutionEntry("rechtsanwalt", "website", "Rechtsanwalt", "Law Firm", "law", "Bereiche, Team, Erstgespräch"),
    SolutionEntry("psychologie", "website", "Psychologie", "Psychology", "psychology", "Therapie, Vertrauen, ruhige Atmosphäre"),
    SolutionEntry("physiotherapie", "website", "Physiotherapie", "Physiotherapy", "fitness", "Behandlung, Termin, Praxis"),
    SolutionEntry("hotel", "website", "Hotel", "Hotel", "realestate", "Zimmer, Buchung, Location"),
    SolutionEntry("ferienwohnung", "website", "Ferienwohnung", "Holiday Apartment", "realestate", "Unterkunft, Kalender, Galerie"),
    SolutionEntry("steuerberater", "website", "Steuerberater", "Tax Advisor", "accounting", "Mandanten, Termine, Vertrauen"),
    SolutionEntry("immobilienmakler", "website", "Immobilienmakler", "Real Estate Agent", "realestate", "Objekte, Exposés, Anfrage"),
    SolutionEntry("versicherung", "website", "Versicherung", "Insurance Broker", "accounting", "Beratung, Policen, Kontakt"),
    SolutionEntry("fitnessstudio", "website", "Fitnessstudio", "Fitness Studio", "fitness", "Training, Mitgliedschaft, Coach"),
    SolutionEntry("personal_trainer", "website", "Personal Trainer", "Personal Trainer", "fitness", "Coaching, Pläne, Buchung"),
    SolutionEntry("fotograf", "website", "Fotograf", "Photographer", "photography", "Portfolio, Sessions, Stil"),
    SolutionEntry("eventagentur", "website", "Eventagentur", "Event Agency", "photography", "Events, Referenzen, Anfrage"),
    SolutionEntry("unternehmensberatung", "website", "Unternehmensberatung", "Business Consulting", "accounting", "Beratung, Cases, Kontakt"),
    SolutionEntry("sprachschule", "website", "Sprachschule", "Language School", "psychology", "Kurse, Levels, Anmeldung"),
    SolutionEntry("nachhilfe", "website", "Nachhilfe", "Tutoring", "psychology", "Fächer, Termine, Lehrer"),
    SolutionEntry("tierarzt", "website", "Tierarzt", "Veterinarian", "dental", "Praxis, Notfall, Team"),
    SolutionEntry("hundesalon", "website", "Hundesalon", "Dog Grooming", "beauty", "Pflege, Termin, Galerie"),
    SolutionEntry("blumenladen", "website", "Blumenladen", "Florist", "green", "Sträuße, Anlässe, Bestellung"),
)

STORE_SOLUTIONS: tuple[SolutionEntry, ...] = (
    SolutionEntry("beauty_store", "store", "Beauty Store", "Beauty Store", "beauty", "Pflege, Bundles, Reviews"),
    SolutionEntry("fashion", "store", "Fashion Store", "Fashion Store", "fashion", "Looks, Kollektionen, Checkout"),
    SolutionEntry("electronics", "store", "Electronics Store", "Electronics Store", "computer", "Geräte, Specs, Versand"),
    SolutionEntry("furniture", "store", "Furniture Store", "Furniture Store", "furniture", "Räume, Konfigurator-feeling"),
    SolutionEntry("pet_shop", "store", "Pet Shop", "Pet Shop", "green", "Futter, Zubehör, Tiere"),
    SolutionEntry("pharmacy", "store", "Pharmacy", "Pharmacy", "beauty", "OTC, Beratung, Lieferung"),
    SolutionEntry("auto_parts", "store", "Auto Parts", "Auto Parts", "auto", "Teile, Suche, Marken"),
    SolutionEntry("sports", "store", "Sports Shop", "Sports Shop", "fitness", "Sport, Outfits, Equipment"),
    SolutionEntry("coffee", "store", "Coffee Store", "Coffee Store", "restaurant", "Bohnen, Sets, Abo"),
    SolutionEntry("bakery", "store", "Bakery", "Bakery", "restaurant", "Backwaren, Vorbestellung"),
    SolutionEntry("jewelry", "store", "Jewelry", "Jewelry", "fashion", "Stücke, Vertrauen, Galerie"),
    SolutionEntry("toys", "store", "Toys", "Toys", "fashion", "Spielzeug, Altersfilter"),
    SolutionEntry("home_garden", "store", "Home & Garden", "Home & Garden", "green", "Haus & Garten"),
    SolutionEntry("flowers", "store", "Flowers", "Flowers", "green", "Blumen online"),
    SolutionEntry("handmade", "store", "Handmade", "Handmade", "fashion", "Unikate, Maker-Story"),
    SolutionEntry("digital", "store", "Digital Products", "Digital Products", "computer", "Downloads, Lizenzen"),
)

AUTOMATION_SOLUTIONS: tuple[SolutionEntry, ...] = (
    SolutionEntry("ai_assistant", "automation", "AI Assistant", "AI Assistant", "computer", "Virtus AI im Workspace", False),
    SolutionEntry("crm_automation", "automation", "CRM Automation", "CRM Automation", "accounting", "Leads → Pipeline", False),
    SolutionEntry("lead_automation", "automation", "Lead Automation", "Lead Automation", "accounting", "Form → Follow-up", False),
    SolutionEntry("whatsapp_automation", "automation", "WhatsApp Automation", "WhatsApp Automation", "computer", "Channel flows", False),
    SolutionEntry("email_automation", "automation", "Email Automation", "Email Automation", "computer", "Sequences", False),
    SolutionEntry("booking_automation", "automation", "Booking Automation", "Booking Automation", "fitness", "Termine ohne Chaos", False),
    SolutionEntry("invoice_automation", "automation", "Invoice Automation", "Invoice Automation", "accounting", "Rechnung aus Auftrag", False),
)

CHATBOT_SOLUTIONS: tuple[SolutionEntry, ...] = (
    SolutionEntry("support_bot", "chatbot", "Support Bot", "Support Bot", "computer", "Fragen 24/7"),
    SolutionEntry("sales_bot", "chatbot", "Sales Bot", "Sales Bot", "computer", "Qualifizierung & Termin"),
    SolutionEntry("booking_bot", "chatbot", "Booking Bot", "Booking Bot", "fitness", "Terminbuchung im Chat"),
    SolutionEntry("restaurant_bot", "chatbot", "Restaurant Bot", "Restaurant Bot", "restaurant", "Tisch & Menü"),
    SolutionEntry("medical_bot", "chatbot", "Medical Bot", "Medical Bot", "dental", "Praxis-FAQ & Termin"),
    SolutionEntry("law_bot", "chatbot", "Law Bot", "Law Bot", "law", "Erstkontakt Kanzlei"),
    SolutionEntry("realestate_bot", "chatbot", "Real Estate Bot", "Real Estate Bot", "realestate", "Objektanfragen"),
)

MARKETING_SOLUTIONS: tuple[SolutionEntry, ...] = (
    SolutionEntry("reels", "marketing", "Reels / Shorts", "Reels / Shorts", "photography", "Coming soon", False),
    SolutionEntry("meta_ads", "marketing", "Meta Ads", "Meta Ads", "photography", "Coming soon", False),
    SolutionEntry("seo_content", "marketing", "SEO Content", "SEO Content", "computer", "Coming soon", False),
)


def all_solutions() -> list[SolutionEntry]:
    return list(
        WEBSITE_SOLUTIONS
        + STORE_SOLUTIONS
        + AUTOMATION_SOLUTIONS
        + CHATBOT_SOLUTIONS
        + MARKETING_SOLUTIONS
    )


def solutions_by_kind(kind: SolutionKind) -> list[SolutionEntry]:
    return [s for s in all_solutions() if s.kind == kind]


def catalog_payload(*, locale: str = "de") -> dict[str, Any]:
    """Public catalog JSON for vitrine / API."""
    de = (locale or "de").lower().startswith("de")

    def pack(entries: tuple[SolutionEntry, ...]) -> list[dict[str, Any]]:
        rows = []
        for e in entries:
            rows.append(
                {
                    "id": e.id,
                    "kind": e.kind,
                    "label": e.label_de if de else e.label_en,
                    "niche_id": e.niche_id,
                    "blurb": e.blurb,
                    "available": e.available,
                    "order_href": (
                        f"/order?niche={e.niche_id}&solution={e.id}"
                        if e.kind == "website" and e.available
                        else f"/order/shop?niche={e.niche_id}&solution={e.id}"
                        if e.kind == "store" and e.available
                        else f"/order/bot?solution={e.id}"
                        if e.kind == "chatbot" and e.available
                        else None
                    ),
                }
            )
        return rows

    return {
        "canon": "Digital Business Creator",
        "commerce_modes": ["standalone", "connected"],
        "groups": [
            {
                "id": "websites",
                "title": "Сайты для бизнеса" if not de else "Websites für Unternehmen",
                "title_en": "Business websites",
                "blurb": "Ready digital solutions — not templates.",
                "items": pack(WEBSITE_SOLUTIONS),
            },
            {
                "id": "stores",
                "title": "Online-Shops",
                "title_en": "Online stores",
                "blurb": "By industry — not «a generic shop».",
                "items": pack(STORE_SOLUTIONS),
            },
            {
                "id": "automation",
                "title": "Automatisierung",
                "title_en": "Automation",
                "blurb": "Business flows — Connected ecosystem.",
                "items": pack(AUTOMATION_SOLUTIONS),
            },
            {
                "id": "chatbots",
                "title": "AI Chatbots",
                "title_en": "AI chatbots",
                "blurb": "Role-based digital employees.",
                "items": pack(CHATBOT_SOLUTIONS),
            },
            {
                "id": "marketing",
                "title": "Marketing",
                "title_en": "Marketing",
                "blurb": "Later — ads, Reels, SEO content.",
                "items": pack(MARKETING_SOLUTIONS),
            },
        ],
    }


__all__ = [
    "AUTOMATION_SOLUTIONS",
    "CHATBOT_SOLUTIONS",
    "MARKETING_SOLUTIONS",
    "STORE_SOLUTIONS",
    "SolutionEntry",
    "SolutionKind",
    "WEBSITE_SOLUTIONS",
    "all_solutions",
    "catalog_payload",
    "solutions_by_kind",
]
