"""Shared types for Farm connectors."""

from __future__ import annotations

from enum import Enum
from typing import Any, Protocol, runtime_checkable


class Tier(str, Enum):
    """Readiness tiers — do not mix automation models."""

    A = "A"  # OSS bounties: Opire / Polar / Algora / GitHub Issues
    B = "B"  # Bug bounty platforms — separate process
    C = "C"  # Web3 / research — no implementation yet


class ConnectorStatus(str, Enum):
    LIVE = "live"  # fetches real opportunities
    PLANNED = "planned"  # Tier A skeleton — API research next
    RESEARCH = "research"  # Tier C — study official process first
    DISABLED = "disabled"  # Tier B until security module exists


@runtime_checkable
class FarmConnector(Protocol):
    """One legal bounty source. Fetch + normalize only — no execution."""

    id: str
    display_name: str
    tier: Tier
    status: ConnectorStatus
    official_docs_url: str

    def fetch_raw(self) -> list[dict[str, Any]]:
        """Platform-native payloads. Empty list if not live / offline."""
        ...

    def normalize(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        """Map one raw item → Opportunity. None = drop."""
        ...
