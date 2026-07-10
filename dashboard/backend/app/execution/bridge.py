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
from app.execution.post_analysis_actions import (
    build_analysis_completion_message,
    suggest_post_analysis_actions,
)
from app.execution.workspace_reuse import format_reuse_explanation, load_workspace_building_blocks
from app.integration.genesis_brain.user_text_normalizer import normalize_user_text
from app.integration.market_context import (
    MARKET_DEFAULT,
    market_clarification_question,
    resolve_market_context,
)
from app.integration.product_line import website_concept_ready_message, website_studio_intro

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
    "Изучаю задачу",
    "Готовлю структуру",
    "Создаю первый вариант сайта",
    "Настраиваю мобильную версию",
    "Проверяю отображение",
    "Сайт готов к просмотру",
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
    r"(?:"
    r"проанализируй|проанализировать|анализ|analyze|разбери|оцени|"
    r"проверь|проверить|проверка|review|check"
    r")\b",
    re.IGNORECASE,
)
_DOC_HINT = re.compile(
    r"(?:бизнес-план|бизнес план|business\s+plan|документ|отчёт|отчет|предложен|pdf)",
    re.IGNORECASE,
)

_CAPABILITY_QUESTION = re.compile(
    r"(?:"
    r"что\s+ты\s+умеешь|что\s+можешь|какие\s+(?:у\s+тебя\s+)?возможност|"
    r"что\s+ты\s+можешь\s+сделать|расскажи\s+о\s+возможност|"
    r"what\s+can\s+you\s+do|what\s+do\s+you\s+do|your\s+capabilit"
    r")",
    re.IGNORECASE,
)
_CAN_YOU = re.compile(
    r"(?:"
    r"ты\s+умеешь|умеешь\s+ли\s+ты|ты\s+можешь|можешь\s+ли\s+ты|"
    r"can\s+you|do\s+you\s+(?:know\s+how|make|create|build)"
    r")",
    re.IGNORECASE,
)
_SITE_TOPIC = re.compile(r"(?:сайт|site|landing|лендинг|веб-страниц|web\s*site)", re.IGNORECASE)
_DOC_TOPIC = re.compile(
    r"(?:pdf|документ|бизнес-план|бизнес\s+план|business\s+plan|отчёт|отчет|анализ)",
    re.IGNORECASE,
)
_FILE_TOPIC = re.compile(r"(?:документ|файл|readme|markdown|\.md\b|\.txt\b)", re.IGNORECASE)

_BUSINESS_CONTEXT = re.compile(
    r"(?:"
    r"стоматолог|dental|зуб|клиник|имплант|"
    r"кафе|cafe|кофе|ресторан|restaurant|бар|"
    r"салон|красот|beauty|spa|маникюр|"
    r"автосервис|авто|garage|шиномонтаж|"
    r"бизнес|компани|фирм|услуг|магазин|shop|"
    r"юрист|law|fitness|спорт|школ|agency|агентств|"
    r"отель|hotel|стоматологи|стоматология"
    r")",
    re.IGNORECASE,
)

_VAGUE_SITE_GOAL = re.compile(
    r"^(?:"
    r"(?:я\s+)?хочу\s+(?:создать\s+)?(?:сайт|лендинг|landing|site)"
    r"|(?:создай|создать|сделай|make|create|build)\s+(?:мне\s+)?(?:сайт|лендинг|landing|site)\s*"
    r"|(?:нужен|need)\s+(?:сайт|лендинг|landing|site)\s*"
    r")\.?$",
    re.IGNORECASE,
)

_CAPABILITY_EXAMPLES: dict[str, list[str]] = {
    "filesystem_write": ["Создай README", "Создай файл notes.txt"],
    "generate_site": [
        "Создай сайт стоматологии",
        "Создай лендинг кофейни",
        "Создай сайт автосервиса",
    ],
    "analyze_business_document": ["Проанализируй бизнес-план (прикрепите PDF)"],
    "filesystem_read": ["Прочитай README.md из workspace"],
}


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
    wants_analyze = bool(_ANALYZE_GOAL.search(g)) or bool(_DOC_HINT.search(g))

    if docs:
        # Site / file goals win — checked earlier in try_user_execution
        return {"attachment_id": str(docs[0].get("id") or ""), "goal": g or "Анализ документа"}

    if wants_analyze and not docs:
        return {"attachment_id": "", "goal": g, "missing_pdf": True}
    return None


