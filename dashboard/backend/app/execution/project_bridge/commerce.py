"""Universal project commerce — approval, satisfaction, purchase (all services)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.integration.product_line import LIFECYCLE_APPROVAL, LIFECYCLE_CHOICE, service_label_ru

from app.execution.project_bridge.context import (
    existing_workspace_id,
    primary_preview_href,
    project_service_id,
    workspace_has_deliverable_preview,
)
from app.execution.project_bridge.lifecycle import (
    mark_project_lifecycle,
    project_client_approved,
)


_PROJECT_SOFT_SATISFACTION = re.compile(
    r"(?:^|\b)(?:мне\s+нравится|нравится\s+результат|выглядит\s+хорошо|"
    r"looks\s+good|i\s+like\s+it)(?:\b|[.!?,]|$)",
    re.IGNORECASE,
)
_PROJECT_EXPLICIT_APPROVAL = re.compile(
    r"(?:"
    r"да[,]?\s+всё\s+устраивает|да[,]?\s+все\s+устраивает|"
    r"всё\s+устраивает|все\s+устраивает|"
    r"устраивает\s+полностью|полностью\s+устраивает|"
    r"готов\s+заказать|готов\s+оформить|"
    r"yes[,]?\s+(?:all\s+good|everything\s+is\s+fine|i\s+approve)"
    r")",
    re.IGNORECASE,
)
_PROJECT_PURCHASE = re.compile(
    r"(?:хочу\s+заказать|хочу\s+оформить|готов\s+оплатить|оформить\s+заказ|"
    r"перейти\s+к\s+оплате|want\s+to\s+order|ready\s+to\s+pay)",
    re.IGNORECASE,
)


def _artifact_cta(service_id: str, preview_path: str) -> tuple[str, list[dict[str, Any]]]:
    from app.execution.project_executors.registry import get_executor

    executor = get_executor(service_id)
    label = executor.preview_open_label()
    return label, [
        {"href": preview_path, "label": label, "group": "artifacts", "available": True},
    ]


def try_soft_satisfaction(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    g = (goal or "").strip()
    if not g or _PROJECT_EXPLICIT_APPROVAL.search(g):
        return None
    if not _PROJECT_SOFT_SATISFACTION.search(g):
        return None
    ws_id = existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not workspace_has_deliverable_preview(memory_dir, ws_id):
        return None
    if project_client_approved(memory_dir, visitor_id):
        return None
    service_id = project_service_id(memory_dir, visitor_id) or "website"
    preview_path = primary_preview_href(
        memory_dir, ws_id, visitor_id, service_id=service_id
    )
    label, actions = _artifact_cta(service_id, preview_path)
    return {
        "answer": (
            "Отлично.\n"
            "Тогда давайте ещё раз спокойно посмотрим результат.\n"
            "Всё ли вас устраивает?\n"
            "Есть ли ещё что-нибудь, что вы хотели бы изменить?"
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": preview_path,
        "cta_label": label,
        "cta_actions": actions,
        "context": {"journey_step": "approval_check", "co_design": False},
    }


def try_explicit_approval(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    g = (goal or "").strip()
    if not g or not _PROJECT_EXPLICIT_APPROVAL.search(g):
        return None
    ws_id = existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not workspace_has_deliverable_preview(memory_dir, ws_id):
        return None
    service_id = project_service_id(memory_dir, visitor_id) or "website"
    mark_project_lifecycle(memory_dir, visitor_id, LIFECYCLE_APPROVAL)
    preview_path = primary_preview_href(
        memory_dir, ws_id, visitor_id, service_id=service_id
    )
    from app.integration.delivery_engine.handoff import build_order_href

    order_href = build_order_href(
        service_id=service_id,
        visitor_id=visitor_id,
        workspace_id=ws_id,
        purchase_type="one_time",
    )
    label = service_label_ru(service_id, fallback="проект").lower()
    _, actions = _artifact_cta(service_id, preview_path)
    actions.append(
        {"href": order_href, "label": "📋 Оформить проект", "group": "next", "available": True}
    )
    return {
        "answer": (
            "Отлично.\n"
            f"Тогда фиксируем именно эту версию {label}.\n"
            "Следующий шаг — оформить проект, после чего мы подготовим его к передаче.\n\n"
            "Когда будете готовы — напишите «хочу заказать» или откройте оформление."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": order_href,
        "cta_label": "📋 Оформить проект",
        "cta_actions": actions,
        "context": {"journey_step": "approval", "co_design": False},
    }


def try_purchase_inquiry(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    if not _PROJECT_PURCHASE.search((goal or "").strip()):
        return None
    ws_id = existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not workspace_has_deliverable_preview(memory_dir, ws_id):
        return None
    service_id = project_service_id(memory_dir, visitor_id) or "website"
    preview_path = primary_preview_href(
        memory_dir, ws_id, visitor_id, service_id=service_id
    )
    label, actions = _artifact_cta(service_id, preview_path)
    if not project_client_approved(memory_dir, visitor_id):
        return {
            "answer": (
                "Прежде чем оформить заказ — давайте убедимся, что текущая версия "
                "вас полностью устраивает.\n\n"
                "Посмотрите результат ещё раз. Если всё хорошо — напишите "
                "«да, всё устраивает»."
            ),
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": preview_path,
            "cta_label": label,
            "cta_actions": actions,
            "context": {"journey_step": "approval_required"},
        }
    from app.integration.delivery_engine.handoff import build_order_href

    order_href = build_order_href(
        service_id=service_id,
        visitor_id=visitor_id,
        workspace_id=ws_id,
        purchase_type="one_time",
    )
    svc_label = service_label_ru(service_id, fallback="проект").lower()
    actions.append(
        {"href": order_href, "label": "📋 Оформить проект", "group": "next", "available": True}
    )
    mark_project_lifecycle(memory_dir, visitor_id, LIFECYCLE_CHOICE)
    return {
        "answer": (
            "Отлично.\n"
            f"Тогда фиксируем именно эту версию {svc_label}.\n"
            "Следующий шаг — оформить проект, после чего мы подготовим его к передаче."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": order_href,
        "cta_label": "📋 Оформить проект",
        "cta_actions": actions,
        "context": {"journey_step": "order"},
    }
