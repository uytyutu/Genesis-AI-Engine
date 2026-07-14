"""Project Bridge router — universal entry for all project types."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.execution.project_bridge.commerce import (
    try_explicit_approval,
    try_purchase_inquiry,
    try_soft_satisfaction,
)
from app.execution.project_bridge.company_memory import (
    apply_service_expansion,
    detect_service_expansion,
    expansion_intro,
    load_company_memory,
    sync_company_memory,
)
from app.execution.project_bridge.context import project_service_id
from app.execution.project_executors.base import ProjectRouteContext
from app.execution.project_executors.registry import (
    detect_project_intent,
    get_executor,
    resolve_service_id,
)


def try_project_execution(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    attachment_files: list[dict[str, Any]] | None = None,
    ui_locale: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    """
    Universal project path — commerce + journey + executor.
    Returns None when goal is not a project request.
    """
    files = attachment_files or []

    satisfied = try_soft_satisfaction(goal, visitor_id=visitor_id, memory_dir=memory_dir)
    if satisfied:
        return satisfied

    approved = try_explicit_approval(goal, visitor_id=visitor_id, memory_dir=memory_dir)
    if approved:
        return approved

    purchase = try_purchase_inquiry(goal, visitor_id=visitor_id, memory_dir=memory_dir)
    if purchase:
        return purchase

    service_id = resolve_service_id(goal, memory_dir=memory_dir, visitor_id=visitor_id)
    if not service_id:
        intent = detect_project_intent(goal)
        if not intent:
            return None
        service_id = str(intent["service_id"])

    expansion_mode = False
    company_memory = load_company_memory(memory_dir, visitor_id)
    intent = detect_project_intent(goal)
    if intent and company_memory and company_memory.knows_company():
        new_svc = str(intent["service_id"])
        if detect_service_expansion(
            goal,
            memory_dir=memory_dir,
            visitor_id=visitor_id,
            new_service_id=new_svc,
        ):
            expansion_mode = True
            company_memory = apply_service_expansion(memory_dir, visitor_id, new_svc)
            service_id = new_svc

    try:
        from app.integration.project_platform.service import ProjectPlatformService

        if expansion_mode:
            ProjectPlatformService(memory_dir).bootstrap_from_message(visitor_id, goal)
            sync_company_memory(memory_dir, visitor_id)
        else:
            ProjectPlatformService(memory_dir).bootstrap_from_message(visitor_id, goal)
    except Exception:
        pass

    executor = get_executor(service_id)
    if not project_service_id(memory_dir, visitor_id) and not executor.detect_new_request(goal):
        if not detect_project_intent(goal):
            return None

    if expansion_mode and company_memory:
        intro = expansion_intro(company_memory, service_id)
        ctx = ProjectRouteContext(
            goal=goal,
            visitor_id=visitor_id,
            memory_dir=memory_dir,
            service_id=service_id,
            attachment_files=files,
            history=history,
            ui_locale=ui_locale,
            company_memory=company_memory,
            expansion_mode=True,
        )
        routed = executor.try_route(ctx)
        if routed:
            routed["answer"] = f"{intro}\n\n{routed['answer']}"
            routed.setdefault("context", {})["expansion_mode"] = True
            routed["context"]["company_name"] = company_memory.company_name
            return routed
        return {
            "answer": intro,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "context": {
                "expansion_mode": True,
                "service_id": service_id,
                "company_name": company_memory.company_name,
            },
        }

    ctx = ProjectRouteContext(
        goal=goal,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        service_id=service_id,
        attachment_files=files,
        history=history,
        ui_locale=ui_locale,
        company_memory=company_memory,
        expansion_mode=expansion_mode,
    )
    result = executor.try_route(ctx)
    if result:
        try:
            sync_company_memory(memory_dir, visitor_id)
        except Exception:
            pass
    return result
