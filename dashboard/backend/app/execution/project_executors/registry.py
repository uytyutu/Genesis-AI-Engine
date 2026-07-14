"""Executor registry — new product = one executor file + register_spec()."""

from __future__ import annotations

import re
from typing import Any

from app.integration.product_line import (
    SERVICE_AI_EMPLOYEE,
    SERVICE_APP,
    SERVICE_AUTOMATION,
    SERVICE_BUSINESS_PLAN,
    SERVICE_CHATBOT,
    SERVICE_CRM,
    SERVICE_DOCUMENT_ANALYSIS,
    SERVICE_PRESENTATION,
    SERVICE_SEO,
    SERVICE_WEBSITE,
)

from app.execution.project_executors.base import ProjectExecutor
from app.execution.project_executors.spec import ExecutorSpec, all_specs, register_spec

_CREATE_INTENT = re.compile(
    r"(?:создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)",
    re.I,
)

# Core intents — executors may add more via register_spec(intent_patterns=...)
_BASE_INTENT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(seo|сео|поисков).{0,20}(оптимиз|продвижен)", re.I), SERVICE_SEO),
    (re.compile(r"(сайт|лендинг|landing|website|webseite)", re.I), SERVICE_WEBSITE),
    (re.compile(r"(бизнес[- ]?план|business\s*plan)", re.I), SERVICE_BUSINESS_PLAN),
    (re.compile(r"(презентац|presentation|pitch)", re.I), SERVICE_PRESENTATION),
    (
        re.compile(r"(анализ|разбор).{0,24}(документ|pdf|отчёт)", re.I),
        SERVICE_DOCUMENT_ANALYSIS,
    ),
    (re.compile(r"(автоматиз|automation|отдел\s+продаж)", re.I), SERVICE_AUTOMATION),
    (re.compile(r"(чат[- ]?бот|chatbot|бот для)", re.I), SERVICE_CHATBOT),
    (re.compile(r"(?:\bcrm\b|система\s+учёта\s+клиент)", re.I), SERVICE_CRM),
    (re.compile(r"(приложени|application|app\b)", re.I), SERVICE_APP),
    (
        re.compile(
            r"(?:ai[- ]?сотрудник|цифровой\s+сотрудник|ai\s+employee).{0,32}(?:продаж|sales)",
            re.I,
        ),
        SERVICE_AI_EMPLOYEE,
    ),
    (
        re.compile(r"(?:ai[- ]?сотрудник|цифровой\s+сотрудник)", re.I),
        SERVICE_AI_EMPLOYEE,
    ),
    (
        re.compile(r"автоматиз.{0,24}(?:заявк|обработк|входящ)", re.I),
        SERVICE_AUTOMATION,
    ),
)


def _load_plugins() -> None:
    """Import executor modules once — each calls register_spec on load."""
    from app.execution.project_executors import inventory_executor  # noqa: F401
    from app.execution.project_executors.universal import UniversalProjectExecutor
    from app.execution.project_executors.website import WebsiteProjectExecutor

    if not any(s.service_ids == frozenset({SERVICE_WEBSITE}) for s in all_specs()):
        register_spec(
            ExecutorSpec(
                executor=WebsiteProjectExecutor(),
                service_ids=frozenset({SERVICE_WEBSITE}),
            )
        )
    universal_ids = frozenset(
        {
            SERVICE_CRM,
            SERVICE_AUTOMATION,
            SERVICE_SEO,
            SERVICE_CHATBOT,
            SERVICE_AI_EMPLOYEE,
            SERVICE_BUSINESS_PLAN,
            SERVICE_PRESENTATION,
            SERVICE_APP,
            "marketing_strategy",
            "logo_design",
        }
    )
    if not any(s.executor.service_id == "universal" for s in all_specs()):
        register_spec(
            ExecutorSpec(
                executor=UniversalProjectExecutor(),
                service_ids=universal_ids,
            )
        )


def _ensure_loaded() -> None:
    if not all_specs():
        _load_plugins()


def detect_project_intent(text: str) -> dict[str, Any] | None:
    """All deliverable intents — base patterns + executor plug-ins."""
    _ensure_loaded()
    t = (text or "").strip()
    if len(t) < 4:
        return None
    has_create = bool(_CREATE_INTENT.search(t))

    for spec in all_specs():
        for pattern, service_id in spec.intent_patterns:
            if pattern.search(t) and (has_create or len(t) > 24):
                return {
                    "service_id": service_id,
                    "confidence": "high" if has_create else "medium",
                }

    for pattern, service_id in _BASE_INTENT_PATTERNS:
        if pattern.search(t) and (has_create or len(t) > 24):
            return {
                "service_id": service_id,
                "confidence": "high" if has_create else "medium",
            }

    if has_create and re.search(r"проект", t, re.I):
        return {"service_id": SERVICE_WEBSITE, "confidence": "medium"}
    return None


def get_executor(service_id: str) -> ProjectExecutor:
    _ensure_loaded()
    for spec in all_specs():
        if spec.matches_service(service_id):
            return spec.executor
    for spec in all_specs():
        if spec.executor.service_id == "universal":
            return spec.executor
    from app.execution.project_executors.universal import UniversalProjectExecutor

    return UniversalProjectExecutor()


def list_executors() -> list[ProjectExecutor]:
    _ensure_loaded()
    return [spec.executor for spec in all_specs()]


def resolve_service_id(goal: str, *, memory_dir, visitor_id: str) -> str | None:
    from app.execution.project_bridge.company_memory import (
        detect_service_expansion,
        load_company_memory,
    )
    from app.execution.project_bridge.context import project_service_id

    intent = detect_project_intent(goal)
    existing = project_service_id(memory_dir, visitor_id)
    if intent:
        new_svc = str(intent["service_id"])
        if existing and new_svc != existing:
            if detect_service_expansion(
                goal,
                memory_dir=memory_dir,
                visitor_id=visitor_id,
                new_service_id=new_svc,
            ):
                return new_svc
        if existing:
            return existing
        return new_svc
    if existing:
        return existing
    return None
