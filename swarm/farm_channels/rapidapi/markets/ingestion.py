"""Dataset ingestion pipeline — license gate before PRODUCTION."""

from __future__ import annotations

from typing import Any

from swarm.farm_channels.rapidapi.markets.data_sources import get_source


PIPELINE_STAGES = (
    "SOURCE",
    "DOWNLOAD_API",
    "VALIDATE",
    "NORMALIZE",
    "LICENSE_CHECK",
    "QUALITY_CHECK",
    "VERSION",
    "PRODUCTION",
)


def plan_ingest(source_id: str) -> dict[str, Any]:
    """
    Return an honest ingest plan. Does not download or invent rows.
    Without commercial_use + usable_in_production → stops at LICENSE_CHECK.
    """
    src = get_source(source_id)
    if not src:
        return {
            "ok": False,
            "source_id": source_id,
            "error": "unknown_source",
            "stages": list(PIPELINE_STAGES),
            "blocked_at": "SOURCE",
        }
    commercial = bool(src.get("commercial_use") and src.get("usable_in_production"))
    stages = [
        {"stage": "SOURCE", "ok": True},
        {
            "stage": "DOWNLOAD_API",
            "ok": False,
            "note": "Manual/CEO-approved download only — not auto-fetched here",
        },
        {"stage": "VALIDATE", "ok": False, "note": "awaiting local file"},
        {"stage": "NORMALIZE", "ok": False},
        {
            "stage": "LICENSE_CHECK",
            "ok": commercial,
            "commercial_use": bool(src.get("commercial_use")),
            "usable_in_production": bool(src.get("usable_in_production")),
        },
        {"stage": "QUALITY_CHECK", "ok": False},
        {"stage": "VERSION", "ok": False, "version": src.get("version")},
        {
            "stage": "PRODUCTION",
            "ok": False,
            "note": "PRODUCTION only after LICENSE_CHECK + QUALITY_CHECK PASS",
        },
    ]
    return {
        "ok": commercial,
        "source_id": source_id,
        "source": src,
        "stages": stages,
        "blocked_at": None if commercial else "LICENSE_CHECK",
        "honesty_rule": "DO NOT USE if commercial license not confirmed.",
    }


class DatasetProvider:
    """Adapter contract — implementations load local verified datasets only."""

    def __init__(self, source_id: str) -> None:
        self.source_id = source_id
        self.meta = get_source(source_id)

    def health(self) -> dict[str, Any]:
        if not self.meta:
            return {"ok": False, "error": "unknown_source", "source_id": self.source_id}
        return {
            "ok": True,
            "source_id": self.source_id,
            "version": self.meta.get("version"),
            "coverage": self.meta.get("coverage"),
            "commercial_use": bool(self.meta.get("commercial_use")),
            "usable_in_production": bool(self.meta.get("usable_in_production")),
        }
