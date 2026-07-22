"""R3.5.6 — EditSession domain model (record only; no editor)."""

from __future__ import annotations

import pytest

from app.portal.edit_session import (
    ENGINE_ID,
    EditSession,
    close_edit_session,
    new_edit_session,
)
from app.portal.website import new_website


def test_engine_id():
    assert ENGINE_ID == "edit_session_domain_v1"


def test_edit_session_required_fields():
    w = new_website(client_id="c1", product_id="p1", market_code="DE")
    s = new_edit_session(website=w)
    assert isinstance(s, EditSession)
    assert s.session_id
    assert s.website_id == w.website_id
    assert s.status == "open"
    assert s.started_at
    assert s.ended_at is None
    payload = s.as_dict()
    assert set(payload) >= {
        "session_id",
        "website_id",
        "status",
        "started_at",
        "ended_at",
    }


def test_website_owns_edit_session_via_website_id():
    w = new_website(client_id="c1", product_id="p1", market_code="FR")
    s = new_edit_session(website=w)
    assert s.website_id == w.website_id
    closed = close_edit_session(s)
    assert closed.website_id == w.website_id
    assert closed.status == "closed"
    assert closed.ended_at


def test_no_editor_infrastructure_fields():
    fields = set(EditSession.__dataclass_fields__)
    for forbidden in (
        "content",
        "diff",
        "autosave",
        "cursor",
        "collaborators",
        "history",
        "password",
        "token",
    ):
        assert forbidden not in fields


def test_close_rejects_open_status():
    w = new_website(client_id="c1", product_id="p1", market_code="AT")
    s = new_edit_session(website=w)
    with pytest.raises(ValueError):
        close_edit_session(s, status="open")
