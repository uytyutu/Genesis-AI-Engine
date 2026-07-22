"""R3.5.2 — Website domain model (no Portal API/UI)."""

from __future__ import annotations

from app.portal.website import (
    ENGINE_ID,
    Deployment,
    OrderWebsiteRef,
    Website,
    link_order_to_website,
    new_deployment,
    new_website,
)


def test_engine_id():
    assert ENGINE_ID == "website_domain_v1"


def test_website_required_fields():
    w = new_website(
        client_id="client-1",
        product_id="prod-abc",
        market_code="de",
    )
    assert isinstance(w, Website)
    assert w.website_id
    assert w.client_id == "client-1"
    assert w.product_id == "prod-abc"
    assert w.market_code == "DE"
    assert w.deployment_id is None
    assert w.status == "draft"
    assert w.created_at
    assert w.updated_at
    d = w.as_dict()
    assert set(d) >= {
        "website_id",
        "client_id",
        "product_id",
        "market_code",
        "deployment_id",
        "status",
        "created_at",
        "updated_at",
    }


def test_order_references_website():
    w = new_website(client_id="c1", product_id="p1", market_code="GB")
    ref = link_order_to_website("order-99", w)
    assert isinstance(ref, OrderWebsiteRef)
    assert ref.order_id == "order-99"
    assert ref.website_id == w.website_id


def test_deployment_references_website():
    w = new_website(client_id="c1", product_id="p1", market_code="FR")
    dep = new_deployment(website=w, mode="zip_only")
    assert isinstance(dep, Deployment)
    assert dep.website_id == w.website_id
    assert dep.mode == "zip_only"
    assert dep.deployment_id

    w2 = new_website(
        client_id="c1",
        product_id="p1",
        market_code="FR",
        deployment_id=dep.deployment_id,
        status="published",
    )
    assert w2.deployment_id == dep.deployment_id


def test_client_website_deployment_chain():
    """Client → Website → Deployment (identity links only)."""
    client_id = "client-el3"
    w = new_website(client_id=client_id, product_id="sandbox-1", market_code="NL")
    assert w.client_id == client_id
    dep = new_deployment(website=w)
    assert dep.website_id == w.website_id