def should_route_attachments_to_execution(
    goal: str, attachment_files: list[dict[str, Any]]
) -> bool:
    """Block Brain essay mode when user attached analyzable business documents."""
    docs = [f for f in attachment_files if _is_analyzable_attachment(f)]
    if not docs:
        return False
    g = goal.strip()
    if _parse_site_request(g) or _parse_file_request(g):
        return False
    return True


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


def _existing_workspace_id(memory_dir: Path, visitor_id: str) -> str | None:
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


def _workspace_has_business_context(memory_dir: Path, workspace_id: str) -> bool:
    blocks = load_workspace_building_blocks(
        ExecutionWorkspaceStore(memory_dir),
        workspace_id,
    )
    return bool(blocks.get("document_structure") or blocks.get("executive_summary") or blocks.get("report_md"))


def _site_brief_insufficient(goal: str) -> bool:
    g = goal.strip()
    if not g:
        return True
    if _BUSINESS_CONTEXT.search(g):
        return False
    if re.search(r"сайт\s+для\s+\w+", g, re.IGNORECASE):
        return False
    if re.search(r"(?:for|für)\s+\w+", g, re.IGNORECASE) and _SITE_TOPIC.search(g):
        return False
    if len(g) > 72:
        return False
    if _VAGUE_SITE_GOAL.match(g):
        return True
    if _SITE_GOAL.search(g) and len(g.split()) <= 7:
        return True
    return False


def _site_brief_clarification(
    *,
    from_project: bool = False,
    goal: str = "",
    ui_locale: str | None = None,
) -> dict[str, Any]:
    if from_project:
        intro = (
            "Использую информацию из вашего проекта.\n"
            "Начинаю подготовку сайта."
        )
    else:
        intro = website_studio_intro()
    answer = intro
    if not from_project:
        ctx = resolve_market_context(text=goal, ui_locale=ui_locale)
        market_q = market_clarification_question(ctx, locale=ui_locale)
        if market_q:
            answer = f"{intro}\n\n{market_q}"
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": None,
        "cta_label": None,
    }


def _site_customer_ctas(preview_path: str) -> list[dict[str, Any]]:
    return [
        {"href": preview_path, "label": "🌐 Открыть сайт", "group": "artifacts", "available": True},
        {
            "href": "#action:Хочу внести правки в сайт",
            "label": "✏ Продолжить редактирование",
            "group": "next",
            "available": True,
        },
        {
            "href": "#horizon:download",
            "label": "📥 Скачать",
            "group": "next",
            "available": False,
        },
    ]


def _build_site_completion_answer(preview_path: str, reuse_note: str) -> str:
    body = (
        f"{_progress_answer(_SITE_PROGRESS)}\n\n"
        f"{website_concept_ready_message()}\n\n"
        "**Что уже готово:**\n"
        "✓ структура сайта\n"
        "✓ дизайн\n"
        "✓ мобильная версия\n"
        "✓ предварительный просмотр"
    )
    if reuse_note:
        body += f"\n\n{reuse_note.strip()}"
    return body


def _default_readme(goal: str) -> str:
    return f"""# README

Создано Vector (Virtus Core).

## Запрос
{goal.strip()}

## Дальше
- Добавьте описание проекта
- Уточните структуру сайта или продукта в диалоге с Vector
"""


def _progress_answer(lines: tuple[str, ...]) -> str:
    return "\n".join(f"✓ {line}..." if line != "Готово" else f"✓ {line}." for line in lines)


