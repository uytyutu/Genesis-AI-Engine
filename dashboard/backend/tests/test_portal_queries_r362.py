"""R3.6.2 — Portal Query Objects (parameters only)."""

from __future__ import annotations

from dataclasses import fields

from app.portal.queries import ENGINE_ID, AssetQuery, ClientQuery, WebsiteQuery


def test_query_engine_id():
    assert ENGINE_ID == "portal_query_v1"


def test_query_shapes():
    assert {f.name for f in fields(ClientQuery)} == {"client_id"}
    assert {f.name for f in fields(WebsiteQuery)} == {"website_id"}
    assert {f.name for f in fields(AssetQuery)} == {"website_id", "asset_type"}


def test_queries_are_frozen():
    q = ClientQuery(client_id="c1")
    try:
        q.client_id = "x"  # type: ignore[misc]
        raised = False
    except Exception:
        raised = True
    assert raised
