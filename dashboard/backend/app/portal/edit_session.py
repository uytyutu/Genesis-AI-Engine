"""R3.5.6 — EditSession domain model.

EditSession is a record that editing occurred (or is open) for a Website —
not an editor, autosave, collaboration, or version history.

No API · UI · Auth in this slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

from app.portal.website import Website

ENGINE_ID = "edit_session_domain_v1"

EditSessionStatus = Literal["open", "closed", "cancelled"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class EditSession:
    """Fact of an edit session for a Website — not the edit payload."""

    session_id: str
    website_id: str
    status: EditSessionStatus
    started_at: str
    ended_at: str | None

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_edit_session(
    *,
    website: Website,
    status: EditSessionStatus = "open",
    session_id: str | None = None,
    started_at: str | None = None,
    ended_at: str | None = None,
) -> EditSession:
    """Construct an EditSession row (in-memory only — no editor logic)."""
    return EditSession(
        session_id=session_id or str(uuid4()),
        website_id=website.website_id,
        status=status,
        started_at=started_at or _utc_now_iso(),
        ended_at=ended_at,
    )


def close_edit_session(
    session: EditSession,
    *,
    status: EditSessionStatus = "closed",
) -> EditSession:
    """Mark session ended — still a record only, no content merge."""
    if status == "open":
        raise ValueError("close_edit_session requires a non-open status")
    return replace(
        session,
        status=status,
        ended_at=session.ended_at or _utc_now_iso(),
    )
