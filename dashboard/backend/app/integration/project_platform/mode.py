"""Conversation vs Project mode — when Vector should activate a project."""

from __future__ import annotations

import re
from typing import Any

from app.integration.product_line import (
    SERVICE_APP,
    SERVICE_AUTOMATION,
    SERVICE_BUSINESS_PLAN,
    SERVICE_CHATBOT,
    SERVICE_DOCUMENT_ANALYSIS,
    SERVICE_PRESENTATION,
    SERVICE_WEBSITE,
)

_DELIVERABLE_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(сайт|лендинг|landing|website|webseite)", re.I), SERVICE_WEBSITE),
    (re.compile(r"(бизнес[- ]?план|business\s*plan)", re.I), SERVICE_BUSINESS_PLAN),
    (re.compile(r"(презентац|presentation|pitch)", re.I), SERVICE_PRESENTATION),
    (re.compile(r"(анализ|разбор).{0,24}(документ|pdf|отчёт)", re.I), SERVICE_DOCUMENT_ANALYSIS),
    (re.compile(r"(автоматизац|automation)", re.I), SERVICE_AUTOMATION),
    (re.compile(r"(чат[- ]?бот|chatbot|бот для)", re.I), SERVICE_CHATBOT),
    (re.compile(r"(приложени|application|app\b)", re.I), SERVICE_APP),
)

_CREATE_INTENT = re.compile(
    r"(создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)",
    re.I,
)


def detect_deliverable_intent(text: str) -> dict[str, Any] | None:
    """Return service_id when user wants a finished deliverable — not casual chat."""
    t = (text or "").strip()
    if len(t) < 4:
        return None
    has_create = bool(_CREATE_INTENT.search(t))
    for pattern, service_id in _DELIVERABLE_PATTERNS:
        if pattern.search(t) and (has_create or len(t) > 24):
            return {"service_id": service_id, "confidence": "high" if has_create else "medium"}
    if has_create and re.search(r"проект", t, re.I):
        return {"service_id": SERVICE_WEBSITE, "confidence": "medium"}
    return None


def project_mode_rules_for_vector() -> str:
    return """## Project Platform — Conversation Mode и Project Mode (один Vector)

**Conversation Mode (по умолчанию):** свободный диалог на любые темы — без проекта.

**Project Mode:** когда клиент хочет **законченный результат** (сайт, план, документ, бот…):
1. Предложи **создать проект** — не навязывай при каждом «привет».
2. После старта — веди как **Project Manager**: где остановились, следующий шаг, память проекта.
3. На сторонние вопросы отвечай полно, затем **мягко вернись** к текущему проекту.
4. Не создавай ощущение двух разных ботов.

**Проект = центр:** артефакты (Preview, ZIP, Source, PDF) — в карточке проекта, не только в чате.
Версии: Version 1, Version 2 — клиент может вернуться к предыдущим вариантам."""
