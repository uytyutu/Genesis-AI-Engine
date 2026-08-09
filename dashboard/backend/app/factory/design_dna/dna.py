"""Design DNA — impression-first identity for Factory products."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


Treatment = str  # photo_band | ink | tint | glass | gradient | open_light | illustration

STYLES = (
    "scandinavian_calm",
    "nature_therapy",
    "luxury_studio",
    "editorial",
    "modern_clinical",
    "organic_premium",
    "cinematic_dark",
    "magazine_ink",
    "boutique_warm",
    "tech_precision",
    "corporate_clear",
    "immersive_nature",
)

EMOTIONS = (
    "calm",
    "trust",
    "warmth",
    "clarity",
    "prestige",
    "nature",
    "luxury",
    "innovation",
    "confidence",
    "energy",
    "elegance",
    "minimal",
    "organic",
    "editorial",
    "cinematic",
    "immersive",
)


@dataclass(frozen=True)
class DesignDNA:
    """Artistic identity resolved before HTML assembly."""

    emotion: str
    style: str
    palette_family: str
    typography_pair: str
    motion: str
    hero_concept: str
    hero_layout: str
    depth: str
    glass: str
    composition: str
    package_id: str
    niche_id: str
    fingerprint: str
    section_treatments: tuple[tuple[str, Treatment], ...] = field(default_factory=tuple)
    accent_hex: str = "#5b7c6e"
    surface_hex: str = "#f4f1eb"
    ink_hex: str = "#1c1917"
    # Brand Book SSOT — atmosphere + provenance (Sprint 1)
    atmosphere_mode: str = ""
    brand_book_fp: str = ""
    border_radius_px: int = 12

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["section_treatments"] = [[k, v] for k, v in self.section_treatments]
        return d

    def body_attrs(self) -> dict[str, str]:
        attrs = {
            "data-dna-style": self.style,
            "data-dna-emotion": self.emotion,
            "data-dna-palette": self.palette_family,
            "data-dna-hero": self.hero_concept,
            "data-dna-depth": self.depth,
            "data-dna-glass": self.glass,
            "data-dna-composition": self.composition,
            "data-dna-fp": self.fingerprint[:16],
        }
        if self.atmosphere_mode:
            attrs["data-dna-atm"] = self.atmosphere_mode
        if self.brand_book_fp:
            attrs["data-brand-book"] = self.brand_book_fp[:16]
        return attrs
