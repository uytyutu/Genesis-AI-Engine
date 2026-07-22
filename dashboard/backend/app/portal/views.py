"""R3.6.3 / R3.6.4 — Portal View Models.

Read projections for Portal consumers — data only.
No business logic · no HTTP · no FastAPI · no Auth.
Domain models stay unchanged; ReadService maps to these views.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.asset import Asset, AssetType
from app.portal.client import Client
from app.portal.deployment import Deployment, DeploymentStatus
from app.portal.edit_session import EditSession, EditSessionStatus
from app.portal.website import Website, WebsiteStatus

ENGINE_ID = "portal_view_v1"


@dataclass(frozen=True)
class ClientView:
    client_id: str
    display_name: str
    primary_email: str
    preferred_language: str


@dataclass(frozen=True)
class WebsiteView:
    website_id: str
    client_id: str
    product_id: str
    market_code: str
    deployment_id: str | None
    status: WebsiteStatus


@dataclass(frozen=True)
class DeploymentView:
    deployment_id: str
    website_id: str
    artifact_id: str
    version: int
    status: DeploymentStatus


@dataclass(frozen=True)
class AssetView:
    asset_id: str
    website_id: str
    asset_type: AssetType
    artifact_ref: str


@dataclass(frozen=True)
class EditSessionView:
    session_id: str
    website_id: str
    status: EditSessionStatus
    started_at: str
    ended_at: str | None


def to_client_view(client: Client) -> ClientView:
    return ClientView(
        client_id=client.client_id,
        display_name=client.display_name,
        primary_email=client.primary_email,
        preferred_language=client.preferred_language,
    )


def to_website_view(website: Website) -> WebsiteView:
    return WebsiteView(
        website_id=website.website_id,
        client_id=website.client_id,
        product_id=website.product_id,
        market_code=website.market_code,
        deployment_id=website.deployment_id,
        status=website.status,
    )


def to_deployment_view(deployment: Deployment) -> DeploymentView:
    return DeploymentView(
        deployment_id=deployment.deployment_id,
        website_id=deployment.website_id,
        artifact_id=deployment.artifact_id,
        version=deployment.version,
        status=deployment.status,
    )


def to_asset_view(asset: Asset) -> AssetView:
    return AssetView(
        asset_id=asset.asset_id,
        website_id=asset.website_id,
        asset_type=asset.asset_type,
        artifact_ref=asset.artifact_ref,
    )


def to_edit_session_view(session: EditSession) -> EditSessionView:
    return EditSessionView(
        session_id=session.session_id,
        website_id=session.website_id,
        status=session.status,
        started_at=session.started_at,
        ended_at=session.ended_at,
    )
