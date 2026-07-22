"""R4.3 — Request principal (Account | Anonymous).

Middleware identity only — not an authorization decision.

Keep minimal: identity of the current request only.
Do **not** grow this into permissions, Website lists, or business payload.
Authorization stays in Authorization Domain (R3.12.5 / R4.4+).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.account import Account

ENGINE_ID = "request_principal_v1"


@dataclass(frozen=True)
class RequestPrincipal:
    """Who is making this request. ``account is None`` ⇒ Anonymous."""

    account: Account | None

    @property
    def is_authenticated(self) -> bool:
        return self.account is not None


ANONYMOUS = RequestPrincipal(account=None)
