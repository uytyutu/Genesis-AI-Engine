"""R4.2 — SessionStore (in-memory).

Server is the source of truth for sessions. Not a JWT store.

``SessionStore`` is the **abstraction**; ``InMemorySessionStore`` is today's
adapter. Future Redis / Database stores plug in without changing SessionFacade.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.session import Session, is_session_active, revoke_session

ENGINE_ID = "session_store_v1"


class SessionStore(Protocol):
    def save(self, session: Session) -> None: ...

    def get(self, session_id: str) -> Session | None: ...

    def invalidate(self, session_id: str) -> bool:
        """Revoke one session. Returns True if it existed and was revoked."""
        ...


class InMemorySessionStore:
    """Process-local session map — replace with DB/Redis later."""

    def __init__(self) -> None:
        self._rows: dict[str, Session] = {}

    def save(self, session: Session) -> None:
        self._rows[session.session_id] = session

    def get(self, session_id: str) -> Session | None:
        session = self._rows.get(session_id)
        if session is None:
            return None
        if not is_session_active(session):
            return None
        return session

    def invalidate(self, session_id: str) -> bool:
        session = self._rows.get(session_id)
        if session is None:
            return False
        if session.status == "revoked":
            return False
        self._rows[session_id] = revoke_session(session)
        return True
