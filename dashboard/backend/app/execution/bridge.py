"""Wire Execution Layer to public chat — one capability at a time (top-down)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote

from app.execution.capabilities import ExecutionCapabilityRegistry
from app.execution.executors.analyze_business_document import AnalyzeBusinessDocumentExecutor
from app.execution.executors.filesystem import FilesystemReadExecutor, FilesystemWriteExecutor
from app.execution.executors.generate_site import GenerateSiteExecutor
from app.execution.log_store import ExecutionLogStore
from app.execution.manager import ExecutionManager
from app.execution.models import ExecutionPlan, ExecutionStep, PermissionGrant, VerificationRule
from app.execution.workspace import ExecutionWorkspaceStore
from app.execution.workspace_reuse import format_reuse_explanation

_REGISTRY: ExecutionCapabilityRegistry | None = None

_README_GOAL = re.compile(
    r"(?:создай|создать|напиши|create|write)\s+(?:файл\s+)?readme\b",
    re.IGNORECASE,
)
_FILE_GOAL = re.compile(
    r"(?:создай|создать|напиши|create|write)\s+(?:файл\s+)?(?P<name>[\w.\-]+\.[a-zA-Z0-9]+)",
    re.IGNORECASE,
)
_SITE_GOAL = re.compile(
    r"(?:создай|создать|сделай|make|create|build)\s+(?:мне\s+)?(?:сайт|site|landing|лендинг)\b",
    re.IGNORECASE,
)
_CONTENT_AFTER = re.compile(r"(?:с\s+текстом|с\s+содержимым|content|:)\s*(.+)$", re.IGNORECASE | re.DOTALL)

_SITE_PROGRESS = (
    "Анализирую запрос",
    "Создаю Workspace",
    "Формирую структуру проекта",
    "Создаю brief",
    "Генерирую HTML",
    "Генерирую CSS",
    "Создаю preview",
    "Готово",
)

_DOC_PROGRESS = (
    "Принимаю документ",
    "Извлекаю текст",
    "Определяю тип документа",
    "Структурный анализ",
    "SWOT и риски",
    "Формирую отчёты",
    "Готово",
)

_ANALYZE_GOAL = re.compile(
    r"(?:проанализируй|проанализировать|анализ|analyze|разбери|оцени)\b",
    re.IGNORECASE,
)
_DOC_HINT = re.compile(
    r"(?:бизнес-план|бизнес план|business\s+plan|документ|отчёт|отчет|предложен|pdf)",
    re.IGNORECASE,
)


def get_execution_registry(memory_dir: Path) -> ExecutionCapabilityRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        reg = ExecutionCapabilityRegistry()
        ws = ExecutionWorkspaceStore(memory_dir)
        reg.register_executor("filesystem_write", FilesystemWriteExecutor(ws))
        reg.register_executor("filesystem_read", FilesystemReadExecutor(ws))
        reg.register_executor("generate_site", GenerateSiteExecutor(ws))
        reg.register_executor(
            "analyze_business_document",
            AnalyzeBusinessDocumentExecutor(ws, memory_dir),
        )
        _REGISTRY = reg
    return _REGISTRY


def _visitor_map_path(memory_dir: Path) -> Path:
    return memory_dir / "execution" / "visitor_workspaces.json"


def _workspace_for_visitor(memory_dir: Path, visitor_id: str, *, title: str = "Vector Workspace") -> str:
    path = _visitor_map_path(memory_dir)
    mapping: dict[str, str] = {}
    if path.is_file():
        try:
            mapping = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            mapping = {}
    if visitor_id in mapping and ExecutionWorkspaceStore(memory_dir).get(mapping[visitor_id]):
        return mapping[visitor_id]
    ws = ExecutionWorkspaceStore(memory_dir).create(
        owner_id=visitor_id[:64] or "anonymous",
        title=title,
    )
    mapping[visitor_id] = ws.workspace_id
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2), encoding="utf-8")
    return ws.workspace_id


def _parse_file_request(goal: str) -> tuple[str, str] | None:
    g = goal.strip()
    if _README_GOAL.search(g):
        content = _default_readme(g)
        m = _CONTENT_AFTER.search(g)
        if m:
            content = m.group(1).strip()
        return "README.md", content
    m = _FILE_GOAL.search(g)
    if m:
        name = m.group("name")
        content = ""
        cm = _CONTENT_AFTER.search(g)
        if cm:
            content = cm.group(1).strip()
        return name, content
    return None


def _workspace_file_href(workspace_id: str, visitor_id: str, rel: str) -> str:
    q = quote(visitor_id, safe="")
    path = rel.lstrip("/")
    return f"/api/public/execution/workspace/{workspace_id}/files/{path}?visitor_id={q}"


def _is_analyzable_attachment(file_row: dict[str, Any]) -> bool:
    ct = str(file_row.get("content_type") or "").lower()
    fn = str(file_row.get("filename") or "").lower()
    if "pdf" in ct or fn.endswith(".pdf"):
        return True
    if fn.endswith(".txt") or fn.endswith(".md"):
        return True
    if "text/plain" in ct or "markdown" in ct:
        return True
    return False


def _parse_document_request(goal: str, attachment_files: list[dict[str, Any]]) -> dict[str, Any] | None:
    docs = [f for f in attachment_files if _is_analyzable_attachment(f)]
    g = goal.strip()
    lower = g.lower()
    wants_analyze = bool(_ANALYZE_GOAL.search(g)) or bool(_DOC_HINT.search(g))
    if docs and (wants_analyze or not g.strip()):
        return {"attachment_id": str(docs[0].get("id") or ""), "goal": g or "Анализ документа"}
    if wants_analyze and not docs:
        return {"attachment_id": "", "goal": g, "missing_pdf": True}
    return None


def _parse_site_request(goal: str) -> str | None:
    g = goal.strip()
    if _SITE_GOAL.search(g):
        return g
    lower = g.lower()
    if any(w in lower for w in ("сайт", "site", "landing", "лендинг")) and any(
        w in lower for w in ("создай", "создать", "сделай", "хочу", "нужен", "need", "create", "build")
    ):
        return g
    return None


def _default_readme(goal: str) -> str:
    return f"""# README

