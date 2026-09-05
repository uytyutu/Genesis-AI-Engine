"""PDF/UA SKU contract — ROADMAP / last; accessibility tagged PDF is a separate engineering track."""

from __future__ import annotations

from typing import Any

SKU_ID = "pdf_ua"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "PDF/UA (tagged accessible PDF)",
    "validation": ["tagged_structure", "pdf_ua_conformance"],
    "note": "Do not Live until full accessibility validator exists.",
    "price_eur_hint": {"min": 14.90, "max": 39.90},
}


def execute_pdf_ua(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "pdf_ua ROADMAP"}


def validate_pdf_ua(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "pdf_ua validator ROADMAP"}
