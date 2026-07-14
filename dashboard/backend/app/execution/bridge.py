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
from app.integration.delivery_engine.gate import delivery_engine_enabled, finalize_execution_response
from app.integration.product_line import (
    LIFECYCLE_APPROVAL,
    LIFECYCLE_CHOICE,
    SERVICE_WEBSITE,
    project_execution_ack_intro,
    universal_first_version_scenario,
    website_concept_ready_message,
)

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
    "Создаю первый вариант",
    "Настраиваю мобильную версию",
    "Проверяю отображение",
    "Первая версия в проекте",
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

_GENERIC_COMPANY_REF = re.compile(
    r"(?:"
    r"(?:для\s+)?(?:моей|своей|нашей)\s+(?:компани|бизнес|фирм)"
    r"|(?:моя|мой|моё|наша|наш|наше)\s+(?:компани|бизнес|фирм)"
    r"|для\s+(?:моего|своего|нашего)\s+бизнеса"
    r"|for\s+(?:my|our)\s+(?:company|business)"
    r")",
    re.IGNORECASE,
)

_SITE_FOR_GENERIC = frozenset(
    {
        "своей",
        "моей",
        "нашей",
        "компании",
        "компания",
        "бизнеса",
        "бизнес",
        "фирмы",
        "фирма",
        "my",
        "our",
        "company",
        "business",
    }
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


_SITE_REVISION = re.compile(
    r"(?:"
    r"правк|измени|изменить|убери|убрать|исправ|поправ|переделай|обнови|"
    r"добавь|добавить|вставь|вставить|замени|поменя|сократи|"
    r"сделай|давай\s+поменя|"
    r"шапк|отзыв|современн|"
    r"логотип.*(?:слева|справа)|(?:слева|справа).*логотип|"
    r"пусть\s+будет"
    r")",
    re.IGNORECASE,
)


_SITE_SOFT_SATISFACTION = re.compile(
    r"(?:теперь\s+)?(?:мне\s+)?нравится",
    re.IGNORECASE,
)

_SITE_EXPLICIT_APPROVAL = re.compile(
    r"(?:"
    r"всё\s+устраивает|все\s+устраивает|"
    r"да,?\s*(?:всё|все)(?:\s+устраивает)?|"
    r"именно\s+такой|"
    r"согласован|оформляем"
    r")",
    re.IGNORECASE,
)


_SITE_PURCHASE = re.compile(
    r"(?:заказать|оформить\s+заказ|сколько\s+стоит|купить\s+этот|хочу\s+купить|готов\s+заказать|хочу\s+заказать)",
    re.IGNORECASE,
)


def _is_site_revision_request(goal: str) -> bool:
    g = (goal or "").strip()
    if not g:
        return False
    if _SITE_REVISION.search(g):
        return True
    lower = g.lower()
    return "правк" in lower and "сайт" in lower


def _parse_site_request(goal: str) -> str | None:
    g = goal.strip()
    if _is_site_revision_request(g):
        return None
    lower = g.lower()
    if _SITE_PURCHASE.search(g):
        return None
    if _SITE_GOAL.search(g):
        return g
    lower = g.lower()
    if any(w in lower for w in ("сайт", "site", "landing", "лендинг")) and any(
        w in lower for w in ("создай", "создать", "сделай", "хочу", "нужен", "need", "create", "build")
    ):
        return g
    return None


def _project_business_brief(memory_dir: Path, visitor_id: str) -> str:
    """Stable business brief from project — not raw edit/chat instructions."""
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return ""
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(ws_id)
    except Exception:
        return ""
    if not record:
        return ""
    from app.factory.analyzer import business_brief_for_site

    chunks: list[str] = []
    if record.description.strip():
        chunks.append(record.description.strip())
    for event in reversed(record.timeline or []):
        detail = (event.detail or "").strip()
        if detail and _has_specific_business_facts(detail):
            chunks.append(detail)
            break
    raw = "\n".join(chunks).strip()
    return business_brief_for_site(raw)


def _project_lifecycle_phase(memory_dir: Path, visitor_id: str) -> str | None:
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return None
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(ws_id)
    except Exception:
        return None
    return record.lifecycle_phase if record else None


def _mark_project_lifecycle(memory_dir: Path, visitor_id: str, phase: str) -> None:
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return
    try:
        from app.integration.project_platform.store import ProjectStore
        from app.integration.project_platform.schema import TimelineEvent
        import uuid
        from datetime import datetime, timezone

        record = ProjectStore(memory_dir).load(ws_id)
        if not record:
            return
        record.lifecycle_phase = phase  # type: ignore[assignment]
        if phase == LIFECYCLE_APPROVAL:
            record.timeline.append(
                TimelineEvent(
                    id=f"tl-{uuid.uuid4().hex[:8]}",
                    type="approval",
                    label="Клиент согласовал версию",
                    at=datetime.now(timezone.utc).isoformat(),
                    detail="Готов к оформлению",
                )
            )
            record.next_step_hint = "Оформление заказа — фиксируем согласованную версию"
        record.updated_at = datetime.now(timezone.utc).isoformat()
        ProjectStore(memory_dir).save(record)
    except Exception:
        pass


def _project_client_approved(memory_dir: Path, visitor_id: str) -> bool:
    phase = _project_lifecycle_phase(memory_dir, visitor_id)
    return phase in (LIFECYCLE_APPROVAL, LIFECYCLE_CHOICE, "handoff", "subscription")


def _try_site_soft_satisfaction(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    """«Мне нравится» — confirm completion before commerce."""
    g = (goal or "").strip()
    if not g or _SITE_EXPLICIT_APPROVAL.search(g):
        return None
    if not _SITE_SOFT_SATISFACTION.search(g):
        return None
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not _workspace_has_site_preview(memory_dir, ws_id):
        return None
    if _project_client_approved(memory_dir, visitor_id):
        return None
    preview_path = _preview_href(ws_id, visitor_id)
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
        "cta_label": "🌐 Открыть сайт",
        "cta_actions": [
            {"href": preview_path, "label": "🌐 Открыть сайт", "group": "artifacts", "available": True},
        ],
        "context": {"journey_step": "approval_check", "co_design": False},
    }


def _try_site_explicit_approval(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    """Explicit «всё устраивает» — fix version, open order path (no regen)."""
    g = (goal or "").strip()
    if not g or not _SITE_EXPLICIT_APPROVAL.search(g):
        return None
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not _workspace_has_site_preview(memory_dir, ws_id):
        return None
    _mark_project_lifecycle(memory_dir, visitor_id, LIFECYCLE_APPROVAL)
    preview_path = _preview_href(ws_id, visitor_id)
    from app.integration.delivery_engine.handoff import build_order_href

    order_href = build_order_href(
        service_id=SERVICE_WEBSITE,
        visitor_id=visitor_id,
        workspace_id=ws_id,
        purchase_type="one_time",
    )
    return {
        "answer": (
            "Отлично.\n"
            "Тогда фиксируем именно эту версию сайта.\n"
            "Следующий шаг — оформить проект, после чего мы подготовим его к публикации.\n\n"
            "Когда будете готовы — напишите «хочу заказать» или откройте оформление."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": order_href,
        "cta_label": "📋 Оформить проект",
        "cta_actions": [
            {"href": preview_path, "label": "🌐 Открыть сайт", "group": "artifacts", "available": True},
            {"href": order_href, "label": "📋 Оформить проект", "group": "next", "available": True},
        ],
        "context": {"journey_step": "approval", "co_design": False},
    }


def _try_site_purchase_inquiry(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    """After approval — route «хочу заказать» to order, never regenerate."""
    if not _SITE_PURCHASE.search((goal or "").strip()):
        return None
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not _workspace_has_site_preview(memory_dir, ws_id):
        return None
    preview_path = _preview_href(ws_id, visitor_id)
    if not _project_client_approved(memory_dir, visitor_id):
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
            "cta_label": "🌐 Открыть сайт",
            "cta_actions": [
                {"href": preview_path, "label": "🌐 Открыть сайт", "group": "artifacts", "available": True},
            ],
            "context": {"journey_step": "approval_required"},
        }
    from app.integration.delivery_engine.handoff import build_order_href

    order_href = build_order_href(
        service_id=SERVICE_WEBSITE,
        visitor_id=visitor_id,
        workspace_id=ws_id,
        purchase_type="one_time",
    )
    _mark_project_lifecycle(memory_dir, visitor_id, LIFECYCLE_CHOICE)
    return {
        "answer": (
            "Отлично.\n"
            "Тогда фиксируем именно эту версию сайта.\n"
            "Следующий шаг — оформить проект, после чего мы подготовим его к публикации."
        ),
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": order_href,
        "cta_label": "📋 Оформить проект",
        "cta_actions": [
            {"href": preview_path, "label": "🌐 Открыть сайт", "group": "artifacts", "available": True},
            {"href": order_href, "label": "📋 Оформить проект", "group": "next", "available": True},
        ],
        "context": {"journey_step": "order"},
    }


def _try_site_revision(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
) -> dict[str, Any] | None:
    """Regenerate site from stable project brief — revision notes must not become page copy."""
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or not _workspace_has_site_preview(memory_dir, ws_id):
        return None
    if not _is_site_revision_request(goal):
        return None
    brief = _project_business_brief(memory_dir, visitor_id)
    if not brief or _site_brief_insufficient(brief):
        return None
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        ProjectPlatformService(memory_dir).bootstrap_from_message(visitor_id, goal)
    except Exception:
        pass
    return _run_generate_site(
        brief,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        revision_note=(goal or "").strip()[:200],
    )


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


def _workspace_has_site_preview(memory_dir: Path, workspace_id: str) -> bool:
    ws_store = ExecutionWorkspaceStore(memory_dir)
    preview = ws_store.path_for(workspace_id, "artifacts") / "preview" / "index.html"
    return preview.is_file()


def _has_specific_business_facts(goal: str) -> bool:
    g = (goal or "").strip()
    if not g:
        return False
    if re.search(r"(?:компани[яи]|фирм[аы]|бренд)\s+[A-ZА-ЯЁ][\w\-]+", g, re.IGNORECASE):
        return True
    if re.search(r"название\s*[-—:]\s*\S", g, re.IGNORECASE):
        return True
    if re.search(r"\b[A-Z][a-z]+(?:Team|Line|Tech|GmbH|AG|Solar)(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?\b", g):
        return True
    lower = g.lower()
    has_industry = bool(_BUSINESS_CONTEXT.search(g)) and not _GENERIC_COMPANY_REF.search(g)
    has_geo = bool(re.search(r"германи|germany|deutschland|berlin|росси|russia", lower))
    has_cta = bool(re.search(r"заявк|консультац|запис|позвон|купить|order|contact", lower))
    if has_industry and (has_geo or has_cta):
        return True
    if len(g.split()) >= 10 and has_industry:
        return True
    return False


_SITE_GOAL_INTENT = re.compile(
    r"(?:заявк|консультац|позвон|запис|купить|заказ|связ|contact|order|call|book|signup|cta|написать)",
    re.IGNORECASE,
)
_SITE_STYLE_INTENT = re.compile(
    r"(?:стиль|дизайн|modern|минимал|тёмн|темн|светл|корпоратив|делов|clean|премиум|элегант|строг)",
    re.IGNORECASE,
)
_SITE_COLORS_INTENT = re.compile(
    r"(?:"
    r"цвет|палитр|зелён|зелен|син|красн|бел|чёрн|черн|gold|orange|blue|#(?:[0-9a-f]{3}){1,2}\b|"
    r"бело-зелён|тёмно-сер|оставляем|оставим|подходит|этот\s+вариант|используем\s+этот"
    r")",
    re.IGNORECASE,
)
_SITE_LOGO_INTENT = re.compile(
    r"(?:"
    r"логотип|\blogo\b|без\s+логотип|нет\s+логотип|прикреп|"
    r"текстов|продолжаем|продолжим|позже|пришл|хорошо|"
    r"готов\s+к\s+концепц"
    r")",
    re.IGNORECASE,
)
_SITE_MATERIALS_INTENT = re.compile(
    r"(?:"
    r"материал|фото|изображен|картин|ссылк|"
    r"пока\s+без\s+материал|готов\s+контент|то\s+что|"
    r"используй\s+описан|используйте\s+то|"
    r"временные\s+материал|временный\s+контент"
    r")",
    re.IGNORECASE,
)

_SITE_CO_DESIGN_ORDER: tuple[str, ...] = (
    "company",
    "goal",
    "style",
    "colors",
    "logo",
    "materials",
)

_SITE_JOURNEY_QUESTIONS: dict[str, str] = {
    "company": "Как называется компания и чем вы занимаетесь?",
    "goal": (
        "Что человек должен сделать на сайте — оставить заявку, позвонить, "
        "записаться или купить?"
    ),
    "style": (
        "Какой визуальный стиль вам ближе — современный минимализм, деловой, "
        "светлый или тёмный?"
    ),
    "colors": "Есть фирменные цвета или пожелания по палитре?",
    "logo": (
        "Есть готовый логотип? Можете прикрепить файл или написать «без логотипа»."
    ),
    "materials": (
        "Есть фото, тексты или ссылки для сайта — или пока работаем с тем, что уже описали?"
    ),
}


def _site_reflection_block(combined: str) -> str:
    """T-002 — Reflection before Direction: user must feel understood."""
    from app.integration.project_platform.journey_state import (
        extract_city_label,
        extract_company_name,
        extract_industry_label,
        extract_site_goal_label,
    )

    text = (combined or "").strip()
    if not text:
        return "Понял."

    company = extract_company_name(text)
    industry = extract_industry_label(text)
    city = extract_city_label(text)
    goal = extract_site_goal_label(text)

    if not any((company, industry, city, goal)):
        return "Записал."

    lines = ["Понял.", ""]
    if company:
        if industry and city:
            lines.append(f"**{company}** — {industry} из {city}.")
        elif industry:
            lines.append(f"**{company}** — {industry}.")
        elif city:
            lines.append(f"**{company}** из {city}.")
        else:
            lines.append(f"**{company}**.")
    elif industry and city:
        lines.append(f"{industry.capitalize()} из {city}.")
    elif industry:
        lines.append(f"{industry.capitalize()}.")

    if goal:
        lines.append(f"Главная задача сайта — {goal}.")

    lines.extend(["", "Это зафиксировал."])
    return "\n".join(lines)


def _site_development_hint(combined: str) -> str | None:
    """T-003 — Professional Surprise when industry knowledge exists."""
    from app.integration.vector_intelligence.industry_intelligence import (
        build_decision_leadership_response,
    )

    surprise = build_decision_leadership_response(combined)
    if surprise:
        return surprise

    low = (combined or "").lower()
    if re.search(r"строитель|ремонт|бригад|handwerk|bau", low):
        return (
            "Тогда сайт сразу будем строить вокруг доверия: "
            "примеры работ, отзывы клиентов и быстрый способ оставить заявку."
        )
    if re.search(r"стоматолог|dental|клиник", low):
        return (
            "Сайт соберём вокруг спокойствия и записи: услуги, врачи "
            "и простая форма записи или звонка."
        )
    if re.search(r"кафе|кофе|ресторан|cafe", low):
        return (
            "Сделаем акцент на атмосфере и меню — и кнопку заказа столика "
            "или доставки на видном месте."
        )
    if re.search(r"солнеч|solar|панел", low):
        return (
            "Сайт выстроим вокруг выгод для клиента, примеров объектов "
            "и быстрой заявки на расчёт."
        )
    if re.search(r"заявк", low):
        return (
            "Сайт сразу соберём так, чтобы заявку можно было оставить "
            "без лишних шагов."
        )
    return None


def _site_understanding_ack(combined: str) -> str:
    """Legacy alias — reflection replaces generic ack."""
    return _site_reflection_block(combined)


def _site_style_pm_proposal(combined: str) -> str:
    """Professional style recommendation before asking override."""
    low = (combined or "").lower()
    if re.search(r"солнеч|solar|панел|энерг", low):
        lead = (
            "Для компаний в солнечной энергетике обычно работает **светлый минимализм** — "
            "чистый, технологичный, вызывает доверие."
        )
    elif re.search(r"стоматолог|dental|клиник", low):
        lead = (
            "Для медицинских клиник чаще выбирают **светлый деловой** стиль — "
            "спокойный, аккуратный, без визуального шума."
        )
    elif re.search(r"кафе|кофе|ресторан|cafe", low):
        lead = (
            "Для кафе и ресторанов хорошо работает **тёплый современный** стиль — "
            "уютный, но не устаревший."
        )
    elif re.search(r"строитель|ремонт|бригад|handwerk|bau", low):
        lead = (
            "Для строительных компаний с заявками я бы начал со **светлого минимализма** — "
            "спокойный, надёжный, без лишнего."
        )
    else:
        lead = (
            "Для сайта с заявками я бы начал со **светлого минимализма** — "
            "понятный и аккуратный."
        )
    return (
        f"{lead}\n\n"
        "Берём такой стиль или вам ближе другой — деловой, тёмный, премиум?"
    )


def _site_color_pm_proposal(combined: str) -> str:
    """Professional palette — Vector leads, client confirms or overrides."""
    from app.integration.project_platform.journey_state import extract_company_name

    company = extract_company_name(combined or "")
    subject = company if company else "вашего проекта"
    low = (combined or "").lower()

    if re.search(r"солнеч|solar|панел|энерг", low):
        proposal = (
            f"Для **{subject}** я бы предложил **бело-зелёную палитру с тёмно-серым текстом**.\n"
            "Такая комбинация хорошо работает для компаний в солнечной энергетике: "
            "выглядит современно, экологично и вызывает доверие."
        )
    elif re.search(r"стоматолог|dental|клиник", low):
        proposal = (
            f"Для **{subject}** я бы предложил **сине-белую палитру с тёмно-серым текстом** — "
            "спокойную и привычную для медицинских услуг."
        )
    elif re.search(r"кафе|кофе|ресторан|cafe", low):
        proposal = (
            f"Для **{subject}** я бы предложил **тёплую кремово-коричневую палитру** — "
            "уютную, но современную."
        )
    else:
        proposal = (
            f"Для **{subject}** я бы предложил **нейтральную палитру с одним акцентным цветом** — "
            "читаемую и легко менять позже."
        )

    return (
        f"{proposal}\n\n"
        "Если у вас уже есть фирменные цвета — адаптирую дизайн под них.\n"
        "Если нет — предлагаю использовать этот вариант как основу.\n\n"
        "Оставляем этот вариант или хотите другую палитру?"
    )


def _site_logo_pm_proposal(combined: str) -> str:
    """Default text logo — project never waits for assets."""
    from app.integration.project_platform.journey_state import extract_company_name

    company = extract_company_name(combined or "")
    label = company if company else "компании"
    return (
        f"Пока предлагаю использовать аккуратный **текстовый логотип {label}** "
        f"в фирменных цветах.\n"
        f"Когда появится готовый логотип — просто заменю его без изменения дизайна сайта.\n\n"
        f"Если логотип уже есть — можете прислать его сейчас или позже."
    )


def _site_materials_pm_lead(combined: str) -> str:
    """PM narrative — work continues with professional placeholders."""
    low = (combined or "").lower()
    if re.search(r"солнеч|solar|панел|энерг", low):
        theme = "солнечной энергетики"
    elif re.search(r"стоматолог|dental|клиник", low):
        theme = "медицинских услуг"
    elif re.search(r"кафе|кофе|ресторан|cafe", low):
        theme = "общепита"
    else:
        theme = "вашей сферы"

    return (
        "Отлично.\n"
        "Тогда первую концепцию я соберу на основе того, что мы уже определили.\n"
        f"Пока использую временные фотографии и тексты по теме {theme}.\n"
        "Когда появятся собственные материалы — просто заменю их, не меняя структуру сайта.\n\n"
        "Если захотите — можете прислать материалы сейчас или позже."
    )


def _run_first_concept_with_temp_materials(
    combined: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    goal: str,
) -> dict[str, Any]:
    """Only materials missing — Vector defaults to placeholders and advances the project."""
    lead = _site_materials_pm_lead(combined)
    try:
        ws_id = _existing_workspace_id(memory_dir, visitor_id)
        if ws_id:
            from app.integration.project_platform.store import ProjectStore

            record = ProjectStore(memory_dir).load(ws_id)
            if record:
                record.next_step_hint = (
                    "Временные материалы в концепции — замена без смены структуры"
                )
                ProjectStore(memory_dir).save(record)
    except Exception:
        pass
    from app.factory.analyzer import business_brief_for_site

    brief = business_brief_for_site(combined) or combined.strip()
    out = _run_generate_site(brief, visitor_id=visitor_id, memory_dir=memory_dir)
    prior = (out.get("answer") or "").strip()
    if prior.lower().startswith("отлично."):
        prior = prior.split("\n", 1)[-1].strip() if "\n" in prior else ""
    out["answer"] = f"{lead}\n\n{prior}" if prior else lead
    return out


def _site_co_design_flags(
    text: str,
    *,
    attachment_files: list[dict[str, Any]] | None = None,
) -> dict[str, bool]:
    g = (text or "").strip()
    has_logo_file = any(
        re.search(r"logo|логотип", str(f.get("name") or ""), re.I)
        for f in (attachment_files or [])
    )
    return {
        "company": _has_specific_business_facts(g),
        "goal": bool(_SITE_GOAL_INTENT.search(g)),
        "style": bool(_SITE_STYLE_INTENT.search(g)),
        "colors": bool(_SITE_COLORS_INTENT.search(g)),
        "logo": bool(_SITE_LOGO_INTENT.search(g) or has_logo_file),
        "materials": bool(_SITE_MATERIALS_INTENT.search(g)),
    }


def _next_site_co_design_gap(
    text: str,
    *,
    attachment_files: list[dict[str, Any]] | None = None,
) -> str | None:
    flags = _site_co_design_flags(text, attachment_files=attachment_files)
    for step in _SITE_CO_DESIGN_ORDER:
        if not flags.get(step):
            return step
    return None


def _only_materials_step_missing(
    text: str,
    *,
    attachment_files: list[dict[str, Any]] | None = None,
) -> bool:
    flags = _site_co_design_flags(text, attachment_files=attachment_files)
    missing = [step for step in _SITE_CO_DESIGN_ORDER if not flags.get(step)]
    return missing == ["materials"]


def _site_journey_step_response(
    gap: str,
    *,
    combined: str,
    visitor_id: str,
    memory_dir: Path,
    goal: str = "",
) -> dict[str, Any]:
    """PE co-design — Reflection before Direction (T-002)."""
    question = _SITE_JOURNEY_QUESTIONS.get(gap, "Расскажите ещё немного о проекте.")
    reflection = _site_reflection_block(combined)
    development = _site_development_hint(combined)
    parts: list[str] = []

    if gap == "company":
        parts.append(reflection if reflection != "Записал." else "Проект создан.")
        parts.append(question)
    elif gap == "goal":
        surprise = None
        try:
            from app.integration.vector_intelligence.industry_intelligence import (
                build_decision_leadership_response,
                profession_style_followup,
            )

            surprise = build_decision_leadership_response(combined)
        except Exception:
            surprise = None

        if surprise and _SITE_GOAL_INTENT.search(combined):
            parts.append(surprise)
            followup = profession_style_followup(combined)
            if followup:
                parts.append(followup)
        elif reflection != "Записал.":
            parts.append(reflection)
        else:
            parts.append("Записал.")
        if not surprise and development:
            parts.append(development)
        if not _SITE_GOAL_INTENT.search(combined):
            parts.append(question)
        elif not surprise:
            parts.append(_site_style_pm_proposal(combined))
    elif gap == "style":
        surprise = None
        try:
            from app.integration.vector_intelligence.industry_intelligence import (
                build_decision_leadership_response,
                profession_style_followup,
            )

            surprise = build_decision_leadership_response(combined)
        except Exception:
            surprise = None

        if surprise:
            parts.append(surprise)
            followup = profession_style_followup(combined)
            if followup:
                parts.append(followup)
        else:
            if reflection != "Записал.":
                parts.append(reflection)
            if development:
                parts.append(development)
            parts.append(_site_style_pm_proposal(combined))
    elif gap == "colors":
        parts.append("Стиль зафиксировал.")
        parts.append(_site_color_pm_proposal(combined))
    elif gap == "logo":
        parts.append("Отлично. Палитру фиксирую.")
        parts.append(_site_logo_pm_proposal(combined))
    elif gap == "materials":
        parts.append("Отлично.")
        parts.append(_site_materials_pm_lead(combined).split("\n", 1)[-1].strip())
    else:
        parts.append("Записал.")
        parts.append(question)

    answer = "\n\n".join(p for p in parts if p.strip())
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        svc = ProjectPlatformService(memory_dir)
        svc.bootstrap_from_message(visitor_id, goal or combined)
        record_hint = {
            "company": "узнаём компанию и сферу",
            "goal": "уточняем цель сайта",
            "style": "выбираем стиль",
            "colors": "согласуем цвета",
            "logo": "текстовый логотип по умолчанию, замена когда появится",
            "materials": "временные материалы, замена без смены структуры",
        }
        state = svc.get_for_visitor(visitor_id)
        ws_id = (state.get("project") or {}).get("workspace_id")
        if ws_id:
            from app.integration.project_platform.store import ProjectStore

            record = ProjectStore(memory_dir).load(ws_id)
            if record:
                record.next_step_hint = record_hint.get(gap, question)
                ProjectStore(memory_dir).save(record)
    except Exception:
        pass
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "execution",
        "cta_href": None,
        "cta_label": None,
        "context": {"journey_step": gap, "co_design": True},
    }


def _accumulated_project_text(memory_dir: Path, visitor_id: str) -> str:
    """All user turns stored on the project — journey gates must not depend on chat history alone."""
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return ""
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(ws_id)
    except Exception:
        return ""
    if not record:
        return ""
    parts: list[str] = []
    if record.description.strip():
        parts.append(record.description.strip())
    for event in record.timeline or []:
        detail = (event.detail or "").strip()
        if detail and detail not in parts:
            parts.append(detail)
    return "\n".join(parts).strip()


def _combined_site_dialog(
    text: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    history: list[dict[str, str]] | None = None,
) -> str:
    chunks: list[str] = []
    project_text = _accumulated_project_text(memory_dir, visitor_id)
    if project_text:
        chunks.append(project_text)
    hist = _brief_from_history(history, tail="")
    if hist:
        chunks.append(hist)
    if text.strip():
        chunks.append(text.strip())
    return "\n".join(chunks).strip()


def _maybe_gate_site_concept(
    text: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    goal: str = "",
    attachment_files: list[dict[str, Any]] | None = None,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    """Block first concept until co-design journey steps are collected together."""
    combined = _combined_site_dialog(
        text,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        history=history,
    )
    if _site_brief_insufficient(combined):
        return None
    if _only_materials_step_missing(combined, attachment_files=attachment_files):
        return _run_first_concept_with_temp_materials(
            combined,
            visitor_id=visitor_id,
            memory_dir=memory_dir,
            goal=goal or text,
        )
    gap = _next_site_co_design_gap(combined, attachment_files=attachment_files)
    if not gap:
        return None
    return _site_journey_step_response(
        gap,
        combined=combined,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        goal=goal or text,
    )


def _site_brief_insufficient(goal: str) -> bool:
    g = goal.strip()
    if not g:
        return True
    if _has_specific_business_facts(g):
        return False
    if _GENERIC_COMPANY_REF.search(g):
        return True
    site_for = re.search(r"сайт\s+для\s+(\w+)", g, re.IGNORECASE)
    if site_for and site_for.group(1).lower() in _SITE_FOR_GENERIC:
        return True
    if _BUSINESS_CONTEXT.search(g):
        return False
    if site_for:
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
    visitor_id: str = "anonymous",
    memory_dir: Path | None = None,
) -> dict[str, Any]:
    if from_project:
        intro = (
            "Использую информацию из вашего проекта.\n"
            "Начинаю подготовку сайта."
        )
    else:
        intro = project_execution_ack_intro(SERVICE_WEBSITE)
    answer = intro
    if not from_project:
        if memory_dir is not None and delivery_engine_enabled(memory_dir):
            from app.integration.delivery_engine import DeliveryEngine

            DeliveryEngine(memory_dir).note_consultation(
                visitor_id, service_id=SERVICE_WEBSITE, goal=goal
            )
        ctx = resolve_market_context(text=goal, ui_locale=ui_locale)
        market_q = market_clarification_question(ctx, locale=ui_locale)
        if market_q and ctx.target_market_code == MARKET_DEFAULT:
            answer = f"{intro}\n\n{market_q}"
    return {
        "answer": answer,
        "source": "genesis-ai",
        "mode": "genesis",
        "provider": "delivery_engine" if not from_project and memory_dir and delivery_engine_enabled(memory_dir) else "execution",
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


def _build_site_completion_answer(
    preview_path: str,
    reuse_note: str = "",
    *,
    revision: bool = False,
    revision_note: str = "",
) -> str:
    if revision:
        detail = (revision_note or "").strip()
        if len(detail) > 96:
            detail = detail[:93] + "..."
        lead = (
            "Готово — внёс правку в проект"
            + (f": {detail}" if detail else "")
            + ".\n"
            "Обновлённая версия уже в проекте — посмотрите, всё ли так, как вы хотели."
        )
        answer = f"{lead}\n\n{website_concept_ready_message()}"
    else:
        answer = (
            "Отлично.\n"
            "Я подготовил первую концепцию вашего сайта.\n\n"
            f"{website_concept_ready_message()}"
        )
    if reuse_note:
        answer = f"{answer}\n\n{reuse_note.strip()}"
    return answer


def _project_awaiting_first_site(memory_dir: Path, visitor_id: str) -> tuple[str, str] | None:
    ws_id = _existing_workspace_id(memory_dir, visitor_id)
    if not ws_id or _workspace_has_site_preview(memory_dir, ws_id):
        return None
    try:
        from app.integration.project_platform.store import ProjectStore

        record = ProjectStore(memory_dir).load(ws_id)
    except Exception:
        return None
    if not record or record.service_id != SERVICE_WEBSITE or record.mode != "project":
        return None
    if record.versions and any(
        a.kind == "preview"
        for ver in record.versions
        for a in ver.artifacts
    ):
        return None
    parts = [record.description.strip()] if record.description.strip() else []
    return ws_id, "\n".join(parts)


def _brief_from_history(history: list[dict[str, str]] | None, *, tail: str) -> str:
    """Combine recent user turns with the current message for site brief detection."""
    chunks: list[str] = []
    for row in history or []:
        if (row.get("role") or "").strip() != "user":
            continue
        part = (row.get("content") or "").strip()
        if part:
            chunks.append(part)
    if tail.strip():
        chunks.append(tail.strip())
    return "\n".join(chunks).strip()


def _try_site_from_project_brief(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any] | None:
    """PE-2 — after sufficient brief in an active website project, show first concept."""
    pending = _project_awaiting_first_site(memory_dir, visitor_id)
    if not pending:
        return None
    _ws_id, _prior = pending
    text = (goal or "").strip()
    if not text or _parse_site_request(text):
        return None
    accumulated = _accumulated_project_text(memory_dir, visitor_id)
    combined = f"{accumulated}\n{text}".strip() if accumulated else text
    if _site_brief_insufficient(combined):
        combined = _brief_from_history(history, tail=text)
    if _site_brief_insufficient(combined):
        return None
    gated = _maybe_gate_site_concept(
        text,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        goal=text,
        history=history,
    )
    if gated:
        return gated
    from app.factory.analyzer import business_brief_for_site

    cleaned = business_brief_for_site(combined)
    if cleaned:
        combined = cleaned
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        ProjectPlatformService(memory_dir).bootstrap_from_message(visitor_id, text)
    except Exception:
        pass
    return _run_generate_site(combined, visitor_id=visitor_id, memory_dir=memory_dir)


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


def _record_project_execution(
    *,
    visitor_id: str,
    workspace_id: str,
    capability_id: str,
    outputs: dict[str, Any],
    goal: str = "",
    memory_dir: Path,
) -> None:
    try:
        from app.integration.project_platform.service import ProjectPlatformService

        ProjectPlatformService(memory_dir).record_execution(
            visitor_id=visitor_id,
            workspace_id=workspace_id,
            capability_id=capability_id,
            outputs=outputs,
            goal=goal,
        )
    except Exception:
        pass


def try_user_execution(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    attachment_files: list[dict[str, Any]] | None = None,
    ui_locale: str | None = None,
    history: list[dict[str, str]] | None = None,
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

    from app.integration.vector_intelligence.guided_execution import (
        try_guided_execution_route,
    )

    guided_out = try_guided_execution_route(
        goal,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        history=history,
    )
    if guided_out:
        return guided_out

    from app.integration.vector_intelligence.decision_intelligence import (
        try_decision_intelligence_route,
    )

    decision_out = try_decision_intelligence_route(goal)
    if decision_out:
        return decision_out

    from app.execution.project_bridge.router import try_project_execution

    project_out = try_project_execution(
        goal,
        visitor_id=visitor_id,
        memory_dir=memory_dir,
        attachment_files=files,
        ui_locale=ui_locale,
        history=history,
    )
    if project_out:
        return project_out

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
        _record_project_execution(
            visitor_id=visitor_id,
            workspace_id=workspace_id,
            capability_id="filesystem_write",
            outputs=cap,
            goal=goal,
            memory_dir=memory_dir,
        )
        file_answer = (
            f"✓ Документ создан: **{cap.get('path') or filename}**\n\n"
            f"{universal_first_version_scenario()}"
        )
        out = finalize_execution_response(
            memory_dir,
            visitor_id=visitor_id,
            workspace_id=workspace_id,
            capability_id="filesystem_write",
            outputs=cap,
            goal=goal,
            primary_href=file_href,
            primary_label="Открыть файл",
            answer_override=file_answer,
        )
        out["context"] = {
            **(out.get("context") or {}),
            "execution": result.to_dict(),
            "capability_result": cap,
            "workspace_id": workspace_id,
        }
        return out

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
    _record_project_execution(
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        capability_id="analyze_business_document",
        outputs=cap,
        goal=str(doc_req.get("goal") or ""),
        memory_dir=memory_dir,
    )
    out = finalize_execution_response(
        memory_dir,
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        capability_id="analyze_business_document",
        outputs=cap,
        goal=str(doc_req.get("goal") or ""),
        primary_href=summary_href,
        primary_label="📊 Executive Summary",
        extra_ctas=cta_actions,
        answer_override=answer,
    )
    out["context"] = {
        **(out.get("context") or {}),
        "execution": result.to_dict(),
        "capability_result": cap,
        "document_type": doc_type,
        "execution_kind": "document_analysis",
        "source_filename": source_name,
        "pages_analyzed": pages,
        "readiness_score": readiness,
        "issues_count": issues_count,
        "report_locale": report_locale,
    }
    return out


def _run_generate_site(
    goal: str,
    *,
    visitor_id: str,
    memory_dir: Path,
    revision_note: str = "",
) -> dict[str, Any]:
    from app.factory.analyzer import business_brief_for_site

    brief = business_brief_for_site(goal) or goal.strip()
    workspace_id = _workspace_for_visitor(memory_dir, visitor_id, title="Site project")
    registry = get_execution_registry(memory_dir)
    ws_store = ExecutionWorkspaceStore(memory_dir)
    logs = ExecutionLogStore(memory_dir)
    mgr = ExecutionManager(registry=registry, workspace_store=ws_store, log_store=logs)

    plan = ExecutionPlan(
        plan_id="",
        goal=brief.strip(),
        workspace_id=workspace_id,
        steps=(
            ExecutionStep(
                id="step-generate-site",
                capability_id="generate_site",
                title="Generate site from brief",
                inputs={"brief": brief.strip(), "workspace_id": workspace_id},
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
    answer = _build_site_completion_answer(
        preview_path,
        reuse_note,
        revision=bool(revision_note.strip()),
        revision_note=revision_note,
    )
    cta_actions = _site_customer_ctas(preview_path)
    _record_project_execution(
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        capability_id="generate_site",
        outputs=cap,
        goal=brief,
        memory_dir=memory_dir,
    )
    out = finalize_execution_response(
        memory_dir,
        visitor_id=visitor_id,
        workspace_id=workspace_id,
        capability_id="generate_site",
        outputs=cap,
        goal=goal,
        preview_href=preview_path,
        primary_href=preview_path,
        primary_label="🌐 Открыть сайт",
        extra_ctas=cta_actions,
        answer_override=answer,
    )
    out["context"] = {
        **(out.get("context") or {}),
        "execution": result.to_dict(),
        "capability_result": cap,
        "preview_url": preview_path,
        "artifact_type": "website",
    }
    return out


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
