"""Pick exactly one best API Farm candidate for the first market track."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.models import (
    STATUS_ARCHIVED,
    STATUS_FAILED,
    STATUS_QUALITY_GATE_FAILED,
)
from swarm.farm_channels.rapidapi.scoring import rank_candidates
from swarm.farm_channels.rapidapi.store import ApiFarmStore

# Prefer self-contained / low license risk for first Hub listing.
_PREFERRED_SLUG_HINTS = (
    "de-plz-city-lookup",
    "openapi-lint-report",
    "html-meta-og-extractor",
)


def candidate_slug(row: dict[str, Any]) -> str:
    plan = (row.get("publish_package") or {}).get("plan") or {}
    if plan.get("slug"):
        return str(plan["slug"])
    name = str(row.get("name") or "unnamed-api")
    return "".join(c if c.isalnum() else "-" for c in name.lower()).strip("-")


def select_best_candidate(store: ApiFarmStore) -> dict[str, Any] | None:
    """Highest total_score among non-failed candidates; prefer known safe runtimes."""
    rows = [
        r
        for r in store.list_candidates()
        if r.get("status")
        not in (STATUS_QUALITY_GATE_FAILED, STATUS_ARCHIVED, STATUS_FAILED)
    ]
    if not rows:
        return None
    ranked = rank_candidates(rows, top_n=max(1, len(rows)))
    # Soft prefer preferred slugs when scores are close (within 5 pts of top)
    top = float(ranked[0].get("total_score") or 0)
    preferred = [
        r
        for r in ranked
        if candidate_slug(r) in _PREFERRED_SLUG_HINTS
        and abs(float(r.get("total_score") or 0) - top) <= 5.0
    ]
    return preferred[0] if preferred else ranked[0]
