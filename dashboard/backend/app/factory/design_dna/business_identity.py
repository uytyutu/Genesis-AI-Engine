"""Business Identity — root digital profile of a company (Studio Era).

Chain:
  Business Identity → Brand Book → Atmosphere → Reputation → Local Identity
  → Website → Store → Marketing

Not a page. The profile from which all digital surfaces are born.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.factory.design_dna.brand_book import BrandBook, resolve_brand_book


@dataclass(frozen=True)
class BusinessIdentity:
    """Full digital identity of a business — source for site/store/marketing."""

    brand_name: str
    niche_id: str
    package_id: str
    founded_year: int
    company_age_years: int
    mission: str
    core_services: tuple[str, ...]
    geography: str
    advantages: tuple[str, ...]
    values: tuple[str, ...]
    client_types: tuple[str, ...]
    price_segment: str
    brand_character: str
    team_size_label: str
    marketing_dna_stub: dict[str, Any]
    video_dna_stub: dict[str, Any]
    fingerprint: str
    demo: bool = True

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["core_services"] = list(self.core_services)
        d["advantages"] = list(self.advantages)
        d["values"] = list(self.values)
        d["client_types"] = list(self.client_types)
        d["chain"] = [
            "business_identity",
            "brand_book",
            "atmosphere",
            "reputation",
            "local_identity",
            "website",
            "store",
            "marketing",
        ]
        return d


_NICHE_IDENTITY: dict[str, dict[str, Any]] = {
    "handwerk": {
        "founded_year": 2019,
        "mission": "Haushalte entlasten — Montage und Reparatur ohne Chaos.",
        "services": (
            "Kleinreparaturen",
            "Möbel- / IKEA-Montage",
            "Lampen & Steckdosen-Check",
            "Streichen / Tapezieren",
            "Boden verlegen",
            "Sanitär-Kleinigkeiten",
            "Stundenweise Einsätze",
        ),
        "geography": "Berlin und Umland (Demo)",
        "advantages": (
            "Festpreis nach Aufmaß",
            "Termin oft innerhalb 24–48h",
            "Saubere Übergabe mit Fotodoku",
            "WhatsApp-Koordination",
        ),
        "values": ("Pünktlichkeit", "Transparenz", "Sorgfalt", "Respekt vor Wohnung"),
        "client_types": ("Mieter", "Eigentümer", "Büros", "Airbnbs"),
        "price_segment": "Mittel — stundenweise / Festpreis",
        "brand_character": "Reliable craftsman on call",
        "team_size_label": "Meister + 2–4 Monteure (Demo)",
        "marketing": {
            "audience": "Berliner Haushalte mit Sofortbedarf",
            "goal": "WhatsApp / Anruf → Termin",
            "emotion": "Entlastung",
            "pacing": "direkt",
            "platforms": ["Website", "Google", "WhatsApp"],
        },
        "video": {
            "camera": ["Handheld on site", "Detail tool shots"],
            "mood": "Warm daylight · work in progress",
            "music": "Soft pulse, no stock pep",
            "pacing": "Short cuts of real tasks",
            "required_scenes": [
                "Meister drilling",
                "Kitchen assembly",
                "Paint roller",
                "Finished room",
            ],
            "forbidden": ["Café", "Laptop stock", "Abstract gradients only"],
        },
    },
    "dachreinigung": {
        "founded_year": 2022,
        "mission": "Ein Dach, dem Hausbesitzer wieder vertrauen können.",
        "services": (
            "Dachreinigung",
            "Moosentfernung",
            "Imprägnierung",
            "Dachrinne",
            "Inspektion",
        ),
        "geography": "Nürnberg und Region (Fürth, Erlangen, Schwabach, Bamberg)",
        "advantages": (
            "Transparente Festpreise",
            "Höhenarbeit mit Sicherung",
            "Fotodokumentation",
            "Lokaler Ansprechpartner",
        ),
        "values": ("Sicherheit", "Präzision", "Ehrlichkeit", "Handwerk"),
        "client_types": ("Hausbesitzer", "Verwaltungen", "Eigentümergemeinschaften"),
        "price_segment": "Mittel bis Premium (klar kalkuliert)",
        "brand_character": "Craftsman + Guardian — ruhig, präzise, lokal",
        "team_size_label": "4–6 Personen (Demo)",
        "marketing": {
            "audience": "Hausbesitzer 35–65 in der Region Nürnberg",
            "goal": "Anfrage / Festpreis-Angebot",
            "emotion": "Sicherheit und Stolz auf das Zuhause",
            "pacing": "langsam · vertrauensbildend",
            "platforms": ["Meta", "Google", "Website Hero"],
        },
        "video": {
            "camera": ["Drone", "Macro", "Handheld"],
            "mood": "Calm after storm",
            "music": "Ambient · light piano",
            "pacing": "Slow",
            "required_scenes": [
                "Roof",
                "Worker harness",
                "Water / washing",
                "Before/After",
                "Drone",
            ],
            "forbidden": ["Office", "Laptop", "Coffee", "Coworking", "Café"],
        },
    },
    "zaunbau": {
        "founded_year": 2019,
        "mission": "Grenzen, die Halt und Haltung geben.",
        "services": ("Zaunbau", "Tore", "Reparatur", "Beratung"),
        "geography": "Metropolregion Nürnberg",
        "advantages": ("Präzise Montage", "Klare Materialien", "Terminplanung"),
        "values": ("Stabilität", "Klarheit", "Handwerk"),
        "client_types": ("Privathaushalte", "Gewerbe"),
        "price_segment": "Mittel",
        "brand_character": "Builder + Guardian",
        "team_size_label": "3–5 Personen (Demo)",
        "marketing": {
            "audience": "Grundstücksbesitzer",
            "goal": "Angebot anfordern",
            "emotion": "Ordentliche Klarheit",
            "pacing": "fest · klar",
            "platforms": ["Meta", "Website"],
        },
        "video": {
            "camera": ["Static", "Handheld"],
            "mood": "Craft dusk",
            "music": "Minimal acoustic",
            "pacing": "Measured",
            "required_scenes": ["Fence line", "Posts", "Gate", "Workshop"],
            "forbidden": ["Café", "Office", "Laptop"],
        },
    },
    "gartenpflege": {
        "founded_year": 2018,
        "mission": "Ein Garten, der atmet — und gepflegt bleibt.",
        "services": ("Rasenpflege", "Heckenschnitt", "Beete", "Jahrespflege"),
        "geography": "Nürnberg und Umland",
        "advantages": ("Saisonpläne", "Sorgfältige Arbeit", "Vorher/Nachher"),
        "values": ("Ruhe", "Natur", "Sorgfalt"),
        "client_types": ("Familien", "Hausbesitzer"),
        "price_segment": "Mittel",
        "brand_character": "Gardener + Steward",
        "team_size_label": "3–4 Personen (Demo)",
        "marketing": {
            "audience": "Gartenbesitzer",
            "goal": "Pflegevertrag / Termin",
            "emotion": "Lebendige Ordnung",
            "pacing": "weich · atmend",
            "platforms": ["Meta", "Website"],
        },
        "video": {
            "camera": ["Static", "Macro"],
            "mood": "Morning dew",
            "music": "Soft nature ambient",
            "pacing": "Gentle",
            "required_scenes": ["Garden", "Tools", "Hedge", "Lawn"],
            "forbidden": ["Spa stock", "Café", "Office"],
        },
    },
}


def resolve_business_identity(
    *,
    business_name: str,
    niche_id: str,
    package_id: str = "business",
    city: str = "",
    diversity_salt: str = "",
) -> BusinessIdentity:
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "business").strip().lower() or "business"
    name = (business_name or "Business").strip() or "Business"
    raw = _NICHE_IDENTITY.get(niche) or {
        "founded_year": 2020,
        "mission": "Klar. Vertrauenswürdig. Vor Ort.",
        "services": ("Beratung", "Service"),
        "geography": city or "Deutschland",
        "advantages": ("Transparenz", "Lokaler Service"),
        "values": ("Vertrauen", "Klarheit"),
        "client_types": ("Privatkunden",),
        "price_segment": "Mittel",
        "brand_character": "Expert + Guide",
        "team_size_label": "Kleinteam (Demo)",
        "marketing": {
            "audience": "Lokale Kunden",
            "goal": "Kontakt",
            "emotion": "Vertrauen",
            "pacing": "ruhig",
            "platforms": ["Website"],
        },
        "video": {
            "camera": ["Static"],
            "mood": "Clear daylight",
            "music": "Soft ambient",
            "pacing": "Steady",
            "required_scenes": ["Workplace", "People at work"],
            "forbidden": ["Café", "Coworking", "Laptop stock"],
        },
    }
    founded = int(raw["founded_year"])
    age = max(1, 2026 - founded)
    geo = str(raw["geography"])
    if city and city.lower() not in geo.lower():
        geo = f"{city} — {geo}"
    fp = hashlib.sha256(
        f"{name}|{niche}|{pid}|{founded}|{diversity_salt}".encode()
    ).hexdigest()[:24]
    return BusinessIdentity(
        brand_name=name,
        niche_id=niche,
        package_id=pid,
        founded_year=founded,
        company_age_years=age,
        mission=str(raw["mission"]),
        core_services=tuple(raw["services"]),
        geography=geo,
        advantages=tuple(raw["advantages"]),
        values=tuple(raw["values"]),
        client_types=tuple(raw["client_types"]),
        price_segment=str(raw["price_segment"]),
        brand_character=str(raw["brand_character"]),
        team_size_label=str(raw["team_size_label"]),
        marketing_dna_stub=dict(raw["marketing"]),
        video_dna_stub=dict(raw["video"]),
        fingerprint=fp,
        demo=True,
    )


def write_business_identity(product_dir: Path, identity: BusinessIdentity) -> Path:
    product_dir.mkdir(parents=True, exist_ok=True)
    path = product_dir / "business_identity.json"
    path.write_text(
        json.dumps(identity.as_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def brand_book_from_identity(
    identity: BusinessIdentity,
    *,
    diversity_salt: str = "",
) -> BrandBook:
    """Brand Book is invented from Business Identity (same niche/name/package)."""
    return resolve_brand_book(
        business_name=identity.brand_name,
        niche_id=identity.niche_id,
        package_id=identity.package_id,
        diversity_salt=diversity_salt or identity.fingerprint,
        city=identity.geography.split("—")[0].strip()
        if "—" in identity.geography
        else identity.geography.split()[0],
    )


__all__ = [
    "BusinessIdentity",
    "brand_book_from_identity",
    "resolve_business_identity",
    "write_business_identity",
]
