"""Universal project executor — CRM, automation, SEO, chatbot, …"""

from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any

from app.execution.project_bridge.context import (
    combined_project_dialog,
    primary_preview_href,
    record_project_execution,
    workspace_for_visitor,
    workspace_file_href,
)
from app.execution.workspace import ExecutionWorkspaceStore
from app.execution.project_executors.vector_pm import (
    pm_company_step,
    pm_first_concept_ready,
    pm_goal_step,
    pm_preview_open_label,
    pm_structure_step,
    pm_workspace_title,
)
from app.integration.product_line import SERVICE_AUTOMATION, SERVICE_CRM, SERVICE_WEBSITE
from app.integration.project_platform.journey_state import extract_company_name
from app.integration.project_platform.mode import detect_deliverable_intent

from app.execution.project_executors.base import ProjectExecutor, ProjectRouteContext

_CO_DESIGN_ORDER: tuple[str, ...] = ("company", "goal", "structure")

_SCOPE_HINT = re.compile(
    r"(?:отдел|склад|компани|фирм|бизнес|команда|процесс|sales|warehouse|team)",
    re.IGNORECASE,
)
_GOAL_HINT = re.compile(
    r"(?:нужно|должен|чтобы|цель|задача|автоматиз|управля|учёт|заявк|лид|клиент)",
    re.IGNORECASE,
)
_REVISION = re.compile(
    r"(?:правк|измени|поменя|добавь|убери|сделай|переделай|доработ|"
    r"компактн|отзыв|блок|шапк|цвет|логотип|структур|этап|воронк|пол)",
    re.IGNORECASE,
)
_STRUCTURE_CONFIRM = re.compile(
    r"(?:хорошо[,]?\s+продолжаем|давайте\s+продолжим|можно\s+продолжать|"
    r"готов[аы]?\s+к\s+концепции|продолжаем)",
    re.IGNORECASE,
)
_CREATE_VERB = re.compile(
    r"(?:создай|создать|сделай|сделать|нужен|нужна|хочу|под ключ|build|create|make)",
    re.IGNORECASE,
)


