"""Data Source Registry — license gate before production datasets."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

# Honest sources only. Sample DE PLZ is internal demo coverage — not a national cadastre.
DATA_SOURCES: dict[str, dict[str, Any]] = {
    "virtus_sample_de_plz": {
        "source_id": "virtus_sample_de_plz",
        "source": "Virtus Core internal sample (major DE cities)",
        "license": "internal_sample",
        "commercial_use": True,
        "attribution": "Virtus Core",
        "last_updated": "2026-08-09",
        "update_frequency": "manual",
        "coverage": "sample_major_cities_only",
        "download_url": "",
        "api": "",
        "checksum": "n/a",
        "version": "de_plz_sample_v1",
        "countries": ["DE"],
        "usable_in_production": True,
        "note": (
            "Not a full Deutsche Post / OpenPLZ dump. "
            "Expand only with a commercially licensed dataset."
        ),
    },
}


def get_source(source_id: str) -> dict[str, Any] | None:
    row = DATA_SOURCES.get((source_id or "").strip())
    return deepcopy(row) if row else None


def list_sources() -> list[dict[str, Any]]:
    return [deepcopy(v) for v in DATA_SOURCES.values()]


def commercial_use_ok(source_id: str) -> bool:
    row = get_source(source_id)
    return bool(row and row.get("commercial_use") and row.get("usable_in_production"))
