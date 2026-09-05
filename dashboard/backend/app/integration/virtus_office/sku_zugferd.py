"""ZUGFeRD / Factur-X SKU contract — ROADMAP until PDF+embedded XML validated."""

from __future__ import annotations

from typing import Any

SKU_ID = "zugferd"
SKU_ENABLED = False
EXECUTOR_IMPLEMENTED = False
VALIDATOR_IMPLEMENTED = False

SKU_CONTRACT: dict[str, Any] = {
    "id": SKU_ID,
    "enabled": SKU_ENABLED,
    "executor_required": True,
    "validator_required": True,
    "high_risk": True,
    "output": "PDF with embedded invoice XML (ZUGFeRD/Factur-X profile)",
    "validation": ["pdf_open", "embedded_xml", "xml_schema", "profile_match"],
    "delivery": "only_if_validator_PASS",
    "depends_on": ["invoice_extract", "xrechnung_or_cii_xml"],
    "price_eur_hint": {"min": 14.90, "max": 29.90},
}


def execute_zugferd(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "error": "not_implemented", "detail": "ZUGFeRD executor ROADMAP"}


def validate_zugferd(**_kwargs: Any) -> dict[str, Any]:
    return {"ok": False, "passed": False, "detail": "ZUGFeRD validator ROADMAP"}
