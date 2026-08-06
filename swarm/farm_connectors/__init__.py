"""Farm connectors — multi-platform bounty sources (Tier A/B/C).

Farm Engine must not depend on a single marketplace.
Each connector only fetches + normalizes. Shared pipeline:
  Connector Manager → Opportunity Normalizer → Confidence → CEO Approve
  → Execution Engine → Draft PR → CEO Submit → Reward Protection → REAL
"""

from __future__ import annotations

from .base import ConnectorStatus, FarmConnector, Tier
from .manager import ConnectorManager, default_manager
from .normalize import dedupe_opportunities, opportunity_key
from .registry import CONNECTOR_CATALOG

__all__ = [
    "CONNECTOR_CATALOG",
    "ConnectorManager",
    "ConnectorStatus",
    "FarmConnector",
    "Tier",
    "dedupe_opportunities",
    "default_manager",
    "opportunity_key",
]
