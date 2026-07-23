"""R3.11.2 — Dashboard endpoint reads Factory sandbox catalog."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.portal.account import new_account
from app.portal.client import new_client
from app.portal.ownership import grant_website_ownership
from app.portal.ownership_directory import InMemoryOwnershipDirectory
from app.portal.portal_dashboard_registration import register_portal_dashboard
from app.portal.portal_dashboard_router import clear_website_dashboard_facade
from app.portal.website import new_website
from app.portal.website_catalog import load_portal_catalog_from_factory_sandbox


def test_endpoint_returns_real_sandbox_site(tmp_path: Path):
    product_id = "live-site-3112"
    product_dir = tmp_path / product_id
    product_dir.mkdir()
    (product_dir / "meta.json").write_text(
        json.dumps(
            {
                "product_id": product_id,
                "business_name": "Nord Cafe",
                "market_code": "DE",
                "status": "published",
                "published": True,
                "published_at": "2026-07-22T12:00:00+00:00",
                "created_at": "2026-07-22T11:00:00+00:00",
                "updated_at": "2026-07-22T12:00:00+00:00",
                "client_legal": {
                    "email": "owner@nord.test",
                    "business_name": "Nord Cafe",
                },
            }
        ),
        encoding="utf-8",
    )
    clear_website_dashboard_facade()
    catalog = load_portal_catalog_from_factory_sandbox(sandbox_dirs=(tmp_path,))
    # AuthN/AuthZ is intentional (R4.4): principal + website ownership required.
    account = new_account(email="owner@nord.test", display_name="Owner", status="ready")
    client = new_client(display_name="Nord Cafe", primary_email="owner@nord.test")
    owned = new_website(
        client_id=client.client_id,
        product_id=product_id,
        market_code="DE",
        website_id=product_id,
    )
    ownerships = InMemoryOwnershipDirectory(
        ownerships=[grant_website_ownership(account, owned)]
    )
    app = FastAPI()

    @app.middleware("http")
    async def inject_account(request: Request, call_next):
        request.state.account = account
        return await call_next(request)

    assert register_portal_dashboard(app, catalog=catalog, ownerships=ownerships) is True
    http = TestClient(app)
    try:
        r = http.get(f"/portal/websites/{product_id}/dashboard")
        assert r.status_code == 200
        body = r.json()
        assert body["website"]["website_id"] == product_id
        assert body["website"]["market_code"] == "DE"
        assert body["status"] == "published"
        assert body["current_deployment"] is not None
        assert body["current_deployment"]["artifact_id"] == product_id
    finally:
        clear_website_dashboard_facade()
