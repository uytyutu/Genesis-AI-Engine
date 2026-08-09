"""Brand Book — single source of truth for Factory personality.

Not a PDF. Not decoration. Every visual/copy decision should flow from this pack
so a roof company cannot accidentally become a café, salon, or SaaS skin.

Sprint 1: invent → constrain DNA / type / atmosphere / moodboard → persist JSON+TXT.
Sprint 2: Atmosphere Pack consumes this Book as page director (scene layers, media briefs).
Sprint 3: Reputation Pack + Media Truth — beauty without profession proof is not quality.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field, replace
from typing import Any

from app.factory.design_dna.dna import DesignDNA


@dataclass(frozen=True)
class BrandPalette:
    """Named swatches + concrete hexes Factory can apply."""

    names: tuple[str, ...]
    accent_hex: str
    surface_hex: str
    ink_hex: str
    secondary_hex: str = ""
    highlight_hex: str = ""

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MediaDNA:
    """Visual proof of profession — beauty alone is never enough.

    Media Truth (all must be yes, else REBUILD):
      1. Beautiful?
      2. Fits the brand?
      3. Matches the profession?
    """

    required: tuple[str, ...]
    preferred: tuple[str, ...]
    forbidden: tuple[str, ...]
    hero_proof: str  # "What does this company live every day?"
    profession_keywords: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "required": list(self.required),
            "preferred": list(self.preferred),
            "forbidden": list(self.forbidden),
            "hero_proof": self.hero_proof,
            "profession_keywords": list(self.profession_keywords),
            "rule": (
                "No photo/illustration/video ships unless it proves profession, "
                "brand personality, and company story. Beauty without meaning ≠ quality."
            ),
        }

    def as_text(self) -> str:
        req = "\n".join(f"✔ {x}" for x in self.required)
        pref = "\n".join(f"✔ {x}" for x in self.preferred)
        ban = "\n".join(f"✖ {x}" for x in self.forbidden)
        return f"""MEDIA DNA
Required
{req}

Preferred
{pref}

Forbidden
{ban}

Hero Proof
{self.hero_proof}
"""


@dataclass(frozen=True)
class BrandBook:
    """Company personality before any HTML exists."""

    brand_name: str
    niche_id: str
    package_id: str
    positioning: str
    archetype_primary: str
    archetype_secondary: str
    brand_promise: str
    core_emotion: str
    secondary_emotion: str
    tone: tuple[str, ...]
    visual_style: str
    visual_metaphor: str
    photography: tuple[str, ...]
    forbidden: tuple[str, ...]
    motion_language: str
    motion_token: str  # soft | business | premium — DesignDNA.motion
    palette: BrandPalette
    typography_display: str
    typography_body: str
    typography_pair_id: str
    typography_emotion: str
    icon_style: str
    border_radius_px: int
    shadow_style: str
    glass_level: str  # low | medium | high
    texture: tuple[str, ...]
    scene_language: tuple[str, ...]
    cta_style: str
    trust_strategy: tuple[str, ...]
    atmosphere_mode: str
    dna_style: str
    dna_palette_family: str
    hero_concept: str
    fingerprint: str
    media_dna: MediaDNA
    city_hint: str = ""

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["palette"] = self.palette.as_dict()
        d["media_dna"] = self.media_dna.as_dict()
        d["tone"] = list(self.tone)
        d["photography"] = list(self.photography)
        d["forbidden"] = list(self.forbidden)
        d["texture"] = list(self.texture)
        d["scene_language"] = list(self.scene_language)
        d["trust_strategy"] = list(self.trust_strategy)
        return d

    def as_text(self) -> str:
        """Human-readable Brand Book (owner / studio preview)."""
        pal = ", ".join(self.palette.names)
        tone = "\n".join(f"  {t}" for t in self.tone)
        photo = "\n".join(f"  {p}" for p in self.photography)
        forbid = "\n".join(f"  {f}" for f in self.forbidden)
        tex = "\n".join(f"  {t}" for t in self.texture)
        scene = "\n".join(f"  {s}" for s in self.scene_language)
        trust = "\n".join(f"  {t}" for t in self.trust_strategy)
        return f"""BRAND BOOK
Brand Name
{self.brand_name}

Positioning
{self.positioning}

Brand Archetype
{self.archetype_primary}
+
{self.archetype_secondary}

Brand Promise
{self.brand_promise}

Core Emotion
{self.core_emotion}

Secondary Emotion
{self.secondary_emotion}

Tone of Voice
{tone}

Visual Style
{self.visual_style}

Visual Metaphor
{self.visual_metaphor}

Photography
{photo}

Forbidden (never generate)
{forbid}

Motion
{self.motion_language}

Palette
{pal}
Accent {self.palette.accent_hex}
Surface {self.palette.surface_hex}
Ink {self.palette.ink_hex}

