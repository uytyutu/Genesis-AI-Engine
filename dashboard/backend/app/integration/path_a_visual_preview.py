"""Path A adaptive Visual Experience preview (no Factory 3D embed yet)."""

from __future__ import annotations

from typing import Any

# Niches that should never force interactive 3D — motion / still only.
_MOTION_ONLY_NICHES = frozenset({"law"})


def resolve_path_a_visual_preview(
    *,
    niche_id: str | None,
    tier: str | None = "business",
    specialization: str | None = None,
    locale: str = "de",
) -> dict[str, Any]:
    """Resolve VXP for order wizard; adapt mode by niche (never empty)."""
    from app.factory.research_3d.visual_experience_registry import (
        resolve_visual_experience,
    )

    t = str(tier or "business").strip().lower()
    if t not in ("basic", "business", "premium"):
        t = "business"

    exp = resolve_visual_experience(
        niche_id=niche_id,
        tier=t,
        specialization=specialization,
        locale=locale,
    )
    niche = str(exp.get("niche_id") or niche_id or "generic").strip().lower()
    mode = str(exp.get("mode") or "none")

    if niche in _MOTION_ONLY_NICHES and mode == "interactive_3d":
        if exp.get("preview"):
            exp["mode"] = "preview"
            exp["reason"] = "path_a_motion_only_still"
            exp["model"] = None
        else:
            exp["mode"] = "css_motion"
            exp["reason"] = "path_a_motion_only_css"
            exp["model"] = None

    # Public URL for research stills (served under /research-3d/ when mounted)
    preview_rel = exp.get("preview")
    preview_url = None
    if preview_rel:
        rel = str(preview_rel).replace("\\", "/").lstrip("/")
        if rel.startswith("showcases/") or rel.startswith("_research_3d/"):
            preview_url = f"/research-3d/{rel}"
        else:
            preview_url = f"/research-3d/{rel}"

    exp["preview_url"] = preview_url
    exp["adaptive"] = True
    return exp
