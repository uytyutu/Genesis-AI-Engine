"""Workforce routing — last step, invisible to the user. Models are replaceable executors."""

from __future__ import annotations

import re
from typing import Literal

from app.integration.genesis_brain.layers.conversation_type import ConversationKind, is_business_mode, is_product_mode
from app.integration.genesis_brain.workforce_performance import WorkforceTask
from app.integration.vector_intelligence.types import VectorAction, VectorNeed

WorkforceTier = Literal[1, 2, 3]
WorkforceChannel = Literal[
    "fast_dialog",
    "deep_reasoning",
    "code",
    "documents",
    "vision",
    "execution",
    "project_platform",
]

_LEGAL = re.compile(
    r"\b(?:договор|vertrag|юрид|legal|nda|лицензи|соглашени|устав|compliance)\b",
    re.I,
)
_DOCUMENT = re.compile(
    r"\b(?:pdf|документ|отчёт|отчет|excel|word|анализ\s+файл|бизнес[- ]?план)\b",
    re.I,
)
_ARCHITECTURE = re.compile(
    r"\b(?:архитектур|saas|микросервис|crm|erp|инфраструктур|system\s+design)\b",
    re.I,
)
_MULTI_DOMAIN = re.compile(
    r"(?:бизнес[- ]?план|юрид|архитектур|документ|сайт).{0,80}(?:бизнес[- ]?план|юрид|архитектур|документ|сайт)",
    re.I | re.S,
)
_IMAGE = re.compile(r"\b(?:изображени|картинк|логотип|фото|нарисуй|сгенерир)\b", re.I)
_SITE = re.compile(r"\b(?:сайт|лендинг|landing|website|webseite)\b", re.I)

_CASUAL_KINDS = frozenset(
    {
        "casual_conversation",
        "humor",
        "philosophy",
        "science",
        "education",
        "general_question",
        "personal_reflection",
        "creative",
        "meta_correction",
    }
)


def select_workforce_channel(
    user_message: str,
    *,
    kind: ConversationKind,
    need: VectorNeed,
    action: VectorAction,
    has_attachments: bool = False,
    has_project: bool = False,
) -> WorkforceChannel:
    """Human-facing channel — never shown to user; maps to internal executors."""
    low = (user_message or "").lower()

    if action in ("execute", "manage_project") and (_SITE.search(low) or action == "manage_project"):
        if has_project or _SITE.search(low):
            return "project_platform"
    if _IMAGE.search(low):
        return "vision"
    if has_attachments or _DOCUMENT.search(low):
        return "documents"
    if kind == "programming" or re.search(r"\b(?:код|python|react|api|sql)\b", low, re.I):
        return "code"
    if _LEGAL.search(low) or _ARCHITECTURE.search(low) or _MULTI_DOMAIN.search(low):
        return "deep_reasoning"
    if need in ("advisor", "employee") and (is_business_mode(kind) or is_product_mode(kind)):
        return "deep_reasoning"
    if kind in _CASUAL_KINDS and len(low) < 120:
        return "fast_dialog"
    if len(low) > 400:
        return "deep_reasoning"
    return "fast_dialog"


def channel_to_task(channel: WorkforceChannel) -> tuple[WorkforceTask, WorkforceTier]:
    """Map invisible channel → legacy workforce task (replaceable implementation detail)."""
    mapping: dict[WorkforceChannel, tuple[WorkforceTask, WorkforceTier]] = {
        "fast_dialog": ("simple", 1),
        "deep_reasoning": ("complex", 2),
        "code": ("code", 2),
        "documents": ("complex", 2),
        "vision": ("complex", 2),
        "execution": ("sales", 1),
        "project_platform": ("conversation", 1),
    }
    return mapping.get(channel, ("conversation", 1))
