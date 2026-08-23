"""Typography Engine — niche-aware font pairing for Digital Creative Studio.

Psychology ≠ Auto ≠ Restaurant ≠ Law. Never one default stack for all niches.
Catalog lists Google Font families; pairs are curated for emotion + niche.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TypePair:
    id: str
    display: str
    body: str
    google_css_url: str
    niches: tuple[str, ...]
    emotions: tuple[str, ...]
    scale: str = "editorial"  # editorial | cinematic | compact | luxury
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display": self.display,
            "body": self.body,
            "google_css_url": self.google_css_url,
            "niches": list(self.niches),
            "emotions": list(self.emotions),
            "scale": self.scale,
            "notes": self.notes,
        }


def _css2(*families: str) -> str:
    """Build Google Fonts CSS2 URL from family= fragments."""
    q = "&".join(families)
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


# Catalog of modern Google Font families (target 150+; grow over time).
GOOGLE_FONT_CATALOG: tuple[str, ...] = (
    "Cormorant Garamond",
    "Playfair Display",
    "Fraunces",
    "Libre Baskerville",
    "Source Serif 4",
    "EB Garamond",
    "Cormorant",
    "Newsreader",
    "Instrument Serif",
    "DM Serif Display",
    "Lora",
    "Literata",
    "Spectral",
    "Cardo",
    "Bitter",
    "Josefin Slab",
    "Bodoni Moda",
    "Cinzel",
    "Marcellus",
    "Prata",
    "DM Sans",
    "Source Sans 3",
    "Manrope",
    "Inter",
    "Outfit",
    "Sora",
    "Figtree",
    "Plus Jakarta Sans",
    "Space Grotesk",
    "Syne",
    "Cabinet Grotesk",
    "General Sans",
    "Satoshi",
    "Neue Montreal",
    "Work Sans",
    "Karla",
    "Nunito Sans",
    "IBM Plex Sans",
    "Public Sans",
    "Albert Sans",
    "Onest",
    "Geist",
    "Schibsted Grotesk",
    "Bricolage Grotesque",
    "Unbounded",
    "Oswald",
    "Barlow Condensed",
    "Bebas Neue",
    "Archivo",
    "Archivo Narrow",
    "Rajdhani",
    "Exo 2",
    "Titillium Web",
    "Chakra Petch",
    "Orbitron",
    "JetBrains Mono",
    "IBM Plex Mono",
    "Instrument Sans",
    "Epilogue",
    "Urbanist",
    "Red Hat Display",
    "Red Hat Text",
    "Lexend",
    "Atkinson Hyperlegible",
    "Commissioner",
    "Geologica",
    "Hanken Grotesk",
    "Schibsted Grotesk",
    "Familjen Grotesk",
    "Young Serif",
    "Gloock",
    "Bodoni Moda",
    "Castoro",
    "Crimson Pro",
    "Libre Caslon Text",
    "Petrona",
    "Rozha One",
    "Abril Fatface",
    "Yeseva One",
    "Big Shoulders Display",
    "Anton",
    "Fjalla One",
    "Passion One",
    "Righteous",
    "Comfortaa",
    "Quicksand",
    "Poppins",
    "Montserrat",
    "Raleway",
    "Mulish",
    "Rubik",
    "Heebo",
    "Noto Sans",
    "Noto Serif",
    "PT Sans",
    "PT Serif",
    "Roboto Flex",
    "Roboto Serif",
    "Open Sans",
    "Fira Sans",
    "Canonical Sans",
    "Alegreya",
    "Alegreya Sans",
    "Vollkorn",
    "Zilla Slab",
    "Arvo",
    "Merriweather",
    "Crimson Text",
    "Old Standard TT",
    "Sorts Mill Goudy",
    "Italiana",
    "Poiret One",
    "Tenor Sans",
    "Jost",
    "Outfit",
    "Sora",
    "Manrope",
    "Figtree",
    "Onest",
    "Geist Mono",
    "Fragment Mono",
    "Recursive",
    "Spline Sans",
    "Spline Sans Mono",
    "Kode Mono",
    "Oxanium",
    "Audiowide",
    "Syncopate",
    "Teko",
    "Russo One",
    "Black Ops One",
    "Permanent Marker",
    "Caveat",
    "Kalam",
    "Patrick Hand",
    "Indie Flower",
    "Amatic SC",
    "Pacifico",
    "Great Vibes",
    "Pinyon Script",
    "Allura",
    "Dancing Script",
    "Sacramento",
    "Parisienne",
    "Alex Brush",
    "Tangerine",
    "Italianno",
    "Mr De Haviland",
    "Rouge Script",
    "Niconne",
    "Cookie",
    "Courgette",
    "Kaushan Script",
    "Satisfy",
    "Yellowtail",
    "Sofia Sans",
    "Anuphan",
    "Handjet",
    "Climate Crisis",
    "M Plus 1",
)


TYPE_PAIRS: tuple[TypePair, ...] = (
    TypePair(
        id="cormorant_source",
        display='"Cormorant Garamond", Georgia, serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Cormorant+Garamond:wght@500;600;700",
            "family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400",
        ),
        niches=("psychology", "dental", "beauty", "law"),
        emotions=("calm", "trust", "elegance", "organic"),
        scale="editorial",
        notes="Therapy / quiet care",
    ),
    TypePair(
        id="playfair_manrope",
        display='"Playfair Display", Georgia, serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Playfair+Display:wght@500;600;700",
            "family=Manrope:wght@400;500;600;700",
        ),
        niches=("law", "realestate", "fashion", "psychology"),
        emotions=("prestige", "luxury", "confidence", "editorial"),
        scale="luxury",
    ),
    TypePair(
        id="fraunces_dm",
        display='"Fraunces", Georgia, serif',
        body='"DM Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Fraunces:opsz,wght@9..144,500;9..144,600;9..144,700",
            "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700",
        ),
        niches=("restaurant", "beauty", "fashion"),
        emotions=("warmth", "energy", "boutique"),
        scale="editorial",
    ),
    TypePair(
        id="instrument_onest",
        display='"Instrument Serif", Georgia, serif',
        body='"Onest", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Instrument+Serif:ital@0;1",
            "family=Onest:wght@400;500;600;700",
        ),
        niches=("psychology", "photography", "creative"),
        emotions=("editorial", "minimal", "clarity"),
        scale="editorial",
    ),
    TypePair(
        id="syne_figtree",
        display='"Syne", "Segoe UI", system-ui, sans-serif',
        body='"Figtree", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Syne:wght@500;600;700;800",
            "family=Figtree:wght@400;500;600;700",
        ),
        niches=("technology", "creative", "saas"),
        emotions=("innovation", "energy", "confidence"),
        scale="cinematic",
    ),
    TypePair(
        id="space_grotesk_inter",
        display='"Space Grotesk", "Segoe UI", system-ui, sans-serif',
        body='"Inter", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Space+Grotesk:wght@500;600;700",
            "family=Inter:wght@400;500;600;700",
        ),
        niches=("computer", "it", "technology", "auto"),
        emotions=("innovation", "clarity", "corporate"),
        scale="compact",
    ),
    TypePair(
        id="oswald_source",
        display='"Oswald", "Arial Narrow", sans-serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Oswald:wght@500;600;700",
            "family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400",
        ),
        niches=("handwerk", "auto", "appliance", "energy"),
        emotions=("confidence", "energy", "corporate"),
        scale="compact",
    ),
    TypePair(
        id="libre_source",
        display='"Libre Baskerville", Georgia, serif',
        body='"Source Sans 3", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Libre+Baskerville:wght@400;700",
            "family=Source+Sans+3:ital,wght@0,400;0,600;0,700;1,400",
        ),
        niches=("law", "accounting", "dental"),
        emotions=("trust", "corporate", "clarity"),
        scale="editorial",
    ),
    TypePair(
        id="bodoni_jakarta",
        display='"Bodoni Moda", Georgia, serif',
        body='"Plus Jakarta Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Bodoni+Moda:opsz,wght@6..96,500;6..96,600;6..96,700",
            "family=Plus+Jakarta+Sans:wght@400;500;600;700",
        ),
        niches=("fashion", "beauty", "jewelry"),
        emotions=("luxury", "elegance", "boutique"),
        scale="luxury",
    ),
    TypePair(
        id="newsreader_public",
        display='"Newsreader", Georgia, serif',
        body='"Public Sans", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Newsreader:opsz,wght@6..72,500;6..72,600;6..72,700",
            "family=Public+Sans:wght@400;500;600;700",
        ),
        niches=("psychology", "law", "realestate"),
        emotions=("editorial", "magazine", "trust"),
        scale="editorial",
    ),
    TypePair(
        id="gloock_manrope",
        display='"Gloock", Georgia, serif',
        body='"Manrope", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Gloock",
            "family=Manrope:wght@400;500;600;700",
        ),
        niches=("psychology", "beauty", "creative"),
        emotions=("cinematic", "immersive", "prestige"),
        scale="cinematic",
    ),
    TypePair(
        id="bricolage_sora",
        display='"Bricolage Grotesque", "Segoe UI", system-ui, sans-serif',
        body='"Sora", "Segoe UI", system-ui, sans-serif',
        google_css_url=_css2(
            "family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600;12..96,700",
            "family=Sora:wght@400;500;600;700",
        ),
        niches=("creative", "saas", "technology"),
        emotions=("innovation", "energy", "modern"),
        scale="cinematic",
    ),
)


def catalog_size() -> int:
    return len(set(GOOGLE_FONT_CATALOG))


def list_pairs() -> list[TypePair]:
    return list(TYPE_PAIRS)


def resolve_type_pair(
    *,
    niche_id: str,
    emotion: str = "",
    package_id: str = "business",
    diversity_salt: str = "",
) -> TypePair:
    """Pick a type pair for niche + emotion. Never hardcode one global stack."""
    niche = (niche_id or "generic").strip().lower()
    emo = (emotion or "").strip().lower()
    pid = (package_id or "business").strip().lower()
    salt = (diversity_salt or "").strip()

    scored: list[tuple[int, TypePair]] = []
    for pair in TYPE_PAIRS:
        score = 1
        if niche in pair.niches:
            score += 12
        if emo and any(e in emo for e in pair.emotions):
            score += 8
        if pid == "premium" and pair.scale in ("luxury", "cinematic", "editorial"):
            score += 4
        if pid == "basic" and pair.scale == "compact":
            score += 3
        scored.append((score, pair))
    scored.sort(key=lambda x: (-x[0], x[1].id))
    top = [p for s, p in scored if s >= scored[0][0] - 4] or [scored[0][1]]
    idx = int(hashlib.sha256(f"{niche}|{emo}|{pid}|type|{salt}".encode()).hexdigest()[:8], 16)
    return top[idx % len(top)]


def type_pair_as_font_stacks(pair: TypePair) -> dict[str, str]:
    return {
        "typography_pair": pair.id,
        "font_display": pair.display,
        "font_body": pair.body,
        "google_css_url": pair.google_css_url,
        "type_scale": pair.scale,
    }
