"""R3.5.5 — Asset domain model.

Asset is a reference to a resource for a Website — not file bytes.
No upload · storage · CDN · resize · Gallery in this slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.website import Website

ENGINE_ID = "asset_domain_v1"

AssetType = Literal["image", "logo", "document", "other"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Asset:
    """Reference to a Website resource (Gallery/docs later use this row)."""

    asset_id: str
    website_id: str
    asset_type: AssetType
    artifact_ref: str
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_asset(
    *,
    website: Website,
    asset_type: AssetType,
    artifact_ref: str,
    asset_id: str | None = None,
) -> Asset:
    """Construct an Asset row (in-memory only — no storage/upload)."""
    return Asset(
        asset_id=asset_id or str(uuid4()),
        website_id=website.website_id,
        asset_type=asset_type,
        artifact_ref=artifact_ref.strip(),
        created_at=_utc_now_iso(),
    )
