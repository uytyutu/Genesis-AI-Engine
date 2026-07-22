"""PT2 — conversation status lifecycle for Operations Workspace."""

from __future__ import annotations

from app.portal.conversation import (
    ConversationError,
    new_conversation,
    set_conversation_status,
)


def test_set_conversation_status_close_and_reopen():
    row = new_conversation(profile_id="prof-1")
    assert row.status == "open"
    closed = set_conversation_status(row, status="closed")
    assert closed.status == "closed"
    assert closed.updated_at >= row.updated_at
    reopened = set_conversation_status(closed, status="open")
    assert reopened.status == "open"


def test_set_conversation_status_rejects_unknown():
    row = new_conversation(profile_id="prof-1")
    try:
        set_conversation_status(row, status="archived")
        assert False, "expected error"
    except ConversationError as exc:
        assert str(exc) == "unknown_status"
