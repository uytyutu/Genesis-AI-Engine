"""Mission 6.2 — WebsiteOwnershipBridge.

```text
WebsiteOwnership
        │
        ▼
WebsiteOwnershipBridge
        │
        ▼
ProductOwnership (source=website_bridge)
```

Does **not** migrate or mutate WebsiteOwnership.
Read-only projection for ProductOwnership views until native rows exist.
"""

from __future__ import annotations

from app.portal.ownership_directory import OwnershipDirectory
from app.portal.product_ownership import ProductOwnership

ENGINE_ID = "website_ownership_bridge_v1"


def website_product_id(website_id: str) -> str:
    """Stable product instance id for a bridged Website."""
    return f"prod_website_{website_id}"


class WebsiteOwnershipBridge:
    """Projects WebsiteOwnership → ProductOwnership without copying into Store."""

    def __init__(self, ownerships: OwnershipDirectory) -> None:
        self._ownerships = ownerships

    def list_for_account(self, account_id: str) -> tuple[ProductOwnership, ...]:
        out: list[ProductOwnership] = []
        for row in self._ownerships.all_ownerships():
            if row.account_id != account_id:
                continue
            out.append(
                ProductOwnership(
                    ownership_id=f"bridge_{row.ownership_id}",
                    account_id=row.account_id,
                    product_id=website_product_id(row.website_id),
                    product_type="website",
                    status="active",
                    source="website_bridge",
                    created_at=row.created_at,
                )
            )
        return tuple(out)