class UniversalProjectExecutor:
    service_id = "universal"

    def matches(self, service_id: str) -> bool:
        return service_id != SERVICE_WEBSITE

    def detect_new_request(self, goal: str) -> bool:
        intent = detect_deliverable_intent(goal)
        return bool(intent and intent["service_id"] != SERVICE_WEBSITE)

    def preview_open_label(self) -> str:
        return pm_preview_open_label()

    def workspace_title(self) -> str:
        return pm_workspace_title()

    def try_route(self, ctx: ProjectRouteContext) -> dict[str, Any] | None:
        if _REVISION.search(ctx.goal) and self._has_preview(ctx) and not ctx.expansion_mode:
            return self._run_revision(ctx)
        if self._has_preview(ctx) and not ctx.expansion_mode:
            return None
        gated = self._maybe_gate_concept(ctx)
        if gated:
            return gated
        if self._co_design_complete(ctx):
            return self._run_first_concept(ctx)
        return None

    def _has_preview(self, ctx: ProjectRouteContext) -> bool:
        from app.execution.project_bridge.context import workspace_has_deliverable_preview

        ws_id = workspace_for_visitor(
            ctx.memory_dir, ctx.visitor_id, title=self.workspace_title()
        )
        return workspace_has_deliverable_preview(ctx.memory_dir, ws_id)

    def _co_design_flags(
        self,
        combined: str,
        *,
        service_id: str,
        ctx: ProjectRouteContext | None = None,
    ) -> dict[str, bool]:
        text = combined or ""
        mem = getattr(ctx, "company_memory", None) if ctx else None
        expansion = bool(getattr(ctx, "expansion_mode", False)) if ctx else False
        company = bool(extract_company_name(text)) or bool(
            mem and getattr(mem, "company_name", None)
        )
        if expansion and mem and getattr(mem, "company_name", None):
            company = True
        intent = detect_deliverable_intent(text)
        goal = (
            bool(_GOAL_HINT.search(text))
            or len(text.split()) > 8
            or bool(intent and intent.get("service_id") == service_id)
            or expansion
        )
        structure = bool(_STRUCTURE_CONFIRM.search(text)) or expansion
        return {"company": company, "goal": goal, "structure": structure}

    def _next_gap(self, combined: str, *, service_id: str, ctx: ProjectRouteContext | None = None) -> str | None:
        flags = self._co_design_flags(combined, service_id=service_id, ctx=ctx)
        for step in _CO_DESIGN_ORDER:
            if not flags.get(step):
                return step
        return None

    def _co_design_complete(self, ctx: ProjectRouteContext) -> bool:
        combined = combined_project_dialog(
            ctx.goal,
            visitor_id=ctx.visitor_id,
            memory_dir=ctx.memory_dir,
            history=ctx.history,
        )
        return self._next_gap(combined, service_id=ctx.service_id, ctx=ctx) is None

    def _maybe_gate_concept(self, ctx: ProjectRouteContext) -> dict[str, Any] | None:
        combined = combined_project_dialog(
            ctx.goal,
            visitor_id=ctx.visitor_id,
            memory_dir=ctx.memory_dir,
            history=ctx.history,
        )
        gap = self._next_gap(combined, service_id=ctx.service_id, ctx=ctx)
        if not gap:
            return None
        return self._journey_step_response(gap, combined=combined, ctx=ctx)

    def _journey_step_response(
        self,
        gap: str,
        *,
        combined: str,
        ctx: ProjectRouteContext,
    ) -> dict[str, Any]:
        mem = ctx.company_memory
        company = (
            (getattr(mem, "company_name", None) if mem else None)
            or extract_company_name(combined)
            or "вашего бизнеса"
        )
        if ctx.expansion_mode and gap == "company":
            gap = "goal"
        questions = {
            "company": pm_company_step(),
            "goal": pm_goal_step(company),
            "structure": pm_structure_step(company),
        }
        answer = questions.get(gap, pm_company_step())
        self._sync_project(ctx, gap=gap, combined=combined)
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "context": {"journey_step": gap, "co_design": True, "service_id": ctx.service_id},
        }

    def _sync_project(self, ctx: ProjectRouteContext, *, gap: str, combined: str) -> None:
        try:
            from app.integration.project_platform.service import ProjectPlatformService
            from app.integration.project_platform.store import ProjectStore

            svc = ProjectPlatformService(ctx.memory_dir)
            svc.bootstrap_from_message(ctx.visitor_id, ctx.goal or combined)
            state = svc.get_for_visitor(ctx.visitor_id)
            ws_id = (state.get("project") or {}).get("workspace_id")
            hints = {
                "company": "узнаём компанию и контекст",
                "goal": "уточняем цель проекта",
                "structure": "собираем требования для первой концепции",
            }
            if ws_id:
                record = ProjectStore(ctx.memory_dir).load(ws_id)
                if record and record.service_id == SERVICE_WEBSITE:
                    record.service_id = ctx.service_id  # type: ignore[assignment]
                if record:
                    record.next_step_hint = hints.get(gap, "")
                    ProjectStore(ctx.memory_dir).save(record)
        except Exception:
            pass

    def _run_first_concept(self, ctx: ProjectRouteContext) -> dict[str, Any]:
        combined = combined_project_dialog(
            ctx.goal,
            visitor_id=ctx.visitor_id,
            memory_dir=ctx.memory_dir,
            history=ctx.history,
        )
        company = extract_company_name(combined) or "Проект"
        concept = self._build_concept_md(company, combined, ctx.service_id)
        workspace_id = workspace_for_visitor(
            ctx.memory_dir,
            ctx.visitor_id,
            title=pm_workspace_title(),
        )
        store = ExecutionWorkspaceStore(ctx.memory_dir)
        files_root = store.path_for(workspace_id, "files")
        preview_dir = store.path_for(workspace_id, "artifacts", "preview")
        files_root.mkdir(parents=True, exist_ok=True)
        preview_dir.mkdir(parents=True, exist_ok=True)
        (files_root / "concept.md").write_text(concept, encoding="utf-8")
        (preview_dir / "concept.md").write_text(concept, encoding="utf-8")

        artifact_id = f"concept-{uuid.uuid4().hex[:8]}"
        outputs = {
            "artifact_id": artifact_id,
            "files": ["concept.md", "preview/concept.md"],
            "preview_url": workspace_file_href(workspace_id, ctx.visitor_id, "concept.md"),
        }
        record_project_execution(
            visitor_id=ctx.visitor_id,
            workspace_id=workspace_id,
            capability_id="project_concept",
            outputs=outputs,
            goal=combined,
            memory_dir=ctx.memory_dir,
        )
        preview_path = primary_preview_href(
            ctx.memory_dir, workspace_id, ctx.visitor_id, service_id=ctx.service_id
        )
        answer = pm_first_concept_ready()
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": preview_path,
            "cta_label": self.preview_open_label(),
            "cta_actions": [
                {
                    "href": preview_path,
                    "label": self.preview_open_label(),
                    "group": "artifacts",
                    "available": True,
                },
                {
                    "href": "#action:Хочу внести правки",
                    "label": "✏ Продолжить редактирование",
                    "group": "next",
                    "available": True,
                },
            ],
            "context": {
                "journey_step": "draft",
                "co_design": False,
                "service_id": ctx.service_id,
                "artifact_type": "concept",
            },
        }

    def _run_revision(self, ctx: ProjectRouteContext) -> dict[str, Any] | None:
        combined = combined_project_dialog(
            ctx.goal,
            visitor_id=ctx.visitor_id,
            memory_dir=ctx.memory_dir,
            history=ctx.history,
        )
        if len(combined) < 24:
            return None
        try:
            from app.integration.project_platform.service import ProjectPlatformService

            ProjectPlatformService(ctx.memory_dir).bootstrap_from_message(
                ctx.visitor_id, ctx.goal
            )
        except Exception:
            pass
        revision_note = (ctx.goal or "").strip()[:200]
        brief = f"{combined}\n\nПравка клиента: {revision_note}"
        return self._run_first_concept(
            ProjectRouteContext(
                goal=brief,
                visitor_id=ctx.visitor_id,
                memory_dir=ctx.memory_dir,
                service_id=ctx.service_id,
                attachment_files=ctx.attachment_files,
                history=ctx.history,
                ui_locale=ctx.ui_locale,
            )
        )

    def _build_concept_md(
        self,
        company: str,
        brief: str,
        service_id: str,
    ) -> str:
        sections = {
            SERVICE_CRM: [
                "## Воронка продаж",
                "- Лиды → квалификация → сделка",
                "## Поля и этапы",
                "- Согласуем с вами на следующем шаге",
                "## Интеграции",
                "- Email, телефония — по необходимости",
            ],
            SERVICE_AUTOMATION: [
                "## Процесс",
                "- Текущие ручные шаги → автоматические",
                "## Триггеры",
                "- События склада / заказов",
                "## Результат",
                "- Меньше ручной работы, прозрачный статус",
            ],
        }
        body = sections.get(service_id, [
            "## Структура",
            "- Согласовано с вашим запросом",
            "## Следующий шаг",
            "- Правки до полного согласования",
        ])
        lines = [
            f"# Концепция проекта — {company}",
            "",
            "## Задача",
            brief[:1200],
            "",
            *body,
            "",
            "---",
            "*Первая версия в проекте Virtus Core. Vector доработает по вашим правкам.*",
        ]
        return "\n".join(lines)
