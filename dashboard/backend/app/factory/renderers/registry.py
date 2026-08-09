"""Industry × Approach → Renderer Strategy.

Composition / Brand approach picks the Approach axis.
Niche picks the Industry default when approach is empty.
Classic coverage must shrink toward 0% (KPI).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.factory.renderers.base import RendererStrategy

# Canonical strategy set (Studio Era)
STRATEGY_IDS: tuple[str, ...] = (
    "craftsman",
    "editorial",
    "luxury",
    "corporate",
    "commerce",
    "clinic",
    "legal",
    "restaurant",
    "technology",
    "minimal",
    "classic",
)

# Approach axis → strategy
APPROACH_TO_STRATEGY: dict[str, str] = {
    "luxury": "luxury",
    "editorial": "editorial",
    "corporate": "corporate",
    "minimal": "minimal",
    "boutique": "editorial",
    "industrial": "craftsman",
    "magazine": "editorial",
    "immersive": "restaurant",
    "craftsman": "craftsman",
    "clinic": "clinic",
    "legal": "legal",
    "commerce": "commerce",
    "technology": "technology",
    "restaurant": "restaurant",
    "classic": "classic",
}

# Composition id → approach (then strategy)
COMPOSITION_TO_APPROACH: dict[str, str] = {
    "magazine": "magazine",
    "editorial": "editorial",
    "folio": "editorial",
    "whisper": "minimal",
    "sanctuary": "editorial",
    "breath": "minimal",
    "dialogue": "editorial",
    "immersive": "immersive",
    "cinematic": "industrial",
    "hearth": "restaurant",
    "signal": "industrial",
    "atelier": "boutique",
    "atelier_night": "luxury",
    "industrial": "industrial",
    "vault": "corporate",
    "ember": "restaurant",
    "horizon": "immersive",
    "boutique": "boutique",
    "luxury_brand": "luxury",
    "narrative": "editorial",
    "storytelling": "editorial",
    "corporate": "corporate",
    "modern": "technology",
    "tech_stack": "technology",
    "product_first": "commerce",
    "runway": "commerce",
    "chamber": "clinic",
    "ledger": "legal",
    "healthcare": "clinic",
    "garden": "craftsman",
    "nature": "minimal",
}

# Niche → default strategy when no approach/composition
NICHE_TO_STRATEGY: dict[str, str] = {
    "dachreinigung": "craftsman",
    "zaunbau": "craftsman",
    "gartenpflege": "craftsman",
    "handwerk": "craftsman",
    "cleaning": "craftsman",
    "green": "craftsman",
    "auto": "craftsman",
    "car_dealership": "luxury",
    "psychology": "editorial",
    "family_psychology": "editorial",
    "dental": "clinic",
    "law": "legal",
    "accounting": "corporate",
    "restaurant": "restaurant",
    "fashion": "commerce",
    "beauty": "clinic",
    "fitness": "minimal",
    "photography": "editorial",
    "realestate": "luxury",
    "computer": "technology",
    "appliance": "corporate",
    "energy": "corporate",
    "furniture": "commerce",
}

# Back-compat alias used by composition as_dict
COMPOSITION_TO_STRATEGY: dict[str, str] = {
    k: APPROACH_TO_STRATEGY.get(v, v) for k, v in COMPOSITION_TO_APPROACH.items()
}


def strategy_id_for(
    *,
    niche_id: str,
    package_id: str = "business",
    composition_id: str = "",
    approach: str = "",
) -> str:
    """Resolve Strategy from Approach × Industry (niche).

    Niche silhouette wins over a generic «corporate» style label —
    otherwise Auto/Dach/Handwerk collapse into one template (Owner FAIL).
    """
    niche = (niche_id or "generic").strip().lower()
    comp = (composition_id or "").strip().lower()
    appr = (approach or "").strip().lower()
    niche_default = NICHE_TO_STRATEGY.get(niche, "classic")

    if appr and appr in APPROACH_TO_STRATEGY:
        sid = APPROACH_TO_STRATEGY[appr]
        # Generic corporate must not erase craft / auto / roof character
        if sid == "corporate" and niche_default in {
            "craftsman",
            "restaurant",
            "editorial",
            "clinic",
            "legal",
            "commerce",
        }:
            sid = niche_default
    elif comp and comp in COMPOSITION_TO_APPROACH:
        sid = APPROACH_TO_STRATEGY.get(
            COMPOSITION_TO_APPROACH[comp], COMPOSITION_TO_APPROACH[comp]
        )
    elif comp and comp in COMPOSITION_TO_STRATEGY:
        sid = COMPOSITION_TO_STRATEGY[comp]
    else:
        sid = niche_default

    # Composition / style labels must not erase Handwerk / Dach / Auto work-site DOM.
    # «Premium look» = craft architecture + premium visual DNA — not LuxuryRenderer.
    if niche_default == "craftsman" and sid != "craftsman":
        if appr in {
            "luxury",
            "minimal",
            "editorial",
            "boutique",
            "magazine",
            "corporate",
            "clinic",
            "legal",
            "technology",
            "commerce",
            "restaurant",
            "immersive",
        } or not appr:
            if sid in {
                "clinic",
                "legal",
                "corporate",
                "minimal",
                "technology",
                "commerce",
                "luxury",
                "editorial",
                "restaurant",
            }:
                sid = "craftsman"

    # Autohaus / realestate must stay Luxury — composition "ember" must not become Restaurant.
    if niche_default == "luxury" and sid != "luxury":
        if niche in {"car_dealership", "realestate"} or sid in {
            "restaurant",
            "clinic",
            "classic",
            "corporate",
            "craftsman",
        }:
            sid = "luxury"

    # Psychology family must stay Editorial — not clinic/classic funnel.
    if niche_default == "editorial" and sid != "editorial":
        if niche in {"psychology", "family_psychology", "photography"} or sid in {
            "classic",
            "clinic",
            "corporate",
            "restaurant",
        }:
            sid = "editorial"

    return sid


def get_renderer(
    *,
    niche_id: str,
    package_id: str = "business",
    composition_id: str = "",
    approach: str = "",
) -> RendererStrategy:
    from app.factory.renderers.classic import ClassicRenderer
    from app.factory.renderers.craftsman import CraftsmanRenderer
    from app.factory.renderers.editorial import EditorialRenderer
    from app.factory.renderers.family import (
        ClinicRenderer,
        CommerceRenderer,
        CorporateRenderer,
        LegalRenderer,
        LuxuryRenderer,
        MinimalRenderer,
        RestaurantRenderer,
        TechnologyRenderer,
    )

    sid = strategy_id_for(
        niche_id=niche_id,
        package_id=package_id,
        composition_id=composition_id,
        approach=approach,
    )
    mapping: dict[str, type] = {
        "craftsman": CraftsmanRenderer,
        "editorial": EditorialRenderer,
        "luxury": LuxuryRenderer,
        "corporate": CorporateRenderer,
        "commerce": CommerceRenderer,
        "clinic": ClinicRenderer,
        "legal": LegalRenderer,
        "restaurant": RestaurantRenderer,
        "technology": TechnologyRenderer,
        "minimal": MinimalRenderer,
        "classic": ClassicRenderer,
        "legacy": ClassicRenderer,
    }
    cls = mapping.get(sid, ClassicRenderer)
    return cls()  # type: ignore[return-value]


def renderer_coverage(*, niches: list[str] | None = None) -> dict[str, Any]:
    """KPI: how many niches escape Classic."""
    from app.factory.design_dna.composition_library import COMPOSITION_LIBRARY

    niche_list = niches or sorted(set(NICHE_TO_STRATEGY) | {"generic", "restaurant"})
    counts: dict[str, int] = {s: 0 for s in STRATEGY_IDS}
    for n in niche_list:
        sid = strategy_id_for(niche_id=n, package_id="premium")
        counts[sid] = counts.get(sid, 0) + 1
    total = max(1, sum(counts.values()))
    pct = {k: round(100.0 * v / total, 1) for k, v in counts.items()}
    status = {
        "craftsman": "PASS",
        "editorial": "PASS",
        "luxury": "PASS",
        "corporate": "PASS",
        "commerce": "PASS",
        "clinic": "PASS",
        "legal": "PASS",
        "restaurant": "PASS",
        "technology": "PASS",
        "minimal": "PASS",
        "classic": "SHRINK",
    }
    return {
        "gate": "RENDERER_COVERAGE",
        "strategies": status,
        "niche_counts": counts,
        "niche_pct": pct,
        "classic_pct": pct.get("classic", 0),
        "compositions_mapped": sum(
            1 for c in COMPOSITION_LIBRARY if c in COMPOSITION_TO_APPROACH
        ),
        "compositions_total": len(COMPOSITION_LIBRARY),
        "kpi": "Drive classic_pct toward 0 without new Engine layers",
    }


__all__ = [
    "APPROACH_TO_STRATEGY",
    "COMPOSITION_TO_APPROACH",
    "COMPOSITION_TO_STRATEGY",
    "NICHE_TO_STRATEGY",
    "STRATEGY_IDS",
    "get_renderer",
    "renderer_coverage",
    "strategy_id_for",
]
