"""R3.5.4 — Deployment domain model (publish record only)."""

from __future__ import annotations

import pytest

from app.portal.deployment import (
    ENGINE_ID,
    Deployment,
    attach_deployment,
    new_deployment,
)
from app.portal.website import new_website


def test_engine_id():
    assert ENGINE_ID == "deployment_domain_v1"


def test_deployment_required_fields():
    w = new_website(client_id="c1", product_id="prod-1", market_code="DE")
    d = new_deployment(
        website=w,
        artifact_id="artifact-prod-1",
        version=1,
        status="recorded",
    )
    assert isinstance(d, Deployment)
    assert d.deployment_id
    assert d.website_id == w.website_id
    assert d.artifact_id == "artifact-prod-1"
    assert d.version == 1
    assert d.status == "recorded"
    assert d.created_at
    payload = d.as_dict()
    assert set(payload) >= {
        "deployment_id",
        "website_id",
        "artifact_id",
        "version",
        "status",
        "created_at",
    }


def test_website_references_deployment():
    w = new_website(client_id="c1", product_id="prod-1", market_code="ES")
    d = new_deployment(website=w, artifact_id="art-1", status="active")
    linked = attach_deployment(w, d)
    assert linked.deployment_id == d.deployment_id
    assert d.website_id == linked.website_id


def test_attach_rejects_mismatched_website():
    w1 = new_website(client_id="c1", product_id="p1", market_code="AT")
    w2 = new_website(client_id="c1", product_id="p2", market_code="AT")
    d = new_deployment(website=w1, artifact_id="a1")
    with pytest.raises(ValueError):
        attach_deployment(w2, d)


def test_no_publish_infrastructure_fields():
    """Record only — no ZIP bytes, host, domain, or auth on the model."""
    fields = set(Deployment.__dataclass_fields__)
    for forbidden in ("zip", "zip_bytes", "host", "domain", "url", "password", "token"):
        assert forbidden not in fields
