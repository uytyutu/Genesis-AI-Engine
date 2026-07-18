"""Niche design profiles for Path A Factory landings.

Gate 1: in-code profiles (niche_id → palette). Horizon: load factory/themes/{niche_id}/config.json
without changing build_landing call shape — only resolve_niche_profile() grows.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NicheStyle:
    primary: str
    primary_dark: str
    accent: str
    hero_gradient: str


@dataclass(frozen=True)
class NicheProfile:
    niche_id: str
    label_de: str
    style: NicheStyle


# 15–20 quality industry keys later — start with Path A DE niches (no random templates).
_PROFILES: dict[str, NicheProfile] = {
    "auto": NicheProfile(
        "auto",
        "Autowerkstatt",
        NicheStyle("#b91c1c", "#7f1d1d", "#f87171", "linear-gradient(135deg,#0a0a0a,#b91c1c)"),
    ),
    "dental": NicheProfile(
        "dental",
        "Zahnmedizin",
        NicheStyle("#0284c7", "#0369a1", "#e0f2fe", "linear-gradient(135deg,#0369a1,#38bdf8)"),
    ),
    "law": NicheProfile(
        "law",
        "Kanzlei",
        NicheStyle("#1e3a5f", "#0f172a", "#c9a227", "linear-gradient(135deg,#0f172a,#1e3a5f)"),
    ),
    "beauty": NicheProfile(
        "beauty",
        "Salon",
        NicheStyle("#be185d", "#9d174d", "#fbcfe8", "linear-gradient(135deg,#831843,#db2777)"),
    ),
    "energy": NicheProfile(
        "energy",
        "Photovoltaik",
        NicheStyle("#16a34a", "#15803d", "#facc15", "linear-gradient(135deg,#14532d,#ca8a04)"),
    ),
    "green": NicheProfile(
        "green",
        "Garten",
        NicheStyle("#22c55e", "#166534", "#86efac", "linear-gradient(135deg,#14532d,#22c55e)"),
    ),
    "computer": NicheProfile(
        "computer",
        "PC-Service",
        NicheStyle("#0369a1", "#0c4a6e", "#38bdf8", "linear-gradient(135deg,#0f172a,#0284c7)"),
    ),
    "appliance": NicheProfile(
        "appliance",
        "Hausgeräte",
        NicheStyle("#475569", "#1e293b", "#94a3b8", "linear-gradient(135deg,#0f172a,#475569)"),
    ),
    "handwerk": NicheProfile(
        "handwerk",
        "Handwerk",
        NicheStyle("#b45309", "#78350f", "#fbbf24", "linear-gradient(135deg,#1c1917,#b45309)"),
    ),
    "generic": NicheProfile(
        "generic",
        "Lokalgeschäft",
        NicheStyle("#334155", "#0f172a", "#38bdf8", "linear-gradient(135deg,#0f172a,#334155)"),
    ),
}


def resolve_niche_profile(niche_id: str | None) -> NicheProfile:
    """Extension point for tomorrow: niche_id from order / site analysis → profile."""
    key = (niche_id or "generic").strip().lower() or "generic"
    return _PROFILES.get(key, _PROFILES["generic"])


def known_niche_ids() -> tuple[str, ...]:
    return tuple(sorted(_PROFILES.keys()))
