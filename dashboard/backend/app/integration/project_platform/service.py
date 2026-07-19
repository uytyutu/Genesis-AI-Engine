"""Project Platform orchestration — workspace + project.json + artifacts."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.execution.workspace import ExecutionWorkspaceStore, WorkspaceMeta
from app.integration.product_line import (
    LIFECYCLE_CONCEPT,
    LIFECYCLE_COLLABORATION,
    SERVICE_DOCUMENT_ANALYSIS,
    SERVICE_WEBSITE,
    service_label_ru,
)
from app.integration.project_platform.identity import (
    build_artifact_folders,
    build_identity,
    build_last_activity,
    build_next_action,
    build_progress,
    build_project_health,
    infer_description,
    infer_market,
)
from app.integration.project_platform.journey_state import (
    build_project_journey_state,
    journey_next_step_hint,
)
from app.integration.project_platform.mode import detect_deliverable_intent
from app.integration.project_platform.schema import (
    SECTION_DOCUMENTS,
    SECTION_FILES,
    SECTION_WEBSITE,
    ProjectArtifact,
    ProjectRecord,
    ProjectVersion,
    TimelineEvent,
)
from app.integration.project_platform.store import ProjectStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _visitor_map_path(memory_dir: Path) -> Path:
    return memory_dir / "execution" / "visitor_workspaces.json"


def resolve_workspace_id(memory_dir: Path, visitor_id: str) -> str | None:
    path = _visitor_map_path(memory_dir)
    if not path.is_file():
        return None
    try:
        mapping = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    ws_id = mapping.get(visitor_id)
    if not ws_id:
        return None
    if ExecutionWorkspaceStore(memory_dir).get(ws_id):
        return ws_id
    return None


def bind_visitor_workspace(memory_dir: Path, visitor_id: str, workspace_id: str) -> None:
    vid = (visitor_id or "anonymous").strip()[:64]
    path = _visitor_map_path(memory_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    mapping: dict[str, str] = {}
    if path.is_file():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                mapping = {str(k): str(v) for k, v in raw.items()}
        except (json.JSONDecodeError, OSError):
            mapping = {}
    mapping[vid] = workspace_id
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")


def _file_href(workspace_id: str, visitor_id: str, rel: str) -> str:
    q = quote(visitor_id, safe="")
    return f"/api/public/execution/workspace/{workspace_id}/files/{rel.lstrip('/')}?visitor_id={q}"


def _preview_href(workspace_id: str, visitor_id: str) -> str:
    q = quote(visitor_id, safe="")
    return f"/api/public/execution/preview/{workspace_id}?visitor_id={q}"


class ProjectPlatformService:
    PLATFORM_VERSION = "project-platform-v1"

    def __init__(self, memory_dir: Path) -> None:
        self._memory = memory_dir
        self._workspaces = ExecutionWorkspaceStore(memory_dir)
        self._projects = ProjectStore(memory_dir)

    def get_for_visitor(self, visitor_id: str, *, locale: str = "ru") -> dict[str, Any]:
        vid = (visitor_id or "anonymous").strip()[:64]
        ws_id = resolve_workspace_id(self._memory, vid)
        if not ws_id:
            return self._empty_state(vid, locale=locale)

        meta = self._workspaces.get(ws_id)
        if not meta:
            return self._empty_state(vid, locale=locale)

        record = self._projects.load(ws_id)
        if not record:
            record = self._projects.ensure_for_workspace(meta, visitor_id=vid)
        self._sync_artifacts_from_disk(record, vid)
        self._refresh_hints(record)
        self._projects.save(record)
        return self._public_payload(record, locale=locale)

    def enrich_with_project_state(self, response: dict[str, Any], visitor_id: str) -> dict[str, Any]:
        """Attach canonical Project State — single source of truth for panel sync."""
        state = self.get_for_visitor(visitor_id)
        out = dict(response)
        ctx = dict(out.get("context") or {})
        ctx["project_state"] = state
        out["context"] = ctx
        return out

    def activate_project(
        self,
        visitor_id: str,
        *,
        title: str,
        service_id: str,
    ) -> dict[str, Any]:
        vid = (visitor_id or "anonymous").strip()[:64]
        ws = self._ensure_workspace(vid, title=title)
        record = self._projects.ensure_for_workspace(
            ws,
            visitor_id=vid,
            title=title,
            service_id=service_id,
            activate_project=True,
        )
        record.lifecycle_phase = LIFECYCLE_CONCEPT
        record.active_section = _section_for_service(service_id)
        now = _utc_now()
        record.timeline.append(
            TimelineEvent(
                id=f"tl-{uuid.uuid4().hex[:8]}",
                type="concept",
                label="Проект активирован",
                at=now,
                detail=service_label_ru(service_id),
            )
        )
        record.updated_at = now
        self._projects.save(record)
        _apply_goal_context(record, title)
        self._projects.save(record)
        return self._public_payload(record)

    def bootstrap_from_message(self, visitor_id: str, message: str) -> dict[str, Any]:
        """PE-1 — create or update project from user message (fast, no LLM)."""
        vid = (visitor_id or "anonymous").strip()[:64]
        text = (message or "").strip()
        intent = detect_deliverable_intent(text)
        ws_id = resolve_workspace_id(self._memory, vid)

        if ws_id:
            meta = self._workspaces.get(ws_id)
            if meta:
                record = self._projects.load(ws_id) or self._projects.ensure_for_workspace(
                    meta, visitor_id=vid
                )
                if intent and record.mode == "conversation":
                    record.mode = "project"
                    record.lifecycle_phase = LIFECYCLE_CONCEPT
                    record.service_id = intent["service_id"]
                    record.active_section = _section_for_service(intent["service_id"])
                _apply_goal_context(record, text)
                record.updated_at = _utc_now()
                if text:
                    record.timeline.append(
                        TimelineEvent(
                            id=f"tl-{uuid.uuid4().hex[:8]}",
                            type="update",
                            label="Обновление проекта",
                            at=record.updated_at,
                            detail=text[:2000],
                        )
                    )
                self._refresh_hints(record)
                self._projects.save(record)
                return self._public_payload(record)

        if not intent:
            return self._empty_state(vid)

        title = _title_from_goal(text)
        if title in ("Мой проект", "") or len(title) < 6:
            title = service_label_ru(intent["service_id"], fallback="Новый проект")
        return self.activate_project(vid, title=title, service_id=intent["service_id"])

    def record_execution(
        self,
        *,
        visitor_id: str,
        workspace_id: str,
        capability_id: str,
        outputs: dict[str, Any],
        goal: str = "",
    ) -> None:
        meta = self._workspaces.get(workspace_id)
        if not meta:
            return
        vid = (visitor_id or "anonymous").strip()[:64]
        service_id = _service_for_capability(capability_id)
        record = self._projects.ensure_for_workspace(
            meta,
            visitor_id=vid,
            title=_title_from_goal(goal) or meta.title,
            service_id=service_id,
            activate_project=True,
        )
        record.mode = "project"
        record.lifecycle_phase = LIFECYCLE_COLLABORATION
        record.active_section = _section_for_service(service_id)
        _apply_goal_context(record, goal)

        version_num = len(record.versions) + 1
        now = _utc_now()
        artifacts = _artifacts_from_capability(
            capability_id,
            outputs,
            workspace_id=workspace_id,
            visitor_id=vid,
            version=version_num,
        )
        record.versions.append(
            ProjectVersion(
                version=version_num,
                label=f"Версия {version_num}",
                created_at=now,
                summary=_version_summary(capability_id, outputs),
                artifacts=artifacts,
            )
        )
        event_type = "generation" if capability_id == "generate_site" else "analysis"
        record.timeline.append(
            TimelineEvent(
                id=f"tl-{uuid.uuid4().hex[:8]}",
                type=event_type,
                label=f"Версия {version_num}",
                at=now,
                detail=record.versions[-1].summary,
            )
        )
        record.updated_at = now
        self._refresh_hints(record)
        self._projects.save(record)

    def _ensure_workspace(self, visitor_id: str, *, title: str) -> WorkspaceMeta:
        ws_id = resolve_workspace_id(self._memory, visitor_id)
        if ws_id:
            meta = self._workspaces.get(ws_id)
            if meta:
                return meta
        meta = self._workspaces.create(owner_id=visitor_id[:64], title=title)
        bind_visitor_workspace(self._memory, visitor_id, meta.workspace_id)
        return meta

    def _sync_artifacts_from_disk(self, record: ProjectRecord, visitor_id: str) -> None:
        if record.versions:
            return
        ws_id = record.workspace_id
        files_dir = self._workspaces.path_for(ws_id, "files")
        if not files_dir.is_dir():
            return
        found: list[ProjectArtifact] = []
        for path in sorted(files_dir.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(files_dir).as_posix()
            kind, section = _classify_file(rel)
            found.append(
                ProjectArtifact(
                    id=f"art-{uuid.uuid4().hex[:8]}",
                    kind=kind,
                    label=path.name,
                    href=_file_href(ws_id, visitor_id, rel),
                    section=section,
                    version=1,
                )
            )
        if not found:
            return
        record.versions.append(
            ProjectVersion(
                version=1,
                label="Версия 1",
                created_at=record.created_at or _utc_now(),
                summary="Импорт существующих файлов проекта",
                artifacts=found[:12],
            )
        )
        if record.mode == "conversation":
            record.mode = "project"
            record.lifecycle_phase = LIFECYCLE_COLLABORATION

    def _refresh_hints(self, record: ProjectRecord) -> None:
        if record.mode == "conversation":
            record.next_step_hint = (
                "Продолжайте разговор с Vector — когда появится результат, "
                "я предложу оформить его как проект."
            )
            return
        journey_hint = journey_next_step_hint(record)
        if journey_hint:
            record.next_step_hint = journey_hint
            return
        phase = record.lifecycle_phase
        if not record.versions:
            record.next_step_hint = (
                "Расскажите, что хотите получить — подготовлю первую версию."
            )
        elif phase == LIFECYCLE_CONCEPT:
            record.next_step_hint = (
                "Сегодня мы закончили первую версию. Посмотрите структуру — "
                "скажите, что изменить, и я подготовлю следующий шаг."
            )
        elif phase == LIFECYCLE_COLLABORATION:
            record.next_step_hint = (
                "Продолжаем правки вместе. После согласования подготовлю финальные материалы."
            )
        else:
            record.next_step_hint = "Я веду проект до согласованного результата — напишите, если нужна помощь."

    def _empty_state(self, visitor_id: str, *, locale: str = "ru") -> dict[str, Any]:
        return {
            "version": self.PLATFORM_VERSION,
            "has_project": False,
            "mode": "conversation",
            "visitor_id": visitor_id,
            "project": None,
            "vector_hint": (
                "Расскажите идею или вопрос — Vector ответит как сотрудник. "
                "Проект появится, когда понадобится хранить результаты."
            ),
        }

    def _public_payload(self, record: ProjectRecord, *, locale: str = "ru") -> dict[str, Any]:
        project = record.to_dict()
        project["identity"] = build_identity(record)
        project["progress"] = build_progress(record)
        project["artifact_folders"] = build_artifact_folders(record)
        project["health"] = build_project_health(record)
        project["next_action"] = build_next_action(record)
        project["activity"] = build_last_activity(record)
        journey = build_project_journey_state(record)
        if journey:
            project["journey"] = journey
        return {
            "version": self.PLATFORM_VERSION,
            "has_project": record.mode == "project" or bool(record.versions),
            "mode": record.mode,
            "visitor_id": record.visitor_id,
            "project": project,
            "vector_hint": record.next_step_hint,
            "deliverable_intent": None,
        }


def _apply_goal_context(record: ProjectRecord, goal: str) -> None:
    g = (goal or "").strip()
    if not g:
        return
    if not record.description.strip():
        record.description = g[:180] + ("…" if len(g) > 180 else "")
    market = infer_market(g)
    if market != "Не указан":
        record.market = market
    title = _title_from_goal(g)
    if title and title != "Мой проект" and record.title in (
        "Мой проект",
        "Site project",
        "Document analysis",
        "Test",
    ):
        record.title = title
    try:
        from app.factory.motion_brief import (
            apply_text_to_project_brief,
            empty_vector_brief,
        )

        base = record.brief or empty_vector_brief(market=record.market or "DE")
        if record.market:
            base["market"] = record.market
        record.brief = apply_text_to_project_brief(base, g)
    except Exception:
        pass


def _section_for_service(service_id: str | None) -> str:
    if service_id == SERVICE_WEBSITE:
        return SECTION_WEBSITE
    if service_id == SERVICE_DOCUMENT_ANALYSIS:
        return SECTION_DOCUMENTS
    return SECTION_FILES


def _service_for_capability(capability_id: str) -> str:
    if capability_id == "generate_site":
        return SERVICE_WEBSITE
    if capability_id == "analyze_business_document":
        return SERVICE_DOCUMENT_ANALYSIS
    return SERVICE_WEBSITE


def _title_from_goal(goal: str) -> str:
    g = (goal or "").strip()
    if len(g) > 60:
        return g[:57] + "…"
    return g or "Мой проект"


def _version_summary(capability_id: str, outputs: dict[str, Any]) -> str:
    if capability_id == "generate_site":
        return "Сгенерирована версия сайта"
    if capability_id == "analyze_business_document":
        title = outputs.get("title") or "Документ"
        return f"Анализ: {title}"
    path = outputs.get("path") or ""
    return f"Создан файл: {path}" if path else "Новая версия результата"


def _artifacts_from_capability(
    capability_id: str,
    outputs: dict[str, Any],
    *,
    workspace_id: str,
    visitor_id: str,
    version: int,
) -> list[ProjectArtifact]:
    arts: list[ProjectArtifact] = []
    section = _section_for_service(_service_for_capability(capability_id))

    if capability_id == "generate_site":
        preview = _preview_href(workspace_id, visitor_id)
        arts.append(
            ProjectArtifact(
                id=f"art-{uuid.uuid4().hex[:8]}",
                kind="preview",
                label="Preview",
                href=preview,
                section=SECTION_WEBSITE,
                version=version,
            )
        )
        for rel in outputs.get("files") or []:
            if str(rel).endswith(".html"):
                arts.append(
                    ProjectArtifact(
                        id=f"art-{uuid.uuid4().hex[:8]}",
                        kind="source",
                        label="Source (HTML)",
                        href=_file_href(workspace_id, visitor_id, str(rel)),
                        section=SECTION_WEBSITE,
                        version=version,
                    )
                )
        arts.append(
            ProjectArtifact(
                id=f"art-{uuid.uuid4().hex[:8]}",
                kind="instructions",
                label="Инструкции",
                href=None,
                section=SECTION_WEBSITE,
                version=version,
            )
        )
        return arts

    if capability_id == "analyze_business_document":
        for rel, label, kind in (
            ("executive_summary.md", "Краткое резюме", "report"),
            ("report.html", "Отчёт", "preview"),
            ("report.md", "Полный отчёт", "pdf"),
        ):
            arts.append(
                ProjectArtifact(
                    id=f"art-{uuid.uuid4().hex[:8]}",
                    kind=kind,  # type: ignore[arg-type]
                    label=label,
                    href=_file_href(workspace_id, visitor_id, rel),
                    section=SECTION_DOCUMENTS,
                    version=version,
                )
            )
        return arts

    path = str(outputs.get("path") or "")
    if path:
        arts.append(
            ProjectArtifact(
                id=f"art-{uuid.uuid4().hex[:8]}",
                kind="file",
                label=path,
                href=_file_href(workspace_id, visitor_id, path),
                section=SECTION_FILES,
                version=version,
            )
        )
    return arts


def _classify_file(rel: str) -> tuple[str, str]:
    lower = rel.lower()
    if lower.endswith(".html"):
        return "preview", SECTION_WEBSITE
    if lower.endswith(".pdf"):
        return "pdf", SECTION_DOCUMENTS
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image", SECTION_FILES
    if "report" in lower or "summary" in lower:
        return "report", SECTION_DOCUMENTS
    return "file", SECTION_FILES


def evaluate_message_intent(text: str) -> dict[str, Any] | None:
    return detect_deliverable_intent(text)
