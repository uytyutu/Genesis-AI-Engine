"""Project identity, visual progress, and artifact folders — product polish layer."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from app.integration.product_line import (
    ASSISTANT_NAME,
    LIFECYCLE_APPROVAL,
    LIFECYCLE_CHOICE,
    LIFECYCLE_COLLABORATION,
    LIFECYCLE_CONCEPT,
    LIFECYCLE_DIALOG,
    LIFECYCLE_HANDOFF,
    SERVICE_BUSINESS_PLAN,
    SERVICE_PRESENTATION,
    SERVICE_WEBSITE,
    artifact_label_ru,
    service_label_ru,
)
from app.integration.project_platform.schema import (
    SECTION_BUSINESS_PLAN,
    SECTION_DOCUMENTS,
    SECTION_WEBSITE,
    ProjectArtifact,
    ProjectRecord,
)

VISUAL_STAGES: tuple[tuple[str, str], ...] = (
    ("analysis", "Анализ"),
    ("concept", "Концепция"),
    ("design", "Дизайн"),
    ("review", "Проверка"),
    ("handoff", "Передача"),
)

ARTIFACT_FOLDERS: tuple[tuple[str, str], ...] = (
    ("website", "Ваш сайт"),
    ("business_plan", "Бизнес-план"),
    ("presentation", "Презентация"),
    ("documents", "Результаты работы"),
    ("images", "Изображения"),
    ("source", "Исходные материалы"),
    ("archive", "Архив"),
)

_MARKET_HINTS: tuple[tuple[str, str], ...] = (
    ("берлин", "Берлин, Германия"),
    ("мюнхен", "Мюнхен, Германия"),
    ("гамбург", "Гамбург, Германия"),
    ("франкфурт", "Франкфурт, Германия"),
    ("кёльн", "Кёльн, Германия"),
    ("москв", "Москва, Россия"),
    ("петербург", "Санкт-Петербург, Россия"),
    ("берлине", "Берлин, Германия"),
    ("мюнхене", "Мюнхен, Германия"),
    ("berlin", "Berlin, Germany"),
    ("munich", "Munich, Germany"),
    ("hamburg", "Hamburg, Germany"),
    ("germany", "Germany"),
    ("deutschland", "Germany"),
    ("герман", "Германия"),
    ("росси", "Россия"),
    ("russia", "Russia"),
    ("ukraine", "Ukraine"),
    ("украин", "Украина"),
    ("poland", "Poland"),
    ("польш", "Польша"),
    ("austria", "Austria"),
    ("австри", "Австрия"),
    ("switzerland", "Switzerland"),
    ("швейцар", "Швейцария"),
)


def infer_market(text: str) -> str:
    t = (text or "").lower()
    for key, label in _MARKET_HINTS:
        if key in t:
            return label
    m = re.search(r"\bв\s+([А-ЯЁA-Z][а-яёa-z\-]{2,})\b", text or "", re.I)
    if m:
        place = m.group(1).strip()
        return place[0].upper() + place[1:] if place else "Не указан"
    return "Не указан"


def infer_description(record: ProjectRecord, *, goal: str = "") -> str:
    if record.description.strip():
        return record.description.strip()
    g = (goal or record.title or "").strip()
    if len(g) > 12:
        return g[:180] + ("…" if len(g) > 180 else "")
    svc = service_label_ru(record.service_id or "", fallback="проект")
    return (
        f"{svc} под управлением {ASSISTANT_NAME}. "
        "Работаем до согласованного результата — каждая версия сохраняется в проекте."
    )


def status_label(record: ProjectRecord) -> str:
    phase = record.lifecycle_phase
    has_versions = bool(record.versions)
    if phase == LIFECYCLE_HANDOFF:
        return "Передача результата"
    if phase == LIFECYCLE_CHOICE:
        return "Выбор формата сотрудничества"
    if phase == LIFECYCLE_APPROVAL:
        return "На согласовании"
    if phase == LIFECYCLE_COLLABORATION:
        return "Совместная доработка" if has_versions else "Подготовка первой версии"
    if phase == LIFECYCLE_CONCEPT:
        return "Формирование концепции"
    if phase == LIFECYCLE_DIALOG:
        return "Анализ задачи" if not has_versions else "Уточнение требований"
    return "В работе"


def _current_visual_stage(record: ProjectRecord) -> str:
    phase = record.lifecycle_phase
    has_versions = bool(record.versions)
    if phase in (LIFECYCLE_HANDOFF, LIFECYCLE_CHOICE):
        return "handoff"
    if phase == LIFECYCLE_APPROVAL:
        return "review"
    if phase == LIFECYCLE_COLLABORATION:
        return "design" if has_versions else "concept"
    if phase == LIFECYCLE_CONCEPT:
        return "concept"
    if has_versions:
        return "design"
    return "analysis"


def build_progress(record: ProjectRecord) -> dict[str, Any]:
    current = _current_visual_stage(record)
    stage_ids = [s[0] for s in VISUAL_STAGES]
    current_idx = stage_ids.index(current)
    percent_map = (12, 28, 52, 78, 100)
    percent = percent_map[current_idx]
    if current == "design" and len(record.versions) > 1:
        percent = min(72, percent + len(record.versions) * 4)

    stages: list[dict[str, Any]] = []
    for i, (sid, label) in enumerate(VISUAL_STAGES):
        if i < current_idx:
            state = "done"
        elif i == current_idx:
            state = "current"
        else:
            state = "upcoming"
        stages.append({"id": sid, "label": label, "state": state})

    return {
        "percent": percent,
        "current_stage_id": current,
        "current_stage_label": dict(VISUAL_STAGES).get(current, current),
        "stages": stages,
    }


def format_last_updated(iso: str) -> str:
    if not iso:
        return "—"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt.astimezone(timezone.utc)
        mins = int(delta.total_seconds() // 60)
        if mins < 2:
            return "только что"
        if mins < 60:
            return f"{mins} мин назад"
        hours = mins // 60
        if hours < 24:
            return f"{hours} ч назад"
        days = hours // 24
        if days == 1:
            return "вчера"
        if days < 7:
            return f"{days} дн назад"
        return dt.strftime("%d.%m.%Y")
    except (ValueError, TypeError):
        return iso[:10] if len(iso) >= 10 else "—"


def build_identity(record: ProjectRecord) -> dict[str, Any]:
    svc_id = record.service_id or ""
    return {
        "title": record.title,
        "type_label": service_label_ru(svc_id, fallback="Проект"),
        "type_id": svc_id or None,
        "artifact_label": artifact_label_ru(svc_id, fallback="Результат"),
        "market": record.market or "Не указан",
        "status": status_label(record),
        "last_updated": format_last_updated(record.updated_at),
        "last_updated_at": record.updated_at,
        "description": infer_description(record),
    }


def build_project_health(record: ProjectRecord) -> dict[str, Any]:
    """Human project pulse — not a technical status code."""
    phase = record.lifecycle_phase
    has_versions = bool(record.versions)

    if phase in (LIFECYCLE_APPROVAL, LIFECYCLE_CHOICE):
        return {
            "tone": "yellow",
            "emoji": "🟡",
            "label": "Требуется ваше согласование",
        }
    if phase == LIFECYCLE_COLLABORATION and has_versions:
        return {
            "tone": "yellow",
            "emoji": "🟡",
            "label": "Требуется ваше согласование",
        }
    if phase == LIFECYCLE_HANDOFF:
        return {
            "tone": "green",
            "emoji": "🟢",
            "label": "Всё идёт по плану",
        }
    if phase in (LIFECYCLE_DIALOG, LIFECYCLE_CONCEPT):
        return {
            "tone": "blue",
            "emoji": "🔵",
            "label": f"{ASSISTANT_NAME} работает",
        }
    if phase == LIFECYCLE_COLLABORATION and not has_versions:
        return {
            "tone": "blue",
            "emoji": "🔵",
            "label": f"{ASSISTANT_NAME} работает",
        }
    if record.mode == "project" and not has_versions and not record.timeline:
        return {
            "tone": "red",
            "emoji": "🔴",
            "label": "Требуется внимание",
        }
    return {
        "tone": "green",
        "emoji": "🟢",
        "label": "Всё идёт по плану",
    }


def build_next_action(record: ProjectRecord) -> dict[str, Any]:
    """One obvious next step — user should not guess."""
    phase = record.lifecycle_phase
    has_versions = bool(record.versions)
    artifact = artifact_label_ru(record.service_id or "", fallback="результат")
    svc = service_label_ru(record.service_id or "", fallback="проект").lower()

    if phase == LIFECYCLE_CHOICE:
        return {"label": "Оплатить проект", "kind": "payment"}
    if phase == LIFECYCLE_APPROVAL:
        return {"label": "Подтвердить концепцию", "kind": "approve"}
    if phase == LIFECYCLE_HANDOFF:
        return {"label": "Получить финальную передачу", "kind": "handoff"}
    if phase == LIFECYCLE_COLLABORATION and has_versions:
        if record.service_id == SERVICE_WEBSITE:
            return {"label": "Посмотреть первую версию сайта", "kind": "review"}
        return {"label": f"Посмотреть первую версию — {artifact}", "kind": "review"}
    if phase in (LIFECYCLE_CONCEPT, LIFECYCLE_DIALOG) and record.mode == "project":
        return {"label": "Ответить на вопрос Vector", "kind": "chat"}
    if phase == LIFECYCLE_DIALOG:
        return {"label": "Описать задачу Vector", "kind": "chat"}
    if phase == LIFECYCLE_COLLABORATION:
        return {"label": f"Уточнить детали {svc} с Vector", "kind": "chat"}
    return {"label": "Продолжить работу с Vector", "kind": "chat"}


def build_last_activity(record: ProjectRecord) -> dict[str, Any]:
    """Recent pulse under progress — feels like a living project."""
    artifact = artifact_label_ru(record.service_id or "", fallback="проект")
    if not record.timeline:
        return {
            "summary": f"{ASSISTANT_NAME} готов начать работу над проектом",
            "when": "—",
        }

    event = record.timeline[-1]
    when = format_last_updated(event.at or record.updated_at)
    by_type: dict[str, str] = {
        "created": "Проект создан",
        "generation": f"{ASSISTANT_NAME} обновил {artifact}",
        "analysis": "Получен новый документ",
        "concept": event.detail or event.label or "Концепция обновлена",
        "approval": "Концепция согласована",
        "handoff": "Проект передан",
        "version": event.label,
        "note": event.label,
    }
    summary = by_type.get(event.type, event.label)
    if event.type == "generation" and record.versions:
        ver = record.versions[-1]
        summary = f"{ASSISTANT_NAME} обновил {artifact} · {ver.label}"
    return {"summary": summary, "when": when}


def classify_artifact_folder(art: ProjectArtifact, service_id: str | None) -> str:
    if art.kind == "zip":
        return "archive"
    if art.kind == "image":
        return "images"
    if art.kind == "source":
        return "source"
    if art.kind == "preview" or art.section == SECTION_WEBSITE:
        return "website"
    if art.section == SECTION_BUSINESS_PLAN or service_id == SERVICE_BUSINESS_PLAN:
        return "business_plan"
    if service_id == SERVICE_PRESENTATION:
        return "presentation"
    if art.kind in ("pdf", "report", "instructions") or art.section == SECTION_DOCUMENTS:
        return "documents"
    if service_id == SERVICE_WEBSITE and art.kind in ("file", "report"):
        return "website"
    return "documents"


def _display_artifact_label(art: ProjectArtifact) -> str:
    mapping = {
        "preview": "Просмотр",
        "source": "Исходные файлы",
        "zip": "Архив проекта",
        "pdf": "PDF-документ",
        "report": "Отчёт",
        "instructions": "Инструкции",
        "image": "Изображение",
    }
    return mapping.get(art.kind, art.label)


def build_artifact_folders(
    record: ProjectRecord,
    *,
    version: int | None = None,
) -> list[dict[str, Any]]:
    versions = record.versions
    if version is not None:
        versions = [v for v in versions if v.version == version]

    buckets: dict[str, list[dict[str, Any]]] = {fid: [] for fid, _ in ARTIFACT_FOLDERS}
    seen: set[str] = set()

    for ver in versions:
        for art in ver.artifacts:
            folder_id = classify_artifact_folder(art, record.service_id)
            dedupe = f"{folder_id}:{art.kind}:{art.label}:{art.href}"
            if dedupe in seen:
                continue
            seen.add(dedupe)
            buckets.setdefault(folder_id, []).append(
                {
                    "id": art.id,
                    "kind": art.kind,
                    "label": _display_artifact_label(art),
                    "href": art.href,
                    "version": ver.version,
                    "version_label": ver.label,
                }
            )

    out: list[dict[str, Any]] = []
    for fid, label in ARTIFACT_FOLDERS:
        items = buckets.get(fid) or []
        if not items:
            continue
        out.append(
            {
                "id": fid,
                "label": label,
                "count": len(items),
                "items": items,
            }
        )
    return out
