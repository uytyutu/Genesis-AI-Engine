"""Fillable PDF (AcroForm) SKU contract — ROADMAP until fields are machine-verified."""

from __future__ import annotations

from typing import Any

SKU_ID = "fillable_pdf"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "PDF with AcroForm fields (text/checkbox/dropdown/date/signature)",
    "validation": ["acroform_present", "fields_fillable", "opens_in_reader"],
    "not_enough": ["docx_form", "instructions_only"],
    "price_eur_hint": {"min": 19.90, "max": 49.90},
}


def execute_fillable_pdf(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "fillable_pdf ROADMAP"}


def validate_fillable_pdf(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "fillable_pdf validator ROADMAP"}
