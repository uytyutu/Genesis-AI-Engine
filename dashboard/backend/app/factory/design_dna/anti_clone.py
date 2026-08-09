"""Anti-clone fingerprints — same niche should not get twin DNA."""

from __future__ import annotations

import hashlib
from collections.abc import Callable
from typing import Sequence

from app.factory.design_dna.dna import Treatment


def fingerprint_dna(
    *,
    style: str,
    hero_layout: str,
    palette: str,
    treatments: Sequence[tuple[str, Treatment]],
    package_id: str,
    niche_id: str,
    business_name: str = "",
) -> str:
    rhythm = "|".join(f"{k}:{v}" for k, v in treatments[:12])
    name = (business_name or "").strip().lower()
    raw = f"{niche_id}|{package_id}|{style}|{hero_layout}|{palette}|{rhythm}|{name}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def ensure_unique_fingerprint(
    base: str,
    *,
    recent: list[str],
    reseed: Callable[[int], str],
    max_attempts: int = 5,
) -> str:
    """If fingerprint collides with recent demos, re-roll up to max_attempts."""
    recent_set = {r[:32] for r in (recent or []) if r}
    if base[:32] not in recent_set:
        return base
    for n in range(1, max_attempts + 1):
        cand = reseed(n)
        if cand[:32] not in recent_set:
            return cand
    return hashlib.sha256(f"{base}|forced-unique".encode("utf-8")).hexdigest()
