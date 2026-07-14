"""Conversation vs Project — natural project birth, not mode switch."""

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
    SERVICE_SEO,
    SERVICE_WEBSITE,
)
from app.integration.vector_intelligence.types import UNIFIED_VECTOR_PRINCIPLE

_DELIVERABLE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(seo|сео|поисков).{0,20}(оптимиз|продвижен)", re.I), SERVICE_SEO),
    (re.compile(r"(сайт|лендинг|landing|website|webseite)", re.I), SERVICE_WEBSITE),
    (re.compile(r"(бизнес[- ]?план|business\s*plan)", re.I), SERVICE_BUSINESS_PLAN),
    (re.compile(r"(презентац|presentation|pitch)", re.I), SERVICE_PRESENTATION),
    (re.compile(r"(анализ|разбор).{0,24}(документ|pdf|отчёт)", re.I), SERVICE_DOCUMENT_ANALYSIS),
    (re.compile(r"(автоматиз|automation|отдел\s+продаж)", re.I), SERVICE_AUTOMATION),
    (re.compile(r"(чат[- ]?бот|chatbot|бот для)", re.I), SERVICE_CHATBOT),
    (re.compile(r"(?:\bcrm\b|система\s+учёта\s+клиент)", re.I), SERVICE_CRM),
    (re.compile(r"(приложени|application|app\b)", re.I), SERVICE_APP),
)

_CREATE_INTENT = re.compile(
    r"(создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)",
    re.I,
)


def detect_deliverable_intent(text: str) -> dict[str, Any] | None:
    """Return service_id when user wants a finished deliverable — not casual chat."""
    from app.execution.project_executors.registry import detect_project_intent

    return detect_project_intent(text)


def project_mode_rules_for_vector() -> str:
    return UNIFIED_VECTOR_PRINCIPLE + """

## Проект в Virtus Core

Проект — рабочий стол для результатов (сайт, документ, план), не отдельный бот.
- Появляется **естественно**, когда разговор созрел или клиент согласился сохранить.
- До этого — обычный диалог: ресторан, космос, ужин — без навязчивого «создать проект».
- После создания — Vector помнит этап, версии, артефакты; на сторонние вопросы отвечает полно, затем мягко возвращает к делу если уместно.
- Артефакты живут в карточке проекта (Preview, файлы, версии), не только в чате."""
