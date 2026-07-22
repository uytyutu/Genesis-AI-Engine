"""R3.11.2 — Website Catalog from Factory sandbox.

Loads ``sandbox/{product_id}/meta.json`` into a ``PortalCatalog`` so the
Dashboard endpoint can return real Website / Deployment views.

Read-only bridge — does not invent Portal persistence.

Architecture: this module is a **temporary Sandbox adapter** into
``PortalCatalog``. A future Database / Cloud adapter should swap here
without changing Facade, Query, or HTTP.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import uuid5, NAMESPACE_URL

from app.portal.client import Client
from app.portal.deployment import Deployment
from app.portal.read_service import PortalCatalog
from app.portal.website import Website, WebsiteStatus

ENGINE_ID = "website_catalog_v1"


def default_factory_sandbox_dirs() -> tuple[Path, ...]:
    """Factory + app sandbox roots (existing on disk only)."""
    app_dir = Path(__file__).resolve().parents[1]
    backend_dir = app_dir.parent
    return (backend_dir / "sandbox", app_dir / "sandbox")


def _map_website_status(meta: dict[str, Any]) -> WebsiteStatus:
    raw = str(meta.get("status") or "").strip().lower()
    if meta.get("published") or raw == "published":
        return "published"
    if raw in ("draft", "built", "published", "archived"):
        return raw  # type: ignore[return-value]
    if raw in ("completed", "ready", "approved"):
        return "built"
    return "draft"


def _client_from_meta(product_id: str, meta: dict[str, Any]) -> Client:
    legal = meta.get("client_legal") if isinstance(meta.get("client_legal"), dict) else {}
    email = str(
        legal.get("email")
        or meta.get("email")
        or f"{product_id}@portal.local"
    ).strip().lower()
    name = str(
        legal.get("business_name")
        or meta.get("business_name")
        or product_id
    ).strip() or product_id
    client_id = str(uuid5(NAMESPACE_URL, f"portal-client:{email}"))
    created = str(meta.get("created_at") or "")
    updated = str(meta.get("updated_at") or created)
    return Client(
        client_id=client_id,
        display_name=name,
        primary_email=email,
        preferred_language=str(meta.get("market_code") or "de").lower()[:2] or "de",
        created_at=created or "1970-01-01T00:00:00+00:00",
        updated_at=updated or created or "1970-01-01T00:00:00+00:00",
    )


def _rows_from_meta(product_id: str, meta: dict[str, Any]) -> tuple[Client, Website, Deployment | None]:
    client = _client_from_meta(product_id, meta)
    status = _map_website_status(meta)
    created = str(meta.get("created_at") or "1970-01-01T00:00:00+00:00")
    updated = str(meta.get("updated_at") or created)
    market = str(meta.get("market_code") or "DE").upper()
    deployment: Deployment | None = None
    deployment_id: str | None = None
    if status == "published" or meta.get("published"):
        deployment_id = str(uuid5(NAMESPACE_URL, f"portal-deploy:{product_id}"))
        deployment = Deployment(
            deployment_id=deployment_id,
            website_id=product_id,
            artifact_id=product_id,
            version=1,
            status="active",
            created_at=str(meta.get("published_at") or updated),
        )
    website = Website(
        website_id=product_id,
        client_id=client.client_id,
        product_id=product_id,
        market_code=market,
        deployment_id=deployment_id,
        status=status,
        created_at=created,
        updated_at=updated,
    )
    return client, website, deployment


def load_portal_catalog_from_factory_sandbox(
    sandbox_dirs: tuple[Path, ...] | None = None,
) -> PortalCatalog:
    """Scan Factory sandbox meta.json files → PortalCatalog."""
    clients: dict[str, Client] = {}
    websites: dict[str, Website] = {}
    deployments: dict[str, Deployment] = {}
    roots = sandbox_dirs if sandbox_dirs is not None else default_factory_sandbox_dirs()
    for root in roots:
        if not root.is_dir():
            continue
        for meta_path in sorted(root.glob("*/meta.json")):
            product_id = meta_path.parent.name
            try:
                meta = json.loads(meta_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if not isinstance(meta, dict):
                continue
            client, website, deployment = _rows_from_meta(product_id, meta)
            clients[client.client_id] = client
            websites[website.website_id] = website
            if deployment is not None:
                deployments[deployment.deployment_id] = deployment
    return PortalCatalog(
        clients=clients,
        websites=websites,
        deployments=deployments,
        assets={},
        edit_sessions={},
    )