Typography
{self.typography_display}
+
{self.typography_body}
({self.typography_pair_id})

Icon Style
{self.icon_style}

Border Radius
{self.border_radius_px} px

Shadow Style
{self.shadow_style}

Glass Level
{self.glass_level}

Texture
{tex}

Scene Language
{scene}

CTA Style
{self.cta_style}

Trust Strategy
{trust}

Atmosphere Mode
{self.atmosphere_mode}

{self.media_dna.as_text()}
Fingerprint
{self.fingerprint}
"""


# ---------------------------------------------------------------------------
# Niche character library — personality, not generic industry skins
# ---------------------------------------------------------------------------

_CRAFT_FORBIDDEN = (
    "cafe",
    "restaurant interior",
    "beauty salon",
    "spa",
    "saas dashboard",
    "startup office",
    "coworking",
    "stock handshake",
    "generic purple gradient",
    "luxury champagne cliché without craft proof",
    "laptop",
    "coffee",
    "abstract business",
    "office meeting",
)

_MEDIA_DNA: dict[str, MediaDNA] = {
    "dachreinigung": MediaDNA(
        required=("Roof", "Water", "Sky", "Drone", "Height", "Worker", "Equipment"),
        preferred=("Morning light", "Clouds", "Wet tiles", "Family house", "Gutter", "Safety harness"),
        forbidden=(
            "Café",
            "Restaurant",
            "Office",
            "Beauty",
            "Laptop",
            "Coworking",
            "Abstract business",
            "Coffee smile stock",
        ),
        hero_proof=(
            "Worker in safety harness cleaning a wet roof after rain — "
            "not a pretty empty roof, not a café."
        ),
        profession_keywords=(
            "roof",
            "dach",
            "tile",
            "ziegel",
            "gutter",
            "rinne",
            "moss",
            "moos",
            "harness",
            "ladder",
            "drone",
            "height",
            "water",
            "rain",
        ),
    ),
    "zaunbau": MediaDNA(
        required=("Fence", "Posts", "Ground", "Material", "Edge", "Craft"),
        preferred=("Dusk light", "Metal", "Wood grain", "Gate", "Workshop"),
        forbidden=("Café", "Restaurant", "Office", "Beauty", "Laptop", "Coworking"),
        hero_proof="Fence line being set or finished at property edge — craft in progress.",
        profession_keywords=("fence", "zaun", "post", "gate", "rail", "metal", "wood"),
    ),
    "gartenpflege": MediaDNA(
        required=("Garden", "Greenery", "Tools", "Outdoor work", "Daylight"),
        preferred=("Dew", "Hedge", "Lawn", "Beds", "Morning"),
        forbidden=("Café", "Spa stones", "Tropical resort", "Office", "Laptop"),
        hero_proof="Gardener at real outdoor work — hedge, lawn, or bed care.",
        profession_keywords=("garden", "garten", "hedge", "lawn", "rasen", "plant", "leaf"),
    ),
    "handwerk": MediaDNA(
        required=("Workshop", "Tools", "Material", "Hands at work"),
        preferred=("Work light", "Bench", "Craft detail"),
        forbidden=("Café", "Office", "Beauty", "Laptop", "Coworking"),
        hero_proof="Craftsperson at the bench or on site with tools — daily work, not décor.",
        profession_keywords=("workshop", "tool", "craft", "handwerk", "bench", "material"),
    ),
    "psychology": MediaDNA(
        required=("Calm room", "Natural light", "Listening space"),
        preferred=("Soft furniture", "Quiet detail", "Warm daylight"),
        forbidden=("Café latte stock", "Party", "Gym", "Laptop hustle", "Abstract neon"),
        hero_proof="Quiet consulting room with natural light — attentive presence, not coffee décor.",
        profession_keywords=("therapy", "calm", "room", "listen", "cabinet", "praxis"),
    ),
    "auto": MediaDNA(
        required=("Workshop", "Lift", "Tools", "Mechanic at work"),
        preferred=("Parts", "Engine bay", "Service bay light"),
        forbidden=("Parking lot glamour only", "Café", "Office", "Laptop"),
        hero_proof="Mechanic working under/over a vehicle with lift and tools — daily garage life.",
        profession_keywords=("garage", "lift", "mechanic", "engine", "service", "werkstatt"),
    ),
}

_DEFAULT_MEDIA = MediaDNA(
    required=("Real workplace", "People at craft", "Daylight"),
    preferred=("Local place", "Honest detail"),
    forbidden=("Café", "Coworking", "Abstract business", "Laptop stock", "Beauty salon"),
    hero_proof="A frame that answers: what does this company live every day?",
    profession_keywords=("work", "local", "craft", "service"),
)

# Extend Media DNA for Commercial Reality exemplars (after craft entries above)
_MEDIA_DNA.update(
    {
        "psychology": MediaDNA(
            required=("Quiet room", "Daylight", "Soft space", "Human pace"),
            preferred=("Empty chair with air", "Window light", "Paper", "Calm hands"),
            forbidden=("Neon spa", "Yoga beach stock", "Purple wellness", "Crystal cliché"),
            hero_proof="A quiet chamber where the first breath feels slower — not a spa brochure.",
            profession_keywords=("therapy", "praxis", "ruhe", "gespräch", "raum"),
        ),
        "restaurant": MediaDNA(
            required=("Evening table", "Food craft", "Warm light", "Courtyard or dining room"),
            preferred=("Hands plating", "Steam", "Wine glass", "Long table"),
            forbidden=("Fast-food plastic", "Neon menu", "Stock handshake", "Empty white plate only"),
            hero_proof="An Italian courtyard evening — appetite and belonging, not a PDF menu.",
            profession_keywords=("küche", "tisch", "abend", "hof", "pasta", "reservierung"),
        ),
        "law": MediaDNA(
            required=("Quiet facade", "Order", "Clear light", "Architecture"),
            preferred=("Empty conference table", "Paper stack neat", "Stone detail"),
            forbidden=("Gavel stock", "Scales of justice cliché", "Angry courtroom"),
            hero_proof="Silence, order, control — authority without theater.",
            profession_keywords=("kanzlei", "recht", "vertrag", "beratung", "ordnung"),
        ),
        "beauty": MediaDNA(
            required=("Atelier light", "Hands at work", "Quiet mirror", "Ritual space"),
            preferred=("Product detail", "Soft tools", "Calm before appointment"),
            forbidden=("Neon salon", "Pink glitter stock", "Waiting-room chair row"),
            hero_proof="A beauty ritual room — not a noisy salon corridor.",
            profession_keywords=("salon", "schnitt", "farbe", "ritual", "atelier"),
        ),
    }
)

_NICHE_BOOKS: dict[str, dict[str, Any]] = {
    "dachreinigung": {
        "positioning": "Premium Roof Care",
        "archetype_primary": "The Craftsman",
        "archetype_secondary": "The Guardian",
        "brand_promise": "Nach dem Regen sieht das Dach wieder neu aus.",
        "core_emotion": "Erleichterung",
        "secondary_emotion": "Stolz auf das eigene Zuhause",
        "tone": ("Ruhig", "Präzise", "Ehrlich", "Kompetent"),
        "visual_style": "Industrial Modern",
        "visual_metaphor": "Frischer Regen nach dem Sturm — nasse Ziegel, klarer Himmel",
        "photography": (
            "Echte Dächer",
            "Morgensonne nach Regen",
            "Wassertropfen",
            "Arbeiter in Schutzkleidung",
            "Luftaufnahmen",
        ),
        "forbidden": _CRAFT_FORBIDDEN
        + ("nail salon", "coffee shop", "yoga studio", "tech landing"),
        "motion_language": "Langsam · Flüssig · Präzise",
        "motion_token": "premium",
        "palette": BrandPalette(
            names=("Slate", "Steel", "Sky Blue", "Warm White", "Safety Orange"),
            accent_hex="#3b82c4",
            secondary_hex="#64748b",
            highlight_hex="#ea580c",
            surface_hex="#f8fafc",
            ink_hex="#0f172a",
        ),
        "typography_display": "Manrope",
        "typography_body": "IBM Plex Sans",
        "typography_pair_id": "manrope_ibm_plex_industrial",
        "typography_emotion": "confidence",
        "icon_style": "Outline Industrial",
        "border_radius_px": 12,
        "shadow_style": "Soft Deep",
        "glass_level": "medium",
        "texture": ("Beton", "Schiefer", "Wasser"),
        "scene_language": ("Sky", "Height", "Light", "Wind", "Rain"),
        "cta_style": "Große Buttons · Viel Abstand · Keine Aggressivität",
        "trust_strategy": (
            "Vorher/Nachher",
            "Zertifikate",
            "Fahrzeuge",
            "Team",
            "Versicherung",
            "Garantie",
        ),
        "atmosphere_mode": "cinematic",
        "dna_style": "tech_precision",
        "dna_palette_family": "slate_steel",
        "hero_concept": "roof_after_rain",
        "media_dna": _MEDIA_DNA["dachreinigung"],
    },
    "psychology": {
        "positioning": "Ruhiger Schutzraum",
        "archetype_primary": "The Guide",
        "archetype_secondary": "The Listener",
        "brand_promise": "Ein Ort, an dem es ruhiger wird.",
        "core_emotion": "Ruhe",
        "secondary_emotion": "Sicherheit",
        "tone": ("Leise", "Klar", "Warm", "Ohne Floskeln"),
        "visual_style": "Editorial Calm",
        "visual_metaphor": "Weiches Morgenlicht in einem stillen Raum",
        "photography": (
            "Stillleben Raum",
            "Tageslicht",
            "Leere Stühle mit Abstand",
            "Papier und Stift",
            "Fensterlicht",
        ),
        "forbidden": _CRAFT_FORBIDDEN
        + ("neon spa", "stock yoga beach", "purple wellness", "crystal cliché"),
        "motion_language": "Sehr langsam · Atmung · Wenig Bewegung",
        "motion_token": "soft",
        "palette": BrandPalette(
            names=("Warm Paper", "Sage", "Stone", "Ink"),
            accent_hex="#5b7c6e",
            secondary_hex="#8a9a90",
            highlight_hex="#c9b8a6",
            surface_hex="#f7f4ef",
            ink_hex="#1c1916",
        ),
        "typography_display": "Cormorant Garamond",
        "typography_body": "Source Serif 4",
        "typography_pair_id": "editorial_calm",
        "typography_emotion": "clarity",
        "icon_style": "Outline Soft",
        "border_radius_px": 4,
        "shadow_style": "Barely",
        "glass_level": "low",
        "texture": ("Paper", "Linen", "Wood grain soft"),
        "scene_language": ("Light", "Space", "Silence", "Breath"),
        "cta_style": "Ein ruhiger Link · Kein Druck",
        "trust_strategy": ("Transparente Honorare", "Ablauf", "Vertraulichkeit"),
        "atmosphere_mode": "atelier",
        "dna_style": "modern_clinical",
        "dna_palette_family": "sage_mist",
        "hero_concept": "quiet_chamber",
        "media_dna": _MEDIA_DNA["psychology"],
    },
    "restaurant": {
        "positioning": "Italienischer Abend",
        "archetype_primary": "The Host",
        "archetype_secondary": "The Craftsman",
        "brand_promise": "Ein Abend im italienischen Hof.",
        "core_emotion": "Wärme",
        "secondary_emotion": "Appetit und Zugehörigkeit",
        "tone": ("Warm", "Sinnlich", "Ehrlich", "Einladend"),
        "visual_style": "Culinary Atmosphere",
        "visual_metaphor": "Abendlicht über dem Hof — lange Tafel, leises Gläserklingen",
        "photography": (
            "Abendlicht",
            "Gedeckter Tisch",
            "Frische Zutaten",
            "Hände in der Küche",
            "Hof / Terrasse",
        ),
        "forbidden": _CRAFT_FORBIDDEN
        + ("fast food plastic", "neon menu board", "stock handshake"),
        "motion_language": "Langsam · Kerzenflackern · Dampf",
        "motion_token": "premium",
        "palette": BrandPalette(
            names=("Terracotta", "Olive", "Candle", "Night Ink"),
            accent_hex="#c45c26",
            secondary_hex="#3d4a32",
            highlight_hex="#e8b86d",
            surface_hex="#1c1410",
            ink_hex="#faf6f1",
        ),
        "typography_display": "Playfair Display",
        "typography_body": "Source Sans 3",
        "typography_pair_id": "playfair_source_culinary",
        "typography_emotion": "warmth",
        "icon_style": "Soft Line",
        "border_radius_px": 2,
        "shadow_style": "Deep Warm",
        "glass_level": "medium",
        "texture": ("Linen", "Wood", "Ceramic"),
        "scene_language": ("Evening", "Table", "Courtyard", "Steam"),
        "cta_style": "Reservierung · Groß · Warm",
        "trust_strategy": ("Allergene klar", "Reservierung", "Küche sichtbar"),
        "atmosphere_mode": "cinematic",
        "dna_style": "warm_craft",
        "dna_palette_family": "terracotta_olive",
        "hero_concept": "italian_courtyard_evening",
        "media_dna": _MEDIA_DNA["restaurant"],
    },
    "law": {
        "positioning": "Ruhige Autorität",
        "archetype_primary": "The Counselor",
        "archetype_secondary": "The Architect",
        "brand_promise": "Stille. Ordnung. Kontrolle.",
        "core_emotion": "Kontrolle",
        "secondary_emotion": "Vertrauen ohne Drama",
        "tone": ("Präzise", "Ruhig", "Autorität", "Klar"),
        "visual_style": "Quiet Authority",
        "visual_metaphor": "Ruhige Fassade, klares Licht, kein Theater",
        "photography": (
            "Fassade",
            "Aktenordnung",
            "Klares Tageslicht",
            "Leerer Konferenztisch",
            "Architekturdetail",
        ),
        "forbidden": _CRAFT_FORBIDDEN
        + ("gavel stock", "scales of justice cliché", "angry courtroom"),
        "motion_language": "Minimal · Präzise · Kein Bounce",
        "motion_token": "business",
        "palette": BrandPalette(
            names=("Ink", "Stone", "Brass", "Paper"),
            accent_hex="#b4975a",
            secondary_hex="#4a5568",
            highlight_hex="#e8dcc8",
            surface_hex="#f4f1ea",
            ink_hex="#14161c",
        ),
        "typography_display": "Libre Baskerville",
        "typography_body": "IBM Plex Sans",
        "typography_pair_id": "baskerville_plex_legal",
        "typography_emotion": "authority",
        "icon_style": "Hairline",
        "border_radius_px": 0,
        "shadow_style": "Hairline",
        "glass_level": "low",
        "texture": ("Stone", "Paper", "Brass"),
        "scene_language": ("Silence", "Order", "Facade", "Light"),
        "cta_style": "Ein Knopf · Keine Dringlichkeit",
        "trust_strategy": ("Honorare klar", "Erstberatung", "Vertraulichkeit"),
        "atmosphere_mode": "atelier",
        "dna_style": "modern_clinical",
        "dna_palette_family": "ink_brass",
        "hero_concept": "quiet_authority",
        "media_dna": _MEDIA_DNA["law"],
    },
    "beauty": {
        "positioning": "Beauty Ritual Atelier",
        "archetype_primary": "The Artist",
        "archetype_secondary": "The Host",
        "brand_promise": "Ein Ritual der Schönheit — kein Salon.",
        "core_emotion": "Ruhe",
        "secondary_emotion": "Selbstachtung",
        "tone": ("Ruhig", "Präzise", "Warm", "Ohne Hype"),
        "visual_style": "Atelier Light",
        "visual_metaphor": "Helles Atelierlicht — ruhige Hände, kein Neon-Salon",
        "photography": (
            "Atelierlicht",
            "Hände bei der Arbeit",
            "Produkt detail",
            "Spiegel ohne Chaos",
            "Ruhe vor dem Termin",
        ),
        "forbidden": _CRAFT_FORBIDDEN
        + ("neon salon", "pink glitter stock", "waiting room chairs row"),
        "motion_language": "Weich · Ritual · Langsam",
        "motion_token": "premium",
        "palette": BrandPalette(
            names=("Porcelain", "Rose Clay", "Soft Ink", "Champagne"),
            accent_hex="#c4787a",
            secondary_hex="#8b7355",
            highlight_hex="#f0e6dc",
            surface_hex="#faf7f4",
            ink_hex="#2a2420",
        ),
        "typography_display": "Cormorant",
        "typography_body": "DM Sans",
        "typography_pair_id": "cormorant_dm_beauty",
        "typography_emotion": "soft_precision",
        "icon_style": "Soft Outline",
        "border_radius_px": 8,
        "shadow_style": "Soft Lift",
        "glass_level": "medium",
        "texture": ("Porcelain", "Linen", "Soft metal"),
        "scene_language": ("Ritual", "Light", "Hands", "Quiet"),
        "cta_style": "Termin · Ruhig · Klar",
        "trust_strategy": ("Beratung zuerst", "Preise", "Portfolio"),
        "atmosphere_mode": "atelier",
        "dna_style": "calm_luxury",
        "dna_palette_family": "porcelain_rose",
        "hero_concept": "beauty_ritual",
        "media_dna": _MEDIA_DNA["beauty"],
    },
    "zaunbau": {
        "positioning": "Präziser Zaunbau & Grundstücksschutz",
        "archetype_primary": "The Builder",
        "archetype_secondary": "The Guardian",
        "brand_promise": "Grenzen, die Halt und Haltung geben.",
        "core_emotion": "Stabilität",
        "secondary_emotion": "Ordentliche Klarheit",
        "tone": ("Klar", "Bodenständig", "Präzise", "Zuverlässig"),
        "visual_style": "Industrial Craft",
        "visual_metaphor": "Linie im Abendlicht entlang der Grundstückskante",
        "photography": (
            "Metallzäune",
            "Holzlatten",
            "Fundament",
            "Werkstatt",
            "Saubere Kanten",
        ),
        "forbidden": _CRAFT_FORBIDDEN + ("garden party stock", "luxury villa only"),
        "motion_language": "Fest · Kontrolliert · Klar",
        "motion_token": "business",
        "palette": BrandPalette(
            names=("Umber", "Iron", "Amber", "Warm White", "Forest Edge"),
            accent_hex="#d97706",
            secondary_hex="#92400e",
            highlight_hex="#15803d",
            surface_hex="#faf7f2",
            ink_hex="#1c1917",
        ),
        "typography_display": "Barlow Condensed",
        "typography_body": "Source Sans 3",
        "typography_pair_id": "barlow_source_craft",
        "typography_emotion": "confidence",
        "icon_style": "Outline Industrial",
        "border_radius_px": 10,
        "shadow_style": "Soft Deep",
        "glass_level": "low",
        "texture": ("Holz", "Metall", "Erde"),
        "scene_language": ("Edge", "Line", "Ground", "Light"),
        "cta_style": "Klare Buttons · Ruhiger Abstand",
        "trust_strategy": ("Referenzen", "Material", "Team", "Garantie"),
        "atmosphere_mode": "atelier",
        "dna_style": "modern_clinical",
        "dna_palette_family": "iron_umber",
        "hero_concept": "fence_line_dusk",
        "media_dna": _MEDIA_DNA["zaunbau"],
    },
    "gartenpflege": {
        "positioning": "Sorgfältige Gartenpflege mit ruhiger Hand",
        "archetype_primary": "The Gardener",
        "archetype_secondary": "The Steward",
        "brand_promise": "Ein Garten, der atmet — und gepflegt bleibt.",
        "core_emotion": "Ruhe",
        "secondary_emotion": "Lebendige Ordnung",
        "tone": ("Warm", "Ruhig", "Natürlich", "Sorgfältig"),
        "visual_style": "Organic Modern",
        "visual_metaphor": "Morgentau auf frisch geschnittenem Grün",
        "photography": (
            "Hecken",
            "Rasenflächen",
            "Beete",
            "Werkzeug",
            "Tageslicht im Garten",
        ),
        "forbidden": _CRAFT_FORBIDDEN + ("tropical resort", "spa stones"),
        "motion_language": "Weich · Atmend · Langsam",
        "motion_token": "soft",
        "palette": BrandPalette(
            names=("Leaf", "Moss", "Soil", "Cream", "Sky Mist"),
            accent_hex="#15803d",
            secondary_hex="#3f6212",
            highlight_hex="#86efac",
            surface_hex="#f4f7f1",
            ink_hex="#14532d",
        ),
        "typography_display": "Fraunces",
        "typography_body": "Source Sans 3",
        "typography_pair_id": "fraunces_source_garden",
        "typography_emotion": "organic",
        "icon_style": "Soft Outline",
        "border_radius_px": 14,
        "shadow_style": "Soft Lift",
        "glass_level": "medium",
        "texture": ("Laub", "Holz", "Erde"),
        "scene_language": ("Garden", "Dew", "Light", "Air"),
        "cta_style": "Einladende Buttons · Viel Weißraum",
        "trust_strategy": ("Saisonarbeit", "Vorher/Nachher", "Team", "Pflegepläne"),
        "atmosphere_mode": "mist",
        "dna_style": "nature_therapy",
        "dna_palette_family": "leaf_moss",
        "hero_concept": "garden_morning_dew",
        "media_dna": _MEDIA_DNA["gartenpflege"],
    },
    "handwerk": {
        "positioning": "Solides Handwerk mit klarer Haltung",
        "archetype_primary": "The Craftsman",
        "archetype_secondary": "The Expert",
        "brand_promise": "Arbeit, die hält — und sich sehen lassen kann.",
        "core_emotion": "Vertrauen",
        "secondary_emotion": "Handwerklicher Stolz",
        "tone": ("Direkt", "Ehrlich", "Kompetent", "Bodenständig"),
        "visual_style": "Craft Modern",
        "visual_metaphor": "Werkstattlicht auf sauberem Werkzeug",
        "photography": ("Werkstatt", "Material", "Hände bei der Arbeit", "Baustelle"),
        "forbidden": _CRAFT_FORBIDDEN,
        "motion_language": "Ruhig · Präzise",
        "motion_token": "business",
        "palette": BrandPalette(
            names=("Charcoal", "Steel", "Ochre", "Warm White"),
            accent_hex="#b45309",
            secondary_hex="#44403c",
            highlight_hex="#f59e0b",
            surface_hex="#fafaf9",
            ink_hex="#1c1917",
        ),
        "typography_display": "Oswald",
        "typography_body": "Figtree",
        "typography_pair_id": "oswald_figtree_craft",
        "typography_emotion": "confidence",
        "icon_style": "Outline Industrial",
        "border_radius_px": 10,
        "shadow_style": "Soft Deep",
        "glass_level": "low",
        "texture": ("Holz", "Metall", "Beton"),
        "scene_language": ("Workshop", "Material", "Light"),
        "cta_style": "Klare Buttons · Keine Hektik",
        "trust_strategy": ("Meister", "Referenzen", "Garantie"),
        "atmosphere_mode": "atelier",
        "dna_style": "modern_clinical",
        "dna_palette_family": "charcoal_ochre",
        "hero_concept": "workshop_precision",
        "media_dna": _MEDIA_DNA["handwerk"],
    },
}

_DEFAULT_BOOK: dict[str, Any] = {
    "positioning": "Klare lokale Marke",
    "archetype_primary": "The Expert",
    "archetype_secondary": "The Guide",
    "brand_promise": "Klar. Vertrauenswürdig. Vor Ort.",
    "core_emotion": "Vertrauen",
    "secondary_emotion": "Klarheit",
    "tone": ("Klar", "Freundlich", "Kompetent"),
    "visual_style": "Modern Clear",
    "visual_metaphor": "Offenes Licht auf ruhiger Fläche",
    "photography": ("Echte Orte", "Menschen bei der Arbeit", "Tageslicht"),
    "forbidden": _CRAFT_FORBIDDEN,
    "motion_language": "Ruhig · Klar",
    "motion_token": "business",
    "palette": BrandPalette(
        names=("Slate", "Sage", "Warm White"),
        accent_hex="#5b7c6e",
        secondary_hex="#64748b",
        highlight_hex="#94a3b8",
        surface_hex="#f7f4ef",
        ink_hex="#1c1917",
    ),
    "typography_display": "Manrope",
    "typography_body": "IBM Plex Sans",
    "typography_pair_id": "manrope_ibm_plex_industrial",
    "typography_emotion": "clarity",
    "icon_style": "Outline Soft",
    "border_radius_px": 12,
    "shadow_style": "Soft",
    "glass_level": "medium",
    "texture": ("Paper", "Light"),
    "scene_language": ("Light", "Space", "Calm"),
    "cta_style": "Große Buttons · Ruhiger Abstand",
    "trust_strategy": ("Transparenz", "Kontakt", "Prozess"),
    "atmosphere_mode": "atelier",
    "dna_style": "modern_clinical",
    "dna_palette_family": "sage_mist",
    "hero_concept": "trust_panel",
    "media_dna": _DEFAULT_MEDIA,
}


def _fp(*parts: str) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def resolve_brand_book(
    *,
    business_name: str,
    niche_id: str,
    package_id: str = "business",
    diversity_salt: str = "",
    city: str = "",
) -> BrandBook:
    """Invent / resolve the Brand Book before Creative Identity and Design DNA."""
    niche = (niche_id or "generic").strip().lower() or "generic"
    pid = (package_id or "basic").strip().lower() or "basic"
    name = (business_name or "Business").strip() or "Business"
    salt = (diversity_salt or "").strip()
    city_h = (city or "").strip()

    base = dict(_NICHE_BOOKS.get(niche) or _DEFAULT_BOOK)
    palette: BrandPalette = base["palette"]
    glass = str(base["glass_level"])
    atm = str(base["atmosphere_mode"])
    motion_token = str(base["motion_token"])

    # Tier ladder: Premium deepens glass/atmosphere; Basic stays calmer
    if pid == "premium":
        if glass == "low":
            glass = "medium"
        if niche == "dachreinigung":
            atm = "cinematic"
            motion_token = "premium"
        elif niche in ("zaunbau", "handwerk") and atm == "atelier":
            atm = "dusk"
    elif pid == "basic":
        if glass == "high":
            glass = "low"
        motion_token = "soft" if motion_token == "premium" else motion_token
        if atm == "cinematic":
            atm = "atelier"

    # Light salt variation of highlight only — character stays fixed
    if salt and niche == "dachreinigung":
        # Keep slate/steel character; optional safety-orange emphasis
        digest = int(hashlib.sha256(f"{name}|{salt}|bb".encode()).hexdigest()[:4], 16)
        if digest % 2 == 0:
            palette = replace(palette, highlight_hex="#f97316")

    # Per-company Visual Brand — unique color system + scene language + motion
    from app.factory.visual_brand_system import invent_visual_brand, scene_library_for

    vb = invent_visual_brand(
        brand_name=name,
        niche_id=niche,
        diversity_salt=salt or pid,
        city=city_h,
        base_accent=palette.accent_hex,
        forbidden=tuple(base["forbidden"]),
    )
    palette = replace(
        palette,
        accent_hex=vb.color.accent or palette.accent_hex,
        surface_hex=vb.color.surface or palette.surface_hex,
        ink_hex=vb.color.ink or palette.ink_hex,
        secondary_hex=vb.color.secondary or palette.secondary_hex,
        highlight_hex=vb.color.accent or palette.highlight_hex,
    )
    scenes = scene_library_for(niche)
    photography = tuple(scenes.get("hero", ())) + tuple(scenes.get("gallery", ())[:4])
    if not photography:
        photography = tuple(base["photography"])
    scene_language = tuple(scenes.get("hero", ())) or tuple(base["scene_language"])
    motion_language = vb.motion_language or str(base["motion_language"])
    icon_style = vb.icon_style or str(base["icon_style"])
    visual_style = f"{base['visual_style']} · {vb.illustration_pack}"
    hero_concept = (
        " · ".join(scenes.get("hero", ())[:3])
        or str(base["hero_concept"])
    )

    return BrandBook(
        brand_name=name,
        niche_id=niche,
        package_id=pid,
        positioning=str(base["positioning"]),
        archetype_primary=str(base["archetype_primary"]),
        archetype_secondary=str(base["archetype_secondary"]),
        brand_promise=str(base["brand_promise"]),
        core_emotion=str(base["core_emotion"]),
        secondary_emotion=str(base["secondary_emotion"]),
        tone=tuple(base["tone"]),
        visual_style=visual_style,
        visual_metaphor=str(base["visual_metaphor"]),
        photography=photography,
        forbidden=tuple(base["forbidden"]),
        motion_language=motion_language,
        motion_token=motion_token,
        palette=palette,
        typography_display=str(base["typography_display"]),
        typography_body=str(base["typography_body"]),
        typography_pair_id=str(base["typography_pair_id"]),
        typography_emotion=str(base["typography_emotion"]),
        icon_style=icon_style,
        border_radius_px=int(base["border_radius_px"]),
        shadow_style=str(base["shadow_style"]),
        glass_level=glass,
        texture=tuple(base["texture"]),
        scene_language=scene_language,
        cta_style=str(base["cta_style"]),
        trust_strategy=tuple(base["trust_strategy"]),
        atmosphere_mode=atm,
        dna_style=str(base["dna_style"]),
        dna_palette_family=str(base["dna_palette_family"]),
        hero_concept=hero_concept,
        fingerprint=_fp(name, niche, pid, salt, atm, palette.accent_hex, vb.fingerprint),
        media_dna=base.get("media_dna") or _MEDIA_DNA.get(niche) or _DEFAULT_MEDIA,
        city_hint=city_h,
    )


def apply_brand_book_to_dna(dna: DesignDNA, book: BrandBook) -> DesignDNA:
    """Force DesignDNA to obey the Brand Book — no café palette for a roof brand."""
    style = book.dna_style if book.dna_style else dna.style
    # Prefer known styles; fall back to existing if book style not in STYLES yet
    from app.factory.design_dna.dna import STYLES

    if style not in STYLES:
        # Map industrial craft onto closest existing style tokens
        style = {
            "tech_precision": "modern_clinical",
            "industrial_modern": "modern_clinical",
        }.get(style, dna.style if dna.style in STYLES else "modern_clinical")

    return replace(
        dna,
        emotion=book.typography_emotion or dna.emotion,
        style=style,
        palette_family=book.dna_palette_family or dna.palette_family,
        typography_pair=book.typography_pair_id or dna.typography_pair,
        motion=book.motion_token or dna.motion,
        hero_concept=book.hero_concept or dna.hero_concept,
        glass=book.glass_level or dna.glass,
        accent_hex=book.palette.accent_hex or dna.accent_hex,
        surface_hex=book.palette.surface_hex or dna.surface_hex,
        ink_hex=book.palette.ink_hex or dna.ink_hex,
        atmosphere_mode=book.atmosphere_mode or getattr(dna, "atmosphere_mode", ""),
        brand_book_fp=book.fingerprint,
        border_radius_px=book.border_radius_px or getattr(dna, "border_radius_px", 12),
    )


def brand_book_css_vars(book: BrandBook) -> str:
    """CSS custom properties derived from the Brand Book (radius, palette, glass)."""
    r = max(4, min(24, int(book.border_radius_px)))
    return f"""
