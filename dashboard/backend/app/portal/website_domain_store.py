"""R5.3 — WebsiteDomainStore (temporary in-memory adapter).

``WebsiteDomainStore`` is the abstraction; ``InMemoryWebsiteDomainStore`` is
today's adapter. Future DNS/SSL/provider adapters plug in without changing
the Facade or HTTP contract.
"""

from __future__ import annotations

from typing import Protocol

from app.portal.website_domain import WebsiteDomain

ENGINE_ID = "website_domain_store_v1"


class WebsiteDomainStore(Protocol):
    def get(self, website_id: str) -> WebsiteDomain | None: ...

    def save(self, binding: WebsiteDomain) -> None: ...


class InMemoryWebsiteDomainStore:
    """Process-local domain map — replace with durable / provider-backed store later."""

    def __init__(self) -> None:
        self._rows: dict[str, WebsiteDomain] = {}

    def get(self, website_id: str) -> WebsiteDomain | None:
        return self._rows.get(website_id)

    def save(self, binding: WebsiteDomain) -> None:
        self._rows[binding.website_id] = binding
