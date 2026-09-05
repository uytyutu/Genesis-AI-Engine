"""Document Archive (batch) SKU contract — ROADMAP until batch pipeline exists."""

from __future__ import annotations

from typing import Any

SKU_ID = "document_archive"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "ZIP archive + index/manifest + per-file status",
    "validation": ["zip_opens", "manifest_complete", "rename_rules_applied"],
    "requires": ["batch_upload"],
    "price_eur_hint": {"min": 29.90, "max": 99.90},
}


def execute_document_archive(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "document_archive ROADMAP"}


def validate_archive(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "document_archive validator ROADMAP"}
