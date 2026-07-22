"""R3.5.3 — Client domain model (identity only; no Auth/Portal)."""

from __future__ import annotations

from app.portal.client import (
    ENGINE_ID,
    Client,
    new_client,
    website_for_client,
)


def test_engine_id():
    assert ENGINE_ID == "client_domain_v1"


def test_client_required_fields():
    c = new_client(
        display_name="  EL3 Studio ",
        primary_email="  Owner@Example.DE ",
        preferred_language="DE",
    )
    assert isinstance(c, Client)
    assert c.client_id
    assert c.display_name == "EL3 Studio"
    assert c.primary_email == "owner@example.de"
    assert c.preferred_language == "de"
    assert c.created_at
    assert c.updated_at
    d = c.as_dict()
    assert set(d) >= {
        "client_id",
        "display_name",
        "primary_email",
        "preferred_language",
        "created_at",
        "updated_at",
    }


def test_website_references_client():
    c = new_client(display_name="Virtus Test", primary_email="a@b.c")
    w = website_for_client(c, product_id="prod-1", market_code="FR")
    assert w.client_id == c.client_id
    assert w.product_id == "prod-1"
    assert w.market_code == "FR"


def test_client_owns_website_not_auth():
    """Client is identity only — no roles/permissions fields on the model."""
    fields = set(Client.__dataclass_fields__)
    assert "role" not in fields
    assert "roles" not in fields
    assert "permissions" not in fields
    assert "password" not in fields
    assert "token" not in fields
