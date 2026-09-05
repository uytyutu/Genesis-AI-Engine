"""PDF/A-2b SKU contract — ROADMAP until conversion + veraPDF-class validation."""

from __future__ import annotations

from typing import Any

SKU_ID = "pdf_a_2b"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "PDF/A-2b",
    "validation": ["pdf_a_2b_conformance"],
    "not_enough": ["opens_as_pdf", "fpdf_default_export"],
    "price_eur_hint": {"min": 7.90, "max": 14.90},
}


def execute_pdf_a_2b(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "pdf_a_2b ROADMAP"}


def validate_pdf_a_2b(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "pdf_a_2b validator ROADMAP"}
