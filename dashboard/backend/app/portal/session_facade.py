"""R4.2 — SessionFacade.

Creates / invalidates sessions after Authentication succeeded.
Does not call Authentication Domain. Does not set HTTP cookies
(that is the cookie factory + router).
"""

from __future__ import annotations

from datetime import timedelta

from app.portal.session import DEFAULT_SESSION_TTL, Session, create_session
from app.portal.session_store import SessionStore

ENGINE_ID = "session_facade_v1"


class SessionFacade:
    def __init__(
        self,
        store: SessionStore,
        *,
        ttl: timedelta = DEFAULT_SESSION_TTL,
    ) -> None:
        self._store = store
        self._ttl = ttl

    def start_session(self, account_id: str) -> Session:
        session = create_session(account_id, ttl=self._ttl)
        self._store.save(session)
        return session

    def invalidate_session(self, session_id: str) -> bool:
        return self._store.invalidate(session_id)

    def get_active_session(self, session_id: str) -> Session | None:
        return self._store.get(session_id)