/* Brand Book tokens — SSOT */
:root {{
  --brand-accent: {book.palette.accent_hex};
  --brand-surface: {book.palette.surface_hex};
  --brand-ink: {book.palette.ink_hex};
  --brand-secondary: {book.palette.secondary_hex or book.palette.accent_hex};
  --brand-highlight: {book.palette.highlight_hex or book.palette.accent_hex};
  --brand-radius: {r}px;
  --brand-glass: {book.glass_level};
  --dna-ar: {int(book.palette.accent_hex[1:3], 16) if book.palette.accent_hex.startswith("#") and len(book.palette.accent_hex) >= 7 else 59};
  --dna-ag: {int(book.palette.accent_hex[3:5], 16) if book.palette.accent_hex.startswith("#") and len(book.palette.accent_hex) >= 7 else 130};
  --dna-ab: {int(book.palette.accent_hex[5:7], 16) if book.palette.accent_hex.startswith("#") and len(book.palette.accent_hex) >= 7 else 196};
}}
body[data-brand-book] {{
  --card-radius: var(--brand-radius);
  --btn-radius: var(--brand-radius);
}}
"""


__all__ = [
    "BrandBook",
    "BrandPalette",
    "MediaDNA",
    "apply_brand_book_to_dna",
    "brand_book_css_vars",
    "resolve_brand_book",
]
