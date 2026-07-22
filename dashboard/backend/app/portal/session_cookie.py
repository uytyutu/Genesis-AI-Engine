"""R4.2 — Session cookie settings (HttpOnly).

Builds kwargs for Response.set_cookie. Does not read cookies.
CSRF / middleware belong to later slices.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

from app.portal.session import DEFAULT_SESSION_TTL

ENGINE_ID = "session_cookie_v1"

SameSite = Literal["lax", "strict", "none"]

DEFAULT_COOKIE_NAME = "virtus_session"


@dataclass(frozen=True)
class SessionCookieSpec:
    """Values for Starlette/FastAPI set_cookie — not a JWT."""

    key: str
    value: str
    httponly: bool
    secure: bool
    samesite: SameSite
    max_age: int
    path: str

    def as_set_cookie_kwargs(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "value": self.value,
            "httponly": self.httponly,
            "secure": self.secure,
            "samesite": self.samesite,
            "max_age": self.max_age,
            "path": self.path,
        }


class SessionCookieFactory:
    def __init__(
        self,
        *,
        cookie_name: str = DEFAULT_COOKIE_NAME,
        secure: bool | None = None,
        samesite: SameSite = "lax",
        path: str = "/",
        ttl: timedelta = DEFAULT_SESSION_TTL,
    ) -> None:
        if secure is None:
            secure = os.environ.get("PORTAL_COOKIE_SECURE", "").lower() in (
                "1",
                "true",
                "yes",
            )
        self._cookie_name = cookie_name
        self._secure = secure
        self._samesite = samesite
        self._path = path
        self._ttl = ttl

    @property
    def cookie_name(self) -> str:
        return self._cookie_name

    def build(self, session_id: str) -> SessionCookieSpec:
        return SessionCookieSpec(
            key=self._cookie_name,
            value=session_id,
            httponly=True,
            secure=self._secure,
            samesite=self._samesite,
            max_age=int(self._ttl.total_seconds()),
            path=self._path,
        )

    def as_delete_cookie_kwargs(self) -> dict[str, Any]:
        """Clear cookie using the same attributes as set_cookie (R4.5)."""
        return {
            "key": self._cookie_name,
            "path": self._path,
            "secure": self._secure,
            "httponly": True,
            "samesite": self._samesite,
        }
