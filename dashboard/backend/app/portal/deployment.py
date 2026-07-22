"""R3.5.4 — Deployment domain model.

Deployment is a publish *record*, not a publish process.
Does not store ZIP · does not host · does not deploy.

Website.deployment_id may point at the current Deployment.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.website import Website

ENGINE_ID = "deployment_domain_v1"

DeploymentStatus = Literal["recorded", "active", "superseded", "failed"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Deployment:
    """One publication record for a Website."""

    deployment_id: str
    website_id: str
    artifact_id: str
    version: int
    status: DeploymentStatus
    created_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_deployment(
    *,
    website: Website,
    artifact_id: str,
    version: int = 1,
    status: DeploymentStatus = "recorded",
    deployment_id: str | None = None,
) -> Deployment:
    """Construct a Deployment row (in-memory only — no publish/hosting)."""
    return Deployment(
        deployment_id=deployment_id or str(uuid4()),
        website_id=website.website_id,
        artifact_id=artifact_id.strip(),
        version=version,
        status=status,
        created_at=_utc_now_iso(),
    )


def attach_deployment(website: Website, deployment: Deployment) -> Website:
    """Website references current Deployment via deployment_id (temporary 1:1)."""
    if deployment.website_id != website.website_id:
        raise ValueError("deployment.website_id must match website.website_id")
    return replace(
        website,
        deployment_id=deployment.deployment_id,
        updated_at=_utc_now_iso(),
    )
