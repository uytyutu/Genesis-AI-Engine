"""Searchable PDF SKU contract — ROADMAP until OCR text-layer PDF is validated."""

from __future__ import annotations

from typing import Any

SKU_ID = "searchable_pdf"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "PDF with searchable/copyable text layer over original pages",
    "validation": ["page_count_match", "text_extractable", "visual_pages_present"],
    "not_enough": ["ocr_text_in_chat_only"],
    "price_eur_hint": {"min": 9.90, "max": 29.90},
}


def execute_searchable_pdf(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "searchable_pdf ROADMAP"}


def validate_searchable_pdf(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "searchable_pdf validator ROADMAP"}
