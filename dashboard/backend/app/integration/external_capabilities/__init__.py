"""External free-tier capabilities for Virtus Core."""

from __future__ import annotations

from app.integration.external_capabilities.models import AdapterResult, ExternalCapabilityDef
from app.integration.external_capabilities.nominatim import resolve_maps_embed
from app.integration.external_capabilities.registry import (
    get_def,
    is_enabled,
    list_external_defs,
    snapshot,
)
from app.integration.external_capabilities.wikiknowledge import enrich_brief

__all__ = [
    "AdapterResult",
    "ExternalCapabilityDef",
    "enrich_brief",
    "get_def",
    "is_enabled",
    "list_external_defs",
    "resolve_maps_embed",
    "snapshot",
]
