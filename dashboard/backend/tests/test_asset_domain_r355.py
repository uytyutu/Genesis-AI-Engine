"""R3.5.5 — Asset domain model (reference only; no Gallery/upload)."""

from __future__ import annotations

from app.portal.asset import ENGINE_ID, Asset, new_asset
from app.portal.website import new_website


def test_engine_id():
    assert ENGINE_ID == "asset_domain_v1"


def test_asset_required_fields():
    w = new_website(client_id="c1", product_id="p1", market_code="DE")
    a = new_asset(
        website=w,
        asset_type="logo",
        artifact_ref="refs/logos/brand-mark",
    )
    assert isinstance(a, Asset)
    assert a.asset_id
    assert a.website_id == w.website_id
    assert a.asset_type == "logo"
    assert a.artifact_ref == "refs/logos/brand-mark"
    assert a.created_at
    payload = a.as_dict()
    assert set(payload) >= {
        "asset_id",
        "website_id",
        "asset_type",
        "artifact_ref",
        "created_at",
    }


def test_website_owns_asset_via_website_id():
    w = new_website(client_id="c1", product_id="p1", market_code="NL")
    a1 = new_asset(website=w, asset_type="image", artifact_ref="refs/img/1")
    a2 = new_asset(website=w, asset_type="document", artifact_ref="refs/doc/1")
    assert a1.website_id == w.website_id
    assert a2.website_id == w.website_id
    assert a1.asset_id != a2.asset_id


def test_no_storage_or_gallery_fields():
    fields = set(Asset.__dataclass_fields__)
    for forbidden in (
        "bytes",
        "blob",
        "path",
        "url",
        "cdn",
        "upload",
        "gallery",
        "width",
        "height",
    ):
        assert forbidden not in fields
