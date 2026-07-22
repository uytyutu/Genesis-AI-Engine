"""R4.4 — Ownership directory for AuthorizationFacade.

Read-only view of WebsiteOwnership rows. Not HTTP · not Session.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from app.portal.ownership import WebsiteOwnership

ENGINE_ID = "ownership_directory_v1"


class OwnershipDirectory(Protocol):
    def all_ownerships(self) -> tuple[WebsiteOwnership, ...]: ...


@dataclass
class InMemoryOwnershipDirectory:
    ownerships: list[WebsiteOwnership] = field(default_factory=list)

    def all_ownerships(self) -> tuple[WebsiteOwnership, ...]:
        return tuple(self.ownerships)

    def add(self, ownership: WebsiteOwnership) -> None:
        self.ownerships.append(ownership)


def empty_ownership_directory() -> InMemoryOwnershipDirectory:
    return InMemoryOwnershipDirectory()