def _preview_href(workspace_id: str, visitor_id: str) -> str:
    q = quote(visitor_id, safe="")
    return f"/api/public/execution/preview/{workspace_id}?visitor_id={q}"


def _format_capability_discovery_answer(
    *,
    intro: str,
    capability_ids: list[str],
    closing: str = "",
) -> str:
    lines = [intro.rstrip(), ""]
    for cap_id in capability_ids:
        examples = _CAPABILITY_EXAMPLES.get(cap_id, [])
        if not examples:
            continue
        lines.append("Например:")
        lines.extend(f"• {ex}" for ex in examples)
        lines.append("")
    if closing:
        lines.append(closing.rstrip())
    return "\n".join(lines).strip()


def try_capability_discovery(goal: str, memory_dir: Path) -> dict[str, Any] | None:
    """Answer «что умеешь?» from Capability Registry — not Brain generic knowledge."""
    g = goal.strip()
    if not g or len(g) > 280:
        return None

    caps = list_user_capabilities(memory_dir)
    ready_ids = [c["id"] for c in caps]
    if not ready_ids:
        return None

    is_question = bool(_CAPABILITY_QUESTION.search(g) or _CAN_YOU.search(g))
    if not is_question:
        return None

    if _SITE_TOPIC.search(g):
        if "generate_site" not in ready_ids:
            return None
        answer = _format_capability_discovery_answer(
            intro="Да.\nЯ умею создавать сайты для бизнеса.",
            capability_ids=["generate_site"],
            closing="Опишите компанию двумя словами — подготовлю первый вариант сайта.",
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "capability_registry",
            "cta_href": None,
            "cta_label": None,
        }

    if _DOC_TOPIC.search(g):
        if "analyze_business_document" not in ready_ids:
            return None
        answer = _format_capability_discovery_answer(
            intro="Да.\nЯ умею анализировать бизнес-документы.",
            capability_ids=["analyze_business_document"],
            closing="Прикрепите PDF и напишите «Проанализируй» — получите отчёт и executive summary.",
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "capability_registry",
            "cta_href": None,
            "cta_label": None,
        }

    if _FILE_TOPIC.search(g) and "filesystem_write" in ready_ids:
        answer = _format_capability_discovery_answer(
            intro="Да.\nЯ умею готовить документы по запросу.",
            capability_ids=["filesystem_write"],
            closing="Напишите, что нужно — подготовлю файл в вашем проекте.",
        )
        return {
            "answer": answer,
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "capability_registry",
            "cta_href": None,
            "cta_label": None,
        }

    bullets: list[str] = []
    labels = {c["id"]: c["label"] for c in caps}
    order = ("filesystem_write", "generate_site", "analyze_business_document", "filesystem_read")
    for cap_id in order:
        if cap_id not in ready_ids:
            continue
        label = labels.get(cap_id, cap_id)
        examples = _CAPABILITY_EXAMPLES.get(cap_id, [])
        hint = f" — «{examples[0]}»" if examples else ""
        bullets.append(f"• {label}{hint}")

    answer = "Я умею:\n" + "\n".join(bullets)
    answer += "\n\nНапишите, что нужно сделать — выполню работу в вашем проекте."
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "capability_registry",
        "cta_href": None,
        "cta_label": None,
    }


