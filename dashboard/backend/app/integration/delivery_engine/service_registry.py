"""Service registry — capability → service, execution profiles (no per-service UX forks)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.product_line import (
    SERVICE_APP,
    SERVICE_AUTOMATION,
    SERVICE_BUSINESS_PLAN,
    SERVICE_CHATBOT,
    SERVICE_CRM,
    SERVICE_DOCUMENT_ANALYSIS,
    SERVICE_PRESENTATION,
    SERVICE_WEBSITE,
    artifact_label_ru,
    service_label_ru,
)

CAPABILITY_TO_SERVICE: dict[str, str] = {
    "generate_site": SERVICE_WEBSITE,
    "analyze_business_document": SERVICE_DOCUMENT_ANALYSIS,
    "filesystem_write": SERVICE_BUSINESS_PLAN,
}

_SERVICE_HINTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(сайт|лендинг|website)", re.I), SERVICE_WEBSITE),
    (re.compile(r"(бизнес[- ]?план)", re.I), SERVICE_BUSINESS_PLAN),
    (re.compile(r"(презентац)", re.I), SERVICE_PRESENTATION),
    (re.compile(r"(crm)", re.I), SERVICE_CRM),
    (re.compile(r"(автоматизац)", re.I), SERVICE_AUTOMATION),
    (re.compile(r"(чат[- ]?бот|бот)", re.I), SERVICE_CHATBOT),
    (re.compile(r"(приложени|application)", re.I), SERVICE_APP),
)


def service_for_capability(capability_id: str, *, goal: str = "") -> str:
    if capability_id in CAPABILITY_TO_SERVICE:
        sid = CAPABILITY_TO_SERVICE[capability_id]
        if capability_id == "filesystem_write":
            for pattern, service_id in _SERVICE_HINTS:
                if pattern.search(goal):
                    return service_id
        return sid
    for pattern, service_id in _SERVICE_HINTS:
        if pattern.search(goal):
            return service_id
    return SERVICE_WEBSITE


def execution_profile(capability_id: str) -> dict[str, Any]:
    """Shared execution metadata — same shape for every capability."""
    return {
        "capability_id": capability_id,
        "artifact_kind": _artifact_kind(capability_id),
        "supports_preview": capability_id in ("generate_site", "analyze_business_document"),
        "supports_revision": True,
    }


def _artifact_kind(capability_id: str) -> str:
    return {
        "generate_site": "website",
        "analyze_business_document": "documents",
        "filesystem_write": "file",
    }.get(capability_id, "deliverable")


def service_display(service_id: str) -> dict[str, str]:
    return {
        "service_id": service_id,
        "label_ru": service_label_ru(service_id),
        "artifact_ru": artifact_label_ru(service_id),
    }
