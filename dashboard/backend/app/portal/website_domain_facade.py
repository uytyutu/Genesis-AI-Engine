"""R5.3 — WebsiteDomainFacade (reference resource-state ModuleFacade).

```text
Authorization (caller)
    ↓
WebsiteDomainFacade
    ↓
WebsiteDomain Domain + Store
```

Sole application entry for Website↔domain state get/update.
Does not authenticate · authorize · know cookies · Session · Ownership.
Does not call DNS · SSL · registrar APIs.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.portal.website_domain import (
    WebsiteDomainError,
    WebsiteDomainUpdate,
    apply_website_domain_update,
    empty_website_domain,
)
from app.portal.website_domain_store import WebsiteDomainStore
from app.portal.website_domain_view import (
    WebsiteDomainView,
    build_website_domain_view,
)

ENGINE_ID = "website_domain_facade_v1"


@dataclass(frozen=True)
class WebsiteDomainFacade:
    """Resource-state ModuleFacade — copy this shape for lifecycle resources."""

    _store: WebsiteDomainStore

    @classmethod
    def from_store(cls, store: WebsiteDomainStore) -> WebsiteDomainFacade:
        return cls(_store=store)

    def get_domain(self, website_id: str) -> WebsiteDomainView:
        row = self._store.get(website_id)
        if row is None:
            row = empty_website_domain(website_id)
        return build_website_domain_view(row)

    def update_domain(
        self,
        website_id: str,
        *,
        primary_domain: str,
        custom_domain: str,
        domain_status: str,
        verification_status: str,
    ) -> WebsiteDomainView:
        current = self._store.get(website_id)
        if current is None:
            current = empty_website_domain(website_id)
        update = WebsiteDomainUpdate(
            primary_domain=primary_domain,
            custom_domain=custom_domain,
            domain_status=domain_status,
            verification_status=verification_status,
        )
        try:
            next_row = apply_website_domain_update(current, update)
        except WebsiteDomainError:
            raise
        self._store.save(next_row)
        return build_website_domain_view(next_row)