def try_user_execution(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    attachment_files: list[dict[str, Any]] | None = None,
    ui_locale: str | None = None,
) -> dict[str, Any] | None:
    """
    Run a single real capability when the user goal matches.
    Returns public chat dict or None (fall through to Brain).
    """
    goal = normalize_user_text(goal) or goal
    discovered = try_capability_discovery(goal, memory_dir)
    if discovered:
        return discovered

    files = attachment_files or []

    site_goal = _parse_site_request(goal)
    if site_goal:
        if _site_brief_insufficient(site_goal):
            ws_id = _existing_workspace_id(memory_dir, visitor_id)
            if ws_id and _workspace_has_business_context(memory_dir, ws_id):
                pass  # enough context from project — proceed
            else:
                return _site_brief_clarification(goal=site_goal, ui_locale=ui_locale)
        return _run_generate_site(site_goal, visitor_id=visitor_id, memory_dir=memory_dir)

    parsed = _parse_file_request(goal)
    if parsed:
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
                    id="step-write-file",
                    capability_id="filesystem_write",
                    title=f"Write {filename}",
                    inputs={
                        "path": filename,
                        "content": content,
                        "workspace_id": workspace_id,
                    },
                    verification=VerificationRule(
                        id="vr-file",
                        description="File written",
                        required_output_keys=("path", "bytes"),
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
                "answer": f"Не удалось создать файл: {err}",
                "source": "genesis-ai",
                "mode": "genesis",
                "provider": "execution",
                "cta_href": None,
                "cta_label": None,
            }
        cap = result.steps[0].outputs
        file_href = _workspace_file_href(workspace_id, visitor_id, cap.get("path") or filename)
        return {
            "answer": (
                f"✓ Документ создан: **{cap.get('path') or filename}**\n\n"
                "Файл добавлен в ваш проект."
            ),
            "source": "genesis-ai",
            "mode": "genesis",
            "provider": "execution",
            "cta_href": file_href,
            "cta_label": "Открыть файл",
            "context": {
                "execution": result.to_dict(),
                "capability_result": cap,
                "workspace_id": workspace_id,
            },
        }

    doc_req = _parse_document_request(goal, files)
    if doc_req:
        return _run_analyze_document(
            doc_req,
            visitor_id=visitor_id,
            memory_dir=memory_dir,
            ui_locale=ui_locale,
        )

    return None


def _run_analyze_document(
    doc_req: dict[str, Any],
    *,
    visitor_id: str,
    memory_dir: Path,
    ui_locale: str | None = None,
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
    source_name = cap.get("source_filename") or title
    pages = cap.get("pages_analyzed") or cap.get("pages_included")
    readiness = cap.get("readiness_score")
    report_locale = str(cap.get("report_locale") or ui_locale or "ru")[:2]
    if report_locale not in ("ru", "en", "de"):
        report_locale = "ru"
    issues_count = int(cap.get("issues_count") or 0)
    priority_count = int(cap.get("priority_count") or 0)

    summary_href = _workspace_file_href(workspace_id, visitor_id, "executive_summary.md")
    conclusion_href = _workspace_file_href(workspace_id, visitor_id, "report.html")

    answer = build_analysis_completion_message(
        locale=report_locale,
        doc_type=doc_type,
        source_name=source_name,
        readiness=readiness if isinstance(readiness, int) else None,
        issues_count=issues_count,
        priority_count=priority_count,
    )

    registry_ref = get_execution_registry(memory_dir)
    cta_actions = suggest_post_analysis_actions(
        doc_type=doc_type,
        locale=report_locale,
        summary_href=summary_href,
        conclusion_href=conclusion_href,
        site_available=registry_ref.is_executable("generate_site"),
    )
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": summary_href,
        "cta_label": "📊 Executive Summary",
        "cta_actions": cta_actions,
        "context": {
            "execution": result.to_dict(),
            "capability_result": cap,
            "workspace_id": workspace_id,
            "document_type": doc_type,
            "execution_kind": "document_analysis",
            "source_filename": source_name,
            "pages_analyzed": pages,
            "readiness_score": readiness,
            "issues_count": issues_count,
            "report_locale": report_locale,
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
    preview_path = _preview_href(workspace_id, visitor_id)
    reuse_score = int(cap.get("reuse_score") or 0)
    reuse_note = format_reuse_explanation(cap) if reuse_score > 0 else ""
    answer = _build_site_completion_answer(preview_path, reuse_note)
    cta_actions = _site_customer_ctas(preview_path)
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": preview_path,
        "cta_label": "🌐 Открыть сайт",
        "cta_actions": cta_actions,
        "context": {
            "execution": result.to_dict(),
            "capability_result": cap,
            "workspace_id": workspace_id,
            "preview_url": preview_path,
            "artifact_type": "website",
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