Создано Vector (Virtus Core).

## Запрос
{goal.strip()}

## Дальше
- Добавьте описание проекта
- Уточните структуру сайта или продукта в чате
"""


def _progress_answer(lines: tuple[str, ...]) -> str:
    return "\n".join(f"✓ {line}..." if line != "Готово" else f"✓ {line}." for line in lines)


def _preview_href(workspace_id: str, visitor_id: str) -> str:
    q = quote(visitor_id, safe="")
    return f"/api/public/execution/preview/{workspace_id}?visitor_id={q}"


def try_user_execution(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    attachment_files: list[dict[str, Any]] | None = None,
) -> dict[str, Any] | None:
    """
    Run a single real capability when the user goal matches.
    Returns public chat dict or None (fall through to Brain).
    """
    files = attachment_files or []

    doc_req = _parse_document_request(goal, files)
    if doc_req:
        return _run_analyze_document(doc_req, visitor_id=visitor_id, memory_dir=memory_dir)

    site_goal = _parse_site_request(goal)
    if site_goal:
        return _run_generate_site(site_goal, visitor_id=visitor_id, memory_dir=memory_dir)

    parsed = _parse_file_request(goal)
    if not parsed:
        return None

    filename, content = parsed
    workspace_id = _workspace_for_visitor(memory_dir, visitor_id)
    registry = get_execution_registry(memory_dir)
    ws_store = ExecutionWorkspaceStore(memory_dir)
    logs = ExecutionLogStore(memory_dir)
    mgr = ExecutionManager(registry=registry, workspace_store=ws_store, log_store=logs)

    plan = ExecutionPlan(
        plan_id="",
        goal=goal.strip(),
        workspace_id=workspace_id,
        steps=(
            ExecutionStep(
                id="step-write",
                capability_id="filesystem_write",
                title=f"Write {filename}",
                inputs={"path": filename, "content": content, "workspace_id": workspace_id},
                verification=VerificationRule(
                    id="vr-write",
                    description="file written",
                    required_output_keys=("path", "bytes"),
                ),
            ),
        ),
        required_permissions=frozenset({"write", "filesystem"}),
    )

    grant = PermissionGrant(
        kinds=frozenset({"read", "write", "filesystem"}),
        workspace_id=workspace_id,
        actor=visitor_id,
    )
    result = mgr.run(plan, grant)
    if result.status != "completed":
        err = result.error or (result.steps[0].error if result.steps else "execution failed")
        return {
            "answer": f"Не удалось создать файл: {err}",
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "context": {"execution": result.to_dict()},
        }

    step = result.steps[0]
    rel = step.outputs.get("path", filename)
    nbytes = step.outputs.get("bytes", 0)
    answer = (
        "✓ Создаю файл в Workspace...\n"
        "✓ Готово.\n\n"
        f"**{rel}** создан ({nbytes} байт).\n\n"
        f"Путь в workspace: `files/{rel}`"
    )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": None,
        "cta_label": None,
        "context": {
            "execution": result.to_dict(),
            "workspace_id": workspace_id,
            "artifact_path": f"files/{rel}",
        },
    }


def _run_analyze_document(
    doc_req: dict[str, Any],
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any]:
    if doc_req.get("missing_pdf"):
        return {
            "answer": (
                "Чтобы проанализировать бизнес-документ, прикрепите PDF к сообщению "
                "и напишите, например: «Проанализируй мой бизнес-план»."
            ),
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "cta_actions": None,
        }

    workspace_id = _workspace_for_visitor(memory_dir, visitor_id, title="Document analysis")
    registry = get_execution_registry(memory_dir)
    ws_store = ExecutionWorkspaceStore(memory_dir)
    logs = ExecutionLogStore(memory_dir)
    mgr = ExecutionManager(registry=registry, workspace_store=ws_store, log_store=logs)

    goal = str(doc_req.get("goal") or "").strip()
    attachment_id = str(doc_req.get("attachment_id") or "").strip()

    plan = ExecutionPlan(
        plan_id="",
        goal=goal or "Анализ бизнес-документа",
        workspace_id=workspace_id,
        steps=(
            ExecutionStep(
                id="step-analyze-doc",
                capability_id="analyze_business_document",
                title="Analyze business document",
                inputs={
                    "goal": goal,
                    "attachment_id": attachment_id,
                    "workspace_id": workspace_id,
                },
                verification=VerificationRule(
                    id="vr-doc",
                    description="Document analysis artifacts produced",
                    required_output_keys=("artifact_id", "files", "document_type"),
                ),
            ),
        ),
        required_permissions=frozenset({"read", "write", "filesystem"}),
    )
    grant = PermissionGrant(
        kinds=frozenset({"read", "write", "filesystem"}),
        workspace_id=workspace_id,
        actor=visitor_id,
    )
    result = mgr.run(plan, grant)
    if result.status != "completed":
        err = result.error or (result.steps[0].error if result.steps else "execution failed")
        return {
            "answer": f"Не удалось проанализировать документ: {err}",
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "cta_actions": None,
            "context": {"execution": result.to_dict()},
        }

    cap = result.steps[0].outputs
    doc_type = cap.get("document_type") or "business_document"
    title = cap.get("title") or "Документ"
    report_href = _workspace_file_href(workspace_id, visitor_id, "report.md")
    summary_href = _workspace_file_href(workspace_id, visitor_id, "executive_summary.md")
    file_list = "\n".join(f"- `{f}`" for f in (cap.get("files") or []) if f)

    answer = (
        f"{_progress_answer(_DOC_PROGRESS)}\n\n"
        f"**Анализ завершён.** Тип: `{doc_type}`. **{title}**\n\n"
        f"{file_list}\n\n"
        "Краткий итог в чате — детали в отчётах. Откройте файлы кнопками ниже."
    )
    cta_actions = [
        {"href": report_href, "label": "Открыть отчёт"},
        {"href": summary_href, "label": "Открыть Executive Summary"},
    ]
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": report_href,
        "cta_label": "Открыть отчёт",
        "cta_actions": cta_actions,
        "context": {
            "execution": result.to_dict(),
            "capability_result": cap,
            "workspace_id": workspace_id,
            "document_type": doc_type,
        },
    }


def _run_generate_site(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any]:
    workspace_id = _workspace_for_visitor(memory_dir, visitor_id, title="Site project")
    registry = get_execution_registry(memory_dir)
    ws_store = ExecutionWorkspaceStore(memory_dir)
    logs = ExecutionLogStore(memory_dir)
    mgr = ExecutionManager(registry=registry, workspace_store=ws_store, log_store=logs)

    plan = ExecutionPlan(
        plan_id="",
        goal=goal.strip(),
        workspace_id=workspace_id,
        steps=(
            ExecutionStep(
                id="step-generate-site",
                capability_id="generate_site",
                title="Generate site from brief",
                inputs={"brief": goal.strip(), "workspace_id": workspace_id},
                verification=VerificationRule(
                    id="vr-site",
                    description="Site artifact produced",
                    required_output_keys=("artifact_id", "preview_url", "files"),
                ),
            ),
        ),
        required_permissions=frozenset({"write", "filesystem", "network"}),
    )
    grant = PermissionGrant(
        kinds=frozenset({"read", "write", "filesystem", "network", "deployment"}),
        workspace_id=workspace_id,
        actor=visitor_id,
    )
    result = mgr.run(plan, grant)
    if result.status != "completed":
        err = result.error or (result.steps[0].error if result.steps else "execution failed")
        return {
            "answer": f"Не удалось создать сайт: {err}",
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": None,
            "cta_label": None,
            "context": {"execution": result.to_dict()},
        }

    cap = result.steps[0].outputs
    files = cap.get("files") or []
    preview_path = _preview_href(workspace_id, visitor_id)
    file_list = "\n".join(f"- `{f}`" for f in files if f)
    reuse_score = int(cap.get("reuse_score") or 0)
    reuse_note = ""
    if reuse_score > 0:
        reuse_note = f"\n\n{format_reuse_explanation(cap)}\n"
    answer = (
        f"{_progress_answer(_SITE_PROGRESS)}\n\n"
        "**Проект готов.**\n\n"
        f"{file_list}"
        f"{reuse_note}\n\n"
        "Откройте preview — это реальный сайт, не описание в чате."
    )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": preview_path,
        "cta_label": "Открыть preview",
        "context": {
            "execution": result.to_dict(),
            "capability_result": cap,
            "workspace_id": workspace_id,
            "preview_url": preview_path,
        },
    }


def list_user_capabilities(memory_dir: Path) -> list[dict[str, str]]:
    """Product KPI — what Vector can actually do today."""
    reg = get_execution_registry(memory_dir)
    ready = [c for c in reg.list_capabilities() if reg.is_executable(c.id)]
    labels = {
        "filesystem_write": "создавать документ по запросу (файл + содержимое + путь)",
        "filesystem_read": "читать документ из Workspace",
        "generate_site": "создавать сайт по запросу (reuse document_structure при наличии)",
        "analyze_business_document": "анализировать бизнес-документы (PDF → отчёты + SWOT)",
    }
    return [{"id": c.id, "label": labels.get(c.id, c.name)} for c in ready]
