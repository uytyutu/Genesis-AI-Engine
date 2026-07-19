"""ExternalCapability registry — enable via env; Mission1 Freeze metadata."""

from __future__ import annotations

import os
from typing import Any

from app.integration.external_capabilities.models import (
    EXTERNAL_CATALOG,
    ExternalCapabilityDef,
)


def _env_on(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def list_external_defs() -> list[ExternalCapabilityDef]:
    return list(EXTERNAL_CATALOG)


def get_def(capability_id: str) -> ExternalCapabilityDef | None:
    for row in EXTERNAL_CATALOG:
        if row.id == capability_id:
            return row
    return None


def is_enabled(capability_id: str) -> bool:
    """Runtime gate: env enable (+ key if required). Never auto-on."""
    row = get_def(capability_id)
    if row is None:
        return False
    if not _env_on(row.env_enable):
        return False
    if row.requires_key and row.env_key:
        if not (os.getenv(row.env_key) or "").strip():
            return False
    return True


def mission1_activatable(row: ExternalCapabilityDef) -> bool:
    """Under Mission 1 Freeze only Mission1/Internal may be turned on."""
    return row.mission_required in ("Mission1", "Internal")


def status_row(row: ExternalCapabilityDef) -> dict[str, Any]:
    enabled = is_enabled(row.id)
    return {
        "id": row.id,
        "label": row.label,
        "provider": row.provider,
        "purpose": row.purpose,
        "commercial_value": row.commercial_value,
        "mission_required": row.mission_required,
        "mission1_activatable": mission1_activatable(row),
        "env_enable": row.env_enable,
        "env_key": row.env_key,
        "requires_key": row.requires_key,
        "license_note": row.license_note,
        "quota_hint": row.quota_hint,
        "fallback_mode": row.fallback_mode,
        "product_surfaces": list(row.product_surfaces),
        "adapter": row.adapter,
        "enabled": enabled,
        "ready": bool(row.adapter) and mission1_activatable(row),
        "exists": True,
    }


def snapshot(*, mission1_freeze: bool = True) -> dict[str, Any]:
    rows = [status_row(r) for r in EXTERNAL_CATALOG]
    enabled = [r for r in rows if r["enabled"]]
    return {
        "version": "external-cap-1",
        "mission1_freeze": mission1_freeze,
        "rule": "disabled_by_default_env_gate_fallback_required",
        "llm_chain_untouched": True,
        "summary": {
            "total": len(rows),
            "enabled": len(enabled),
            "mission1_activatable": sum(1 for r in rows if r["mission1_activatable"]),
            "ready_adapters": sum(1 for r in rows if r["ready"]),
        },
        "capabilities": rows,
    }
