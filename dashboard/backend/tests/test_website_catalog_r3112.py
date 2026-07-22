"""R3.11.2 — Website Catalog from Factory sandbox → PortalCatalog."""

from __future__ import annotations

import json
from pathlib import Path

from app.portal.website_catalog import (
    ENGINE_ID,
    load_portal_catalog_from_factory_sandbox,
)
from app.portal.website_dashboard_facade import WebsiteDashboardFacade
from app.portal.website_dashboard_query import WebsiteDashboardQuery


def test_engine_id():
    assert ENGINE_ID == "website_catalog_v1"


def test_load_from_temp_sandbox(tmp_path: Path):
    product_id = "site-real-001"
    product_dir = tmp_path / product_id
    product_dir.mkdir()
    meta = {
        "product_id": product_id,
        "business_name": "Dental Smile",
        "market_code": "DE",
        "status": "published",
        "published": True,
        "published_at": "2026-07-22T10:00:00+00:00",
        "created_at": "2026-07-22T09:00:00+00:00",
        "updated_at": "2026-07-22T10:00:00+00:00",
        "client_legal": {"email": "info@dental.test", "business_name": "Dental Smile"},
    }
    (product_dir / "meta.json").write_text(
        json.dumps(meta),
        encoding="utf-8",
    )
    catalog = load_portal_catalog_from_factory_sandbox(sandbox_dirs=(tmp_path,))
    assert product_id in catalog.websites
    site = catalog.websites[product_id]
    assert site.status == "published"
    assert site.market_code == "DE"
    assert site.client_id in catalog.clients
    assert catalog.clients[site.client_id].primary_email == "info@dental.test"
    assert site.deployment_id in catalog.deployments


def test_dashboard_query_reads_catalog(tmp_path: Path):
    product_id = "site-dash-002"
    product_dir = tmp_path / product_id
    product_dir.mkdir()
    (product_dir / "meta.json").write_text(
        json.dumps(
            {
                "product_id": product_id,
                "business_name": "Cafe Nord",
                "market_code": "NL",
                "status": "completed",
                "created_at": "2026-07-22T09:00:00+00:00",
                "updated_at": "2026-07-22T09:00:00+00:00",
                "client_legal": {"email": "hello@cafe.test"},
            }
        ),
        encoding="utf-8",
    )
    catalog = load_portal_catalog_from_factory_sandbox(sandbox_dirs=(tmp_path,))
    facade = WebsiteDashboardFacade.from_query(
        WebsiteDashboardQuery.from_catalog(catalog)
    )
    dash = facade.get_dashboard(product_id)
    assert dash is not None
    assert dash.website.website_id == product_id
    assert dash.website.market_code == "NL"
    assert dash.status == "built"
    assert dash.current_deployment is None


def test_skips_corrupt_meta(tmp_path: Path):
    bad = tmp_path / "bad"
    bad.mkdir()
    (bad / "meta.json").write_text("{not-json", encoding="utf-8")
    catalog = load_portal_catalog_from_factory_sandbox(sandbox_dirs=(tmp_path,))
    assert catalog.websites == {}
