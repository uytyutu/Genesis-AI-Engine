"""Business Intelligence Generation — understand the company before HTML.

STOP THINKING LIKE A WEBSITE GENERATOR.
Virtus Core creates a digital business: sub-niche → identity → components → media → site.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BusinessComponent:
    id: str
    label: str
    why: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BusinessIntelligence:
    """Answers Factory must know before generating HTML."""

    niche_id: str
    subniche_id: str
    subniche_label: str
    business_model: str  # e.g. family_premium_service
    city: str
    company_name: str
    who: str
    trust_why: str
    sells: str
    differentiator: str
    atmosphere: str
    people: str
    projects_focus: str
    media_brief: dict[str, str] = field(default_factory=dict)
    components: tuple[BusinessComponent, ...] = ()
    site_jobs: tuple[str, ...] = ()
    style: str = ""
    clients_who: str = ""
    fingerprint: str = ""
    canon: str = "Digital Business Creator"
    business_scale: str = "small_team"
    dream_vision: str = ""
    dream_signals: dict[str, str] = field(default_factory=dict)
    clarify_answers: dict[str, str] = field(default_factory=dict)
    technical_decisions: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["components"] = [c.as_dict() if hasattr(c, "as_dict") else c for c in self.components]
        d["site_jobs"] = list(self.site_jobs)
        return d


# Sub-niche detectors: keyword → (subniche_id, label, atmosphere bias)
_SUBNICHE_HINTS: dict[str, tuple[tuple[str, ...], str, str, str]] = {
    # psychology
    "cbt": (("cbt", "kognitive", "cognitive"), "cbt", "CBT / kognitive Therapie", "calm_minimal"),
    "anxiety": (("angst", "anxiety", "panik"), "anxiety", "Angst & Panik", "calm_soft"),
    "family_psy": (("familie", "family therapy", "paar"), "family", "Familien- / Paartherapie", "warm_editorial"),
    "child_psy": (("kind", "child", "jugend"), "child", "Kinder- & Jugendpsychologie", "warm_friendly"),
    "online_psy": (("online", "video", "fern"), "online", "Online-Sitzungen", "calm_minimal"),
    "emdr": (("emdr",), "emdr", "EMDR", "calm_clinical"),
    # restaurant
    "italian": (("italien", "italian", "pasta", "trattoria"), "italian", "Italienisches Restaurant", "warm_evening"),
    "sushi": (("sushi", "japan"), "sushi", "Sushi / Japanisch", "minimal_dark"),
    "burger": (("burger", "smash"), "burger", "Burger", "bold_youth"),
    "cafe": (("café", "cafe", "kaffee", "coffee"), "cafe", "Café", "light_natural"),
    "pizza": (("pizza", "pizzeria"), "pizza", "Pizzeria", "warm_family"),
    "steak": (("steak", "grill"), "steak", "Steakhouse", "dark_premium"),
    "vegan": (("vegan", "plant"), "vegan", "Vegan / Plant-based", "natural_green"),
    # handwerk / roof
    "roof": (("dach", "roof", "moos"), "roof_cleaning", "Dachreinigung", "outdoor_trust"),
    "bathroom": (("bad", "badreno", "fliese"), "bathroom", "Badrenovierung", "craftsman_clean"),
    "kitchen": (("küche", "ikea", "kitchen"), "kitchen", "Küchenmontage", "craftsman_clean"),
    "paint": (("maler", "streich", "paint"), "painting", "Malerarbeiten", "craftsman_clean"),
    # auto
    "tires": (("reifen", "tire", "vulka"), "tires", "Reifenservice", "industrial"),
    "detailing": (("detail", "politur"), "detailing", "Detailing", "premium_dark"),
    "body": (("karosserie", "body"), "body_shop", "Karosserie", "industrial"),
    "dealership": (("autohaus", "verkauf", "gebraucht"), "dealership", "Autohaus", "corporate_clean"),
}

# Default Business Components per niche (AI picks; client does not)
_NICHE_COMPONENTS: dict[str, tuple[BusinessComponent, ...]] = {
    "handwerk": (
        BusinessComponent("cost_calculator", "Cost Calculator", "Kunden wollen Orientierung vor dem Anruf."),
        BusinessComponent("before_after", "Before / After", "Beweis, dass Arbeit sichtbar ist."),
        BusinessComponent("projects", "Projects", "Konkrete Aufträge statt Wortlisten."),
        BusinessComponent("equipment", "Equipment Fleet", "Werkzeug & Fahrzeug bauen Vertrauen."),
        BusinessComponent("crew", "Crew", "Menschen hinter dem Handwerk."),
        BusinessComponent("whatsapp", "WhatsApp CTA", "Schnelle Anfrage ohne Formular-Friction."),
        BusinessComponent("service_area", "Service Area Map", "Lokale Reichweite."),
        BusinessComponent("emergency_call", "Priority Call", "Dringende Einsätze."),
    ),
    "dachreinigung": (
        BusinessComponent("cost_calculator", "Cost Calculator", "Dachfläche → grobe Orientierung."),
        BusinessComponent("before_after", "Before / After", "Moos → klar — der stärkste Beweis."),
        BusinessComponent("emergency_call", "Emergency Call", "Akute Abläufe / Regenperiode."),
        BusinessComponent("whatsapp", "WhatsApp CTA", "Fotos vom Dach schicken."),
        BusinessComponent("service_area", "Service Area Map", "Einsatzgebiet."),
        BusinessComponent("projects", "Projects", "Häuser in der Region."),
        BusinessComponent("equipment", "Equipment", "Höhe & Sicherheit."),
        BusinessComponent("crew", "Crew", "Team auf dem Dach."),
    ),
    "restaurant": (
        BusinessComponent("reservation", "Online Reservation", "Tisch ohne Telefonwarteschleife."),
        BusinessComponent("menu", "Menu", "Heute essen — nicht nur lesen."),
        BusinessComponent("chef", "Chef / Kitchen", "Gesicht hinter dem Teller."),
        BusinessComponent("gallery", "Gallery", "Essen, Raum, Abendstimmung."),
        BusinessComponent("instagram", "Instagram", "Live-Atmosphäre."),
        BusinessComponent("reviews", "Reviews", "Social proof."),
        BusinessComponent("events", "Events", "Private Abende / Groups."),
    ),
    "psychology": (
        BusinessComponent("first_consultation", "First Consultation", "Niedrige Einstiegshürde."),
        BusinessComponent("session_calendar", "Session Calendar", "Online- oder Praxis-Termin."),
        BusinessComponent("directions", "Therapy Directions", "Klarheit über Methode."),
        BusinessComponent("emergency_contact", "Emergency Contact", "Verantwortung & Grenzen."),
        BusinessComponent("faq", "FAQ", "Ablauf, Kosten, Schweigepflicht."),
        BusinessComponent("reviews", "Reviews", "Vertrauen — Demo-gekennzeichnet."),
        BusinessComponent("map", "Map", "Praxis finden."),
    ),
    "law": (
        BusinessComponent("practice_areas", "Practice Areas", "Klarheit über Schwerpunkte."),
        BusinessComponent("appointment", "Appointment", "Erstgespräch."),
        BusinessComponent("team", "Team", "Anwälte mit Gesicht."),
        BusinessComponent("cases", "Selected Matters", "Erfahrung ohne Sensationsjournalismus."),
        BusinessComponent("documents", "Documents", "Was mitbringen."),
        BusinessComponent("faq", "FAQ", "Kosten & Ablauf."),
    ),
    "dental": (
        BusinessComponent("booking", "Online Booking", "Termin ohne Telefon."),
        BusinessComponent("doctors", "Doctors", "Team der Praxis."),
        BusinessComponent("services", "Services", "Leistungen klar."),
        BusinessComponent("insurance", "Insurance Info", "Kasse / Privat."),
        BusinessComponent("gallery", "Practice Gallery", "Räume = Vertrauen."),
        BusinessComponent("faq", "FAQ", "Angstpatienten & Ablauf."),
    ),
    "beauty": (
        BusinessComponent("booking", "Online Booking", "Termin ist der CTA."),
        BusinessComponent("treatments", "Treatments", "Leistungen mit Preisrahmen."),
        BusinessComponent("gallery", "Look Gallery", "Ergebnisse & Atmosphäre."),
        BusinessComponent("instagram", "Instagram", "Social proof."),
        BusinessComponent("team", "Stylists", "Personen hinter dem Look."),
    ),
    "fitness": (
        BusinessComponent("membership", "Membership / Plans", "Klarer Einstieg."),
        BusinessComponent("booking", "Session Booking", "PT & Kurse."),
        BusinessComponent("coaches", "Coaches", "Gesichter."),
        BusinessComponent("gallery", "Studio Gallery", "Raum & Energie."),
        BusinessComponent("faq", "FAQ", "Probe & Preise."),
    ),
    "auto": (
        BusinessComponent("booking", "Service Booking", "Termin für Werkstatt."),
        BusinessComponent("services", "Services", "Diagnose bis Reifen."),
        BusinessComponent("fleet", "Fleet / Shop Floor", "Ausstattung."),
        BusinessComponent("whatsapp", "WhatsApp", "Foto vom Schaden."),
        BusinessComponent("reviews", "Reviews", "Lokales Vertrauen."),
    ),
    "realestate": (
        BusinessComponent("listings", "Listings", "Objekte im Fokus."),
        BusinessComponent("inquiry", "Inquiry Form", "Besichtigung anfragen."),
        BusinessComponent("map", "Area Map", "Lage verstehen."),
        BusinessComponent("team", "Agents", "Makler mit Gesicht."),
        BusinessComponent("valuation", "Valuation CTA", "Immobilie bewerten."),
    ),
    "commerce_store": (
        BusinessComponent("wishlist", "Wishlist", "Moderner Shop-Standard."),
        BusinessComponent("recently_viewed", "Recently Viewed", "Rückkehrpfad."),
        BusinessComponent("recommendations", "Recommendations", "Warenkorb-Wert."),
        BusinessComponent("reviews", "Reviews", "Kaufvertrauen."),
        BusinessComponent("shipping", "Shipping", "Klarheit vor Checkout."),
        BusinessComponent("returns", "Returns", "Risiko senken."),
        BusinessComponent("compare", "Product Comparison", "Entscheidungshilfe."),
        BusinessComponent("bundles", "Bundles", "AOV."),
        BusinessComponent("categories", "Categories", "Navigation."),
    ),
}

_DEFAULT_COMPONENTS = (
    BusinessComponent("contact_form", "Contact Form", "Kern-CTA."),
    BusinessComponent("whatsapp", "WhatsApp", "Schneller Kanal."),
    BusinessComponent("map", "Map", "Lokalität."),
    BusinessComponent("reviews", "Reviews", "Social proof (Demo-label)."),
    BusinessComponent("faq", "FAQ", "Einwände vor dem Anruf."),
    BusinessComponent("gallery", "Gallery", "Visueller Beweis."),
)


def detect_subniche(
    niche_id: str,
    *,
    text: str = "",
    services: list[str] | tuple[str, ...] = (),
) -> tuple[str, str, str]:
    """Return (subniche_id, label, atmosphere)."""
    blob = " ".join(
        [
            niche_id or "",
            text or "",
            " ".join(str(s) for s in services),
        ]
    ).lower()
    niche = (niche_id or "").lower()

    niche_groups: dict[str, tuple[str, ...]] = {
        "psychology": ("cbt", "anxiety", "family_psy", "child_psy", "online_psy", "emdr"),
        "restaurant": ("italian", "sushi", "burger", "cafe", "pizza", "steak", "vegan"),
        "handwerk": ("bathroom", "kitchen", "paint", "roof"),
        "dachreinigung": ("roof",),
        "auto": ("tires", "detailing", "body", "dealership"),
    }
    preferred = niche_groups.get(niche, tuple(_SUBNICHE_HINTS.keys()))

    for key in preferred:
        words, sid, label, atm = _SUBNICHE_HINTS[key]
        if any(w in blob for w in words):
            return sid, label, atm

    # Global fallback scan
    for key, (words, sid, label, atm) in _SUBNICHE_HINTS.items():
        if any(w in blob for w in words):
            return sid, label, atm

    defaults = {
        "psychology": ("general_therapy", "Psychologische Beratung", "calm_minimal"),
        "restaurant": ("bistro", "Restaurant", "warm_evening"),
        "handwerk": ("general_craft", "Handwerk & Renovierung", "craftsman_clean"),
        "dachreinigung": ("roof_cleaning", "Dachreinigung", "outdoor_trust"),
        "dental": ("general_dental", "Zahnarztpraxis", "clinic_trust"),
        "law": ("general_law", "Rechtsberatung", "corporate_trust"),
        "beauty": ("salon", "Beauty Studio", "soft_premium"),
        "fitness": ("studio", "Fitness", "energy_clean"),
        "auto": ("workshop", "Autowerkstatt", "industrial"),
        "cleaning": ("residential_cleaning", "Reinigung", "fresh_clean"),
        "realestate": ("agency", "Immobilien", "luxury_light"),
    }
    return defaults.get(niche, ("general", niche or "Business", "modern_eu"))


def recommend_components(
    niche_id: str,
    *,
    subniche_id: str = "",
    site_jobs: list[str] | tuple[str, ...] = (),
    is_store: bool = False,
) -> tuple[BusinessComponent, ...]:
    if is_store:
        base = list(_NICHE_COMPONENTS.get("commerce_store", _DEFAULT_COMPONENTS))
    else:
        base = list(_NICHE_COMPONENTS.get((niche_id or "").lower(), _DEFAULT_COMPONENTS))

    jobs = {str(j).lower() for j in site_jobs}
    extra: list[BusinessComponent] = []
    if "booking" in jobs or "termin" in jobs or "reserv" in jobs:
        extra.append(
            BusinessComponent("booking", "Booking", "Site job requires scheduling.")
        )
    if "sell" in jobs or "shop" in jobs or "katalog" in jobs:
        extra.append(
            BusinessComponent("catalog", "Catalog / Offers", "Site job includes selling.")
        )
    if "portfolio" in jobs or "galerie" in jobs:
        extra.append(
            BusinessComponent("portfolio", "Portfolio", "Work must be visible.")
        )

    # Subniche tweaks
    sid = (subniche_id or "").lower()
    if sid in ("roof_cleaning", "bathroom", "kitchen", "painting") and not any(
        c.id == "before_after" for c in base
    ):
        extra.append(
            BusinessComponent("before_after", "Before / After", "Sub-niche needs visual proof.")
        )
    if sid in ("anxiety", "cbt", "emdr") and not any(c.id == "emergency_contact" for c in base):
        extra.append(
            BusinessComponent(
                "emergency_contact",
                "Crisis Boundaries",
                "Therapy sub-niche needs responsible framing.",
            )
        )

    seen = set()
    out: list[BusinessComponent] = []
    for c in base + extra:
        if c.id in seen:
            continue
        seen.add(c.id)
        out.append(c)
    return tuple(out)


def build_media_brief(niche_id: str, subniche_id: str, atmosphere: str) -> dict[str, str]:
    niche = (niche_id or "").lower()
    packs = {
        "handwerk": {
            "hero": "Meister on site with tools — real work, not stock smile",
            "gallery": "Projects: bathroom, kitchen, paint, floors",
            "video": "Timelapse renovation or drilling close-up",
            "before_after": "Worn room → finished room",
            "team": "Crew in workwear",
            "equipment": "Bosch/Makita/Milwaukee + branded van",
        },
        "dachreinigung": {
            "hero": "Technician on roof / moss removal",
            "gallery": "Roof surface, gutter, impregnation",
            "video": "Pressure wash timelapse",
            "before_after": "Mossy roof → clean roof",
            "team": "Height-safety crew",
            "equipment": "Lift, hoses, safety gear",
        },
        "restaurant": {
            "hero": "Signature dish or dining room evening light",
            "gallery": "Plates, kitchen, guests, interior",
            "video": "Plating or open kitchen",
            "before_after": "",
            "team": "Chef / front of house",
            "equipment": "Pass, wine, table setting",
        },
        "psychology": {
            "hero": "Calm practice room, soft daylight",
            "gallery": "Chair, window light, quiet details",
            "video": "Slow ambient room (no clinical coldness)",
            "before_after": "",
            "team": "Therapist portrait — trustworthy, warm",
            "equipment": "",
        },
        "dental": {
            "hero": "Modern clinic room, doctor with patient trust",
            "gallery": "Chair, equipment, reception",
            "video": "Gentle clinic atmosphere",
            "before_after": "Smile cases only if appropriate",
            "team": "Dentists & assistants",
            "equipment": "Modern dental unit",
        },
        "law": {
            "hero": "City / meeting / documents — serious calm",
            "gallery": "Office, negotiation, skyline",
            "video": "Quiet professional motion",
            "before_after": "",
            "team": "Attorneys",
            "equipment": "",
        },
        "beauty": {
            "hero": "Studio process / detail / atmosphere",
            "gallery": "Looks, tools, space",
            "video": "Treatment detail",
            "before_after": "Look transformations (demo-labeled)",
            "team": "Stylists",
            "equipment": "Station & tools",
        },
    }
    brief = dict(
        packs.get(
            niche,
            {
                "hero": f"Professional {niche or 'business'} scene — European studio 2026",
                "gallery": "Work, place, people, proof",
                "video": "Niche atmosphere loop if provider available",
                "before_after": "",
                "team": "People of the company",
                "equipment": "",
            },
        )
    )
    brief["atmosphere"] = atmosphere
    brief["subniche"] = subniche_id
    brief["local"] = "City landmarks / neighborhood only as supporting identity"
    return brief


def resolve_business_intelligence(
    *,
    niche_id: str,
    company_name: str = "",
    city: str = "",
    interview: dict[str, Any] | None = None,
    contacts: dict[str, Any] | None = None,
    is_store: bool = False,
) -> BusinessIntelligence:
    c = contacts if isinstance(contacts, dict) else {}
    iv = interview if isinstance(interview, dict) else {}
    if not iv and isinstance(c.get("business_interview"), dict):
        iv = c["business_interview"]

    text_blob = " ".join(
        str(x)
        for x in (
            iv.get("free_text"),
            iv.get("about"),
            iv.get("differentiator"),
            iv.get("wishes"),
            iv.get("dream_vision"),
            c.get("client_story"),
            c.get("why_choose_us"),
            c.get("dream_vision"),
            " ".join(str(s) for s in (c.get("services_list") or [])),
        )
        if x
    )
    services = c.get("services_list") or iv.get("top_services") or ()
    if isinstance(services, str):
        services = [s.strip() for s in services.split(",") if s.strip()]

    clarify = {}
    if isinstance(iv.get("clarify_answers"), dict):
        clarify = {str(k): str(v) for k, v in iv["clarify_answers"].items()}
    elif isinstance(c.get("clarify_answers"), dict):
        clarify = {str(k): str(v) for k, v in c["clarify_answers"].items()}

    # Clarifying answers can refine sub-niche (e.g. therapy_focus, cuisine_mood)
    refine_blob = text_blob
    if clarify.get("therapy_focus"):
        refine_blob += " " + clarify["therapy_focus"]
    if clarify.get("cuisine_mood"):
        refine_blob += " " + clarify["cuisine_mood"]
    if clarify.get("shop_type"):
        refine_blob += " " + clarify["shop_type"]
    if clarify.get("session_mode") == "online":
        refine_blob += " online"
    if clarify.get("property_type"):
        refine_blob += " " + clarify["property_type"]

    sid, slabel, atm = detect_subniche(niche_id, text=refine_blob, services=services)
    style = str(iv.get("style") or c.get("brand_style") or c.get("style") or "")
    if style:
        atm = style

    from app.factory.interview_clarify import (
        apply_clarify_to_components,
        apply_clarify_to_site_jobs,
        build_clarify_session,
        detect_business_scale,
        dream_influence,
    )

    jobs_raw = iv.get("site_jobs") or c.get("site_jobs") or ()
    if isinstance(jobs_raw, str):
        jobs = tuple(j.strip() for j in re.split(r"[,;|]", jobs_raw) if j.strip())
    else:
        jobs = tuple(str(j) for j in jobs_raw if str(j).strip())
    jobs = apply_clarify_to_site_jobs(jobs, clarify)

    scale = str(
        iv.get("business_scale")
        or c.get("business_scale")
        or detect_business_scale(
            text=text_blob, team=str(iv.get("team") or c.get("team_note") or ""), clarify_answers=clarify
        )
    )
    dream = str(iv.get("dream_vision") or c.get("dream_vision") or "")
    dream_sig = dream_influence(dream)

    # Dream Mode can lift atmosphere toward ambition
    if dream_sig.get("tone") == "luxury" and not style:
        atm = "luxury"
    elif dream_sig.get("ambition") == "category_leader" and atm in ("modern", "craftsman_clean"):
        atm = f"{atm}_aspirational"

    base_comps = recommend_components(
        niche_id, subniche_id=sid, site_jobs=jobs, is_store=is_store
    )
    wanted_ids = apply_clarify_to_components(
        [comp.id for comp in base_comps],
        niche_id=niche_id,
        answers=clarify,
        scale=scale,
    )
    # Rebuild component tuple preserving known labels; synthesize unknowns
    by_id = {comp.id: comp for comp in base_comps}
    extra_labels = {
        "delivery": ("Delivery", "Lieferung als Kernleistung."),
        "delivery_zones": ("Delivery Zones", "Einzugsgebiet klar zeigen."),
        "order_cta": ("Order CTA", "Bestellen ohne Reibung."),
        "reservation": ("Online Reservation", "Tischreservierung."),
        "personal_story": ("Personal Story", "Solo-Gesicht der Marke."),
        "multi_page": ("Multi-page Structure", "Mehr Seiten für Unternehmensumfang."),
        "locations": ("Locations", "Mehrere Standorte."),
        "franchise_story": ("Franchise Story", "Markensystem erklären."),
        "video_session": ("Video Sessions", "Online-Sitzungen."),
    }
    rebuilt: list[BusinessComponent] = []
    for cid in wanted_ids:
        if cid in by_id:
            rebuilt.append(by_id[cid])
        elif cid in extra_labels:
            lab, why = extra_labels[cid]
            rebuilt.append(BusinessComponent(cid, lab, why))
    components = tuple(rebuilt) or base_comps
    media = build_media_brief(niche_id, sid, atm)
    if clarify.get("session_mode") == "online":
        media["hero"] = "Calm home-office / soft light video-call atmosphere — not a clinic corridor"
        media["gallery"] = "Quiet details, notebook, window light"
    if clarify.get("delivery") == "yes":
        media["hero"] = media.get("hero", "") + " · delivery / packaging moment"
        media["gallery"] = (media.get("gallery") or "") + " · delivery packaging"

    who = str(
        iv.get("about")
        or c.get("who_is_company")
        or c.get("client_story")
        or f"{company_name or 'Unternehmen'} · {slabel}"
    )
    diff = str(
        iv.get("differentiator")
        or c.get("why_choose_us")
        or c.get("main_promise")
        or ""
    )
    from app.factory.de_export_text import resolve_differentiator

    diff = resolve_differentiator(
        niche_id=niche_id,
        city=city or "",
        raw=diff,
    )
    if dream_sig.get("ambition") == "category_leader" and dream:
        diff = f"{diff} · Vision: {dream[:120]}"
    clients = str(iv.get("clients_who") or c.get("clients_who") or "")
    trust = str(iv.get("trust") or f"Nachweisbare Arbeit · {slabel} · {city or 'lokal'}")

    people = str(iv.get("team") or c.get("team_note") or "Fachteam vor Ort")
    if scale == "solo":
        people = "Inhabergeführt — persönlicher Kontakt"
    elif scale == "franchise":
        people = "Markenteam · mehrere Standorte"
    elif scale == "company":
        people = people if "team" in people.lower() else "Fachteam mit klaren Rollen"

    model_bits = [sid, atm, scale]
    if "familie" in text_blob.lower() or "family" in text_blob.lower() or "bruder" in text_blob.lower():
        model_bits.append("family")
    if any(w in text_blob.lower() for w in ("premium", "nicht die günstig", "qualität")):
        model_bits.append("quality_over_price")
    if clarify.get("delivery") == "yes":
        model_bits.append("delivery")
    if clarify.get("session_mode") == "online":
        model_bits.append("online_first")
    business_model = "_".join(model_bits)

    session = build_clarify_session(
        niche_id=niche_id,
        answered=clarify,
        free_text=text_blob,
        team=str(iv.get("team") or ""),
        dream=dream,
        site_jobs=jobs,
    )
    tech = session.technical

    fp = hashlib.sha256(
        f"{niche_id}|{sid}|{company_name}|{city}|{diff}|{atm}|{scale}|{dream[:40]}".encode()
    ).hexdigest()[:20]

    return BusinessIntelligence(
        niche_id=(niche_id or "").lower(),
        subniche_id=sid,
        subniche_label=slabel,
        business_model=business_model,
        city=city or str(c.get("city") or ""),
        company_name=company_name or str(c.get("business_name") or ""),
        who=who,
        trust_why=trust,
        sells=str(iv.get("top_services") or ", ".join(services) or slabel),
        differentiator=diff,
        atmosphere=atm,
        people=people,
        projects_focus=str(iv.get("projects") or media.get("gallery") or ""),
        media_brief=media,
        components=components,
        site_jobs=jobs,
        style=style,
        clients_who=clients,
        fingerprint=fp,
        business_scale=scale,
        dream_vision=dream,
        dream_signals=dream_sig,
        clarify_answers=clarify,
        technical_decisions=tech,
    )


def write_business_intelligence(product_dir: Path, bi: BusinessIntelligence) -> Path:
    product_dir.mkdir(parents=True, exist_ok=True)
    path = product_dir / "business_intelligence.json"
    path.write_text(
        json.dumps(bi.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    # Human-readable owner brief
    md = product_dir / "BUSINESS_INTELLIGENCE.md"
    comps = "\n".join(f"- **{c.label}** — {c.why}" for c in bi.components)
    tech = bi.technical_decisions or {}
    md.write_text(
        f"""# Business Intelligence — {bi.company_name or bi.subniche_label}

Canon: Digital Business Creator

## Who
{bi.who}

## Sub-niche
{bi.subniche_label} (`{bi.subniche_id}`) · model `{bi.business_model}` · scale `{bi.business_scale}`

## Dream Mode
{bi.dream_vision or "—"}
Signals: {bi.dream_signals}

## Why trust
{bi.trust_why}

## Differentiator (Hero seed)
{bi.differentiator}

## Atmosphere
{bi.atmosphere}

## Business Components
{comps}

## Technical decisions (Factory-owned — not asked to the client)
{json.dumps(tech, ensure_ascii=False, indent=2)}

## Media brief
{json.dumps(bi.media_brief, ensure_ascii=False, indent=2)}
""",
        encoding="utf-8",
    )
    return path


__all__ = [
    "BusinessComponent",
    "BusinessIntelligence",
    "build_media_brief",
    "detect_subniche",
    "recommend_components",
    "resolve_business_intelligence",
    "write_business_intelligence",
]
