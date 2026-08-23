"""Visual Benchmark — look before you design (especially Premium).

Factory must study best-in-niche references for composition, rhythm, Hero,
color, type, depth, and atmosphere — then decide. Never copy pixels.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class VisualBenchmark:
    niche_id: str
    references: tuple[str, ...]
    composition: str
    rhythm: str
    hero: str
    color: str
    typography: str
    depth: str
    atmosphere: str
    anti_patterns: tuple[str, ...] = ()
    notes: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)

    def design_brief(self) -> str:
        """Short brief injected into DNA resolution / composer comments."""
        lines = [
            f"Visual Benchmark · {self.niche_id}",
            f"Composition: {self.composition}",
            f"Rhythm: {self.rhythm}",
            f"Hero: {self.hero}",
            f"Color: {self.color}",
            f"Type: {self.typography}",
            f"Depth: {self.depth}",
            f"Atmosphere: {self.atmosphere}",
        ]
        if self.anti_patterns:
            lines.append("Avoid: " + "; ".join(self.anti_patterns[:4]))
        return "\n".join(lines)


# Curated study notes — not scrapes. Update when a niche becomes the proving ground.
_BENCHMARKS: dict[str, VisualBenchmark] = {
    "psychology": VisualBenchmark(
        niche_id="psychology",
        references=(
            "European private therapy practices (calm editorial sites)",
            "Nordic wellness / nature-therapy studios",
            "Quiet high-end coaching studios (not clinic templates)",
        ),
        composition=(
            "One full-bleed Hero scene, then alternating depth bands — "
            "never a stack of equal white cards"
        ),
        rhythm=(
            "Slow inhale: dark/photo → soft open → ink CTA. "
            "Max one consecutive light band"
        ),
        hero=(
            "Cinematic stillness: nature path, greenhouse light, or intimate "
            "therapy room — readable type in first viewport, expensive quiet"
        ),
        color="Sage, sand, warm stone, soft ink — no salon pink-gold glam",
        typography="Editorial display + calm body; generous leading; few words in Hero",
        depth="Glass panels, soft mesh, vignette, real photo grain — not flat #fff slabs",
        atmosphere="Living air: particles, aurora wash, scroll glass nav — life, not wallpaper",
        anti_patterns=(
            "Beauty salon / spa glam interiors",
            "White section ladder",
            "Generic stock smile headshots as Hero",
            "Template feature-grid as first impression",
        ),
    ),
}


# Official quality floors (owner rule) — impression, not HTML scores.
QUALITY_FLOORS: dict[str, str] = {
    "basic": "Starter ≥ modern small-business website (sellable without shame at Starter price)",
    "business": "Business ≥ Virtus Core /site quality floor (never worse than Virtus itself)",
    "premium": "Premium > Virtus Core /site — expensive European digital-studio impression (logo off still reads studio)",
}


def get_visual_benchmark(niche_id: str | None) -> VisualBenchmark | None:
    key = (niche_id or "").strip().lower()
    return _BENCHMARKS.get(key)


def require_visual_benchmark(niche_id: str | None, *, package_id: str) -> VisualBenchmark | None:
    """Premium must consult niche benchmark before design decisions."""
    pid = (package_id or "").strip().lower()
    bench = get_visual_benchmark(niche_id)
    if pid == "premium" and bench is None:
        # Soft: niche without curated notes still builds, but DNA gets a generic studio brief.
        return VisualBenchmark(
            niche_id=(niche_id or "generic").strip().lower() or "generic",
            references=("Best contemporary niche sites in market",),
            composition="Full-bleed Hero, asymmetric next fold, no equal-card stack",
            rhythm="Contrast ladder; never two open-light bands in a row",
            hero="First viewport must sell the craft before any section list",
            color="Niche-true palette; no default purple mesh",
            typography="Expressive display + calm body",
            depth="Photo + glass + atmosphere layers",
            atmosphere="Living canvas, not flat white",
            anti_patterns=("Template ladder", "Metric PASS without eye check"),
        )
    return bench


def quality_floor_for(package_id: str) -> str:
    pid = (package_id or "basic").strip().lower()
    if pid == "starter":
        pid = "basic"
    return QUALITY_FLOORS.get(pid, QUALITY_FLOORS["basic"])
