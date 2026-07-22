"""R3.5.2 — Website domain model.

Website is the primary managed object after Path A delivery.
``Website.client_id`` = commercial owner (Client).
Portal human access = ``WebsiteOwnership`` (Account) — R3.12.1; not this field.

No API · no storage · no Portal UI in this slice.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ENGINE_ID = "website_domain_v1"

WebsiteStatus = Literal["draft", "built", "published", "archived"]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


@dataclass(frozen=True)
class Website:
    """One manageable site project — not an Order, not a ZIP."""

    website_id: str
    client_id: str
    product_id: str
    market_code: str
    deployment_id: str | None
    status: WebsiteStatus
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OrderWebsiteRef:
    """Order creates a Website; ownership stays with Client via Website.client_id."""

    order_id: str
    website_id: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def new_website(
    *,
    client_id: str,
    product_id: str,
    market_code: str,
    status: WebsiteStatus = "draft",
    deployment_id: str | None = None,
    website_id: str | None = None,
) -> Website:
    """Construct a Website row (in-memory only — no persistence in R3.5.2)."""
    now = _utc_now_iso()
    return Website(
        website_id=website_id or str(uuid4()),
        client_id=client_id,
        product_id=product_id,
        market_code=market_code.upper(),
        deployment_id=deployment_id,
        status=status,
        created_at=now,
        updated_at=now,
    )


def link_order_to_website(order_id: str, website: Website) -> OrderWebsiteRef:
    return OrderWebsiteRef(order_id=order_id, website_id=website.website_id)
