"""R3.5.3 — Client domain model.

Client is owner identity only — not auth, roles, teams, or permissions.
Website.client_id references Client.client_id.

No API · no storage · no Portal UI in this slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.portal.website import Website, new_website

ENGINE_ID = "client_domain_v1"


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Client:
    """Owner identity for one or more Websites."""

    client_id: str
    display_name: str
    primary_email: str
    preferred_language: str
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_client(
    *,
    display_name: str,
    primary_email: str,
    preferred_language: str = "de",
    client_id: str | None = None,
) -> Client:
    """Construct a Client row (in-memory only — no persistence in R3.5.3)."""
    now = _utc_now_iso()
    return Client(
        client_id=client_id or str(uuid4()),
        display_name=display_name.strip(),
        primary_email=primary_email.strip().lower(),
        preferred_language=preferred_language.strip().lower(),
        created_at=now,
        updated_at=now,
    )


def website_for_client(
    client: Client,
    *,
    product_id: str,
    market_code: str,
    **kwargs: Any,
) -> Website:
    """Website owned by Client — link is Website.client_id == Client.client_id."""
    return new_website(
        client_id=client.client_id,
        product_id=product_id,
        market_code=market_code,
        **kwargs,
    )
