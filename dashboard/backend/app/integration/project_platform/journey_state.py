"""Website journey items — Project State source of truth (Vector memory, not LLM)."""

from __future__ import annotations

import re
from typing import Any

from app.integration.product_line import SERVICE_WEBSITE, service_label_ru
from app.integration.project_platform.identity import infer_market, status_label
from app.integration.project_platform.schema import ProjectRecord

_SITE_GOAL = re.compile(
    r"(?:заявк|консультац|позвон|запис|купить|заказ|связ|contact|order|call|book|signup|cta|написать)",
    re.IGNORECASE,
)
_SITE_STYLE = re.compile(
    r"(?:стиль|дизайн|modern|минимал|тёмн|темн|светл|корпоратив|делов|clean|премиум|элегант|строг)",
    re.IGNORECASE,
)
_SITE_COLORS = re.compile(
    r"(?:цвет|палитр|зелён|зелен|син|красн|бел|чёрн|черн|gold|orange|blue|#(?:[0-9a-f]{3}){1,2}\b)",
    re.IGNORECASE,
)
_SITE_LOGO = re.compile(
    r"(?:логотип|\blogo\b|без\s+логотип|нет\s+логотип|прикреп)",
    re.IGNORECASE,
)
_SITE_MATERIALS = re.compile(
    r"(?:"
    r"материал|фото|изображен|картин|ссылк|"
    r"пока\s+без\s+материал|готов\s+контент|то\s+что|"
    r"используй\s+описан|временные\s+материал"
    r")",
    re.IGNORECASE,
)
_COMPANY_NAME = re.compile(
    r"(?:компани[яи]|фирм[аы])\s+([A-ZА-ЯЁ][\w\-]+(?:\s+[A-ZА-ЯЁ][\w\-äöüÄÖÜß]+)?)",
    re.IGNORECASE,
)
_COMPANY_NAMED = re.compile(r"название\s*[-—:]\s*([^.!\n]{2,48})", re.IGNORECASE)
_BRAND_TOKEN = re.compile(
    r"\b([A-Z][a-z]+(?:Team|Line|Tech|GmbH|Solar)(?:\s+[A-ZÄÖÜ][a-zäöüß]+)?)\b"
)

_INDUSTRY_LABELS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(строитель|ремонт|бригад|bau|handwerk)", re.I), "строительная компания"),
    (re.compile(r"(стоматолог|dental|зуб)", re.I), "стоматология"),
    (re.compile(r"(кафе|кофе|ресторан|cafe)", re.I), "кафе / ресторан"),
    (re.compile(r"(салон|красот|beauty)", re.I), "салон красоты"),
    (re.compile(r"(солнеч|solar|панел)", re.I), "солнечная энергетика"),
)

_CITY_LABELS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(кёльн|колн|köln|cologne)", re.I), "Кёльн"),
    (re.compile(r"(берлин|berlin)", re.I), "Берлин"),
    (re.compile(r"(мюнхен|munich)", re.I), "Мюнхен"),
    (re.compile(r"(гамбург|hamburg)", re.I), "Гамбург"),
)

_DESIGN_VALUES: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"тёмн|темн|dark", re.I), "Modern Dark"),
    (re.compile(r"светл|light|минимал", re.I), "Light Minimal"),
    (re.compile(r"корпоратив|business|делов", re.I), "Business"),
)

_PANEL_STEPS: tuple[tuple[str, str], ...] = (
    ("type", "Тип проекта"),
    ("goal", "Цель"),
    ("company", "Компания"),
    ("country", "Страна"),
    ("structure", "Структура"),
    ("design", "Дизайн"),
    ("colors", "Цвета"),
    ("logo", "Логотип"),
    ("content", "Контент"),
    ("draft", "Черновик"),
    ("revisions", "Правки"),
    ("launch", "Готов к запуску"),
)


_BRAND_BLOCKLIST = frozenset({"virtus", "vector", "core", "virtuscore"})
_GENERIC_COMPANY_NAMES = frozenset(
    {"компания", "компании", "бизнес", "фирма", "фирмы", "бренд", "company", "business"}
)


def extract_company_name(text: str) -> str | None:
    t = text or ""
    m = _COMPANY_NAMED.search(t)
    if m:
        name = m.group(1).strip().rstrip(".")
        if name and name.lower() not in _BRAND_BLOCKLIST:
            return name
    for m in _COMPANY_NAME.finditer(t):
        name = m.group(1).strip()
        low = name.lower()
        if low in _BRAND_BLOCKLIST or low in _GENERIC_COMPANY_NAMES:
            continue
        return name
    m = _BRAND_TOKEN.search(t)
    if m:
        name = m.group(0)
        if name.lower() not in _BRAND_BLOCKLIST:
            return name
    return None


def extract_industry_label(text: str) -> str | None:
    for pattern, label in _INDUSTRY_LABELS:
        if pattern.search(text or ""):
            return label
    return None


def extract_city_label(text: str) -> str | None:
    for pattern, label in _CITY_LABELS:
        if pattern.search(text or ""):
            return label
    return None


def extract_site_goal_label(text: str) -> str | None:
    t = (text or "").lower()
    if re.search(r"заявк", t):
        if re.search(r"ремонт", t):
            return "чтобы люди оставляли заявки на ремонт"
        return "чтобы люди оставляли заявки"
    if re.search(r"позвон|телефон|звон", t):
        return "чтобы клиенты могли позвонить"
    if re.search(r"запис", t):
        return "чтобы клиенты записывались онлайн"
    if re.search(r"заказ|купить", t):
        return "чтобы можно было оформить заказ"
    if _SITE_GOAL.search(text or ""):
        return "чтобы посетители совершили нужное действие на сайте"
    return None


def accumulated_dialog_text(record: ProjectRecord) -> str:
    parts: list[str] = []
    if record.description.strip():
        parts.append(record.description.strip())
    for event in record.timeline or []:
        if event.type not in ("update", "note") and (event.label or "") != "Обновление проекта":
            continue
        detail = (event.detail or "").strip()
        if detail and detail not in parts:
            parts.append(detail)
    return "\n".join(parts).strip()


def _design_value(text: str) -> str | None:
    for pattern, label in _DESIGN_VALUES:
        if pattern.search(text):
            return label
    return None


def _colors_value(text: str) -> str | None:
    m = re.search(r"цвет[аы]?\s*[:—-]\s*([^.!\n]{3,48})", text or "", re.I)
    if m:
        return m.group(1).strip()
    if _SITE_COLORS.search(text or ""):
        return "Заданы"
    return None


def _logo_value(text: str) -> str | None:
    if re.search(r"без\s+логотип|нет\s+логотип", text or "", re.I):
        return "Без логотипа"
    if _SITE_LOGO.search(text or ""):
        return "Учтён"
    return None


def _active_co_design_step(
    *,
    has_project: bool,
    has_preview: bool,
    facts: dict[str, tuple[bool, str | None]],
) -> str | None:
    """Match Vector co-design gate order (bridge._SITE_CO_DESIGN_ORDER)."""
    if not has_project:
        return None

    def done(step_id: str) -> bool:
        return facts.get(step_id, (False, None))[0]

    if not done("company"):
        return "company"
    if not done("goal"):
        return "goal"
    if not done("structure"):
        return "structure"
    if not done("design"):
        return "design"
    if not done("colors"):
        return "colors"
    if not done("logo"):
        return "logo"
    if not done("content"):
        return "content"
    if not has_preview:
        return "draft"
    if not done("revisions") and has_preview:
        return "revisions"
    if not done("launch"):
        return "launch"
    return None


def _has_site_preview(record: ProjectRecord) -> bool:
    for ver in record.versions or []:
        for art in ver.artifacts or []:
            if art.kind == "preview":
                return True
    return False


_UNIVERSAL_PANEL_STEPS: tuple[tuple[str, str], ...] = (
    ("type", "Тип проекта"),
    ("goal", "Цель"),
    ("company", "Компания"),
    ("structure", "Требования"),
    ("draft", "Черновик"),
    ("revisions", "Правки"),
    ("launch", "Готов к передаче"),
)


def _has_project_artifact(record: ProjectRecord) -> bool:
    for ver in record.versions or []:
        if ver.artifacts:
            return True
    return False


def build_universal_journey_state(record: ProjectRecord) -> dict[str, Any] | None:
    """Same panel journey for CRM, automation, chatbot, SEO — not website-only."""
    if record.service_id == SERVICE_WEBSITE:
        return None

    text = accumulated_dialog_text(record)
    company = extract_company_name(text)
    service_label = service_label_ru(record.service_id, fallback="Проект")
    has_goal = len(text) > 24
    has_structure = len(text) > 64 or bool(company)
    has_artifact = _has_project_artifact(record)
    has_project = record.mode == "project"

    facts: dict[str, tuple[bool, str | None]] = {
        "type": (has_project, service_label),
        "goal": (has_goal, "Зафиксирована" if has_goal else None),
        "company": (bool(company), company),
        "structure": (has_structure, "Собраны" if has_structure else None),
        "draft": (has_artifact, "Версия 1" if has_artifact else None),
        "revisions": (has_artifact and len(record.versions or []) > 1, None),
        "launch": (record.lifecycle_phase in ("approval", "choice", "handoff"), None),
    }

    active_id: str | None = None
    if not has_project:
        active_id = None
    elif not facts["company"][0]:
        active_id = "company"
    elif not facts["goal"][0]:
        active_id = "goal"
    elif not facts["structure"][0]:
        active_id = "structure"
    elif not has_artifact:
        active_id = "draft"
    elif not facts["launch"][0] and has_artifact:
        active_id = "revisions" if facts["revisions"][0] else "launch"

    items: list[dict[str, Any]] = []
    for step_id, label in _UNIVERSAL_PANEL_STEPS:
        done, value = facts.get(step_id, (False, None))
        if done:
            status = "done"
        elif step_id == active_id:
            status = "active"
        else:
            status = "pending"
        row: dict[str, Any] = {"id": step_id, "label": label, "status": status}
        if value:
            row["value"] = value
        items.append(row)

    done_count = sum(1 for i in items if i["status"] == "done")
    percent = min(99, int(round((done_count / max(len(items), 1)) * 100)))
    if has_artifact:
        percent = max(percent, 52)

    hint = (record.next_step_hint or "").strip()
    vector_now: list[str] = []
    if hint:
        vector_now.append(f"⏳ {hint}")
    elif active_id:
        active_label = dict(_UNIVERSAL_PANEL_STEPS).get(active_id, active_id)
        vector_now.append(f"⏳ {active_label}")
    else:
        vector_now.append("✓ проект в работе")

    return {
        "items": items,
        "percent": percent,
        "active_step_id": active_id,
        "status_label": f"🟡 {status_label(record)}",
        "vector_now": vector_now,
    }


def build_project_journey_state(record: ProjectRecord) -> dict[str, Any] | None:
    """Single entry — website co-design or universal project journey."""
    if record.service_id == SERVICE_WEBSITE:
        return build_website_journey_state(record)
    return build_universal_journey_state(record)


def build_website_journey_state(record: ProjectRecord) -> dict[str, Any] | None:
    """Canonical journey for the project panel — must match Vector co-design memory."""
    if record.service_id != SERVICE_WEBSITE:
        return None

    text = accumulated_dialog_text(record)
    company = extract_company_name(text)
    country = record.market if record.market and record.market != "Не указан" else infer_market(text)
    has_goal = bool(_SITE_GOAL.search(text))
    has_design = bool(_SITE_STYLE.search(text))
    has_colors = bool(_SITE_COLORS.search(text))
    has_logo = bool(_SITE_LOGO.search(text))
    has_content = bool(_SITE_MATERIALS.search(text))
    has_preview = _has_site_preview(record)
    has_project = record.mode == "project"

    facts: dict[str, tuple[bool, str | None]] = {
        "type": (has_project, "Сайт"),
        "goal": (has_goal, "Заявка / действие" if has_goal else None),
        "company": (bool(company), company),
        "country": (country != "Не указан", country if country != "Не указан" else None),
        "structure": (has_goal and bool(company), None),
        "design": (has_design, _design_value(text)),
        "colors": (has_colors, _colors_value(text)),
        "logo": (has_logo, _logo_value(text)),
        "content": (has_content, "Собраны" if has_content else None),
        "draft": (has_preview, "Версия 1" if has_preview else None),
        "revisions": (
            has_preview and len(record.versions or []) > 1,
            None,
        ),
        "launch": (record.lifecycle_phase in ("approval", "choice", "handoff"), None),
    }

    active_id = _active_co_design_step(
        has_project=has_project,
        has_preview=has_preview,
        facts=facts,
    )

    items: list[dict[str, Any]] = []
    for step_id, label in _PANEL_STEPS:
        done, value = facts.get(step_id, (False, None))
        if done:
            status = "done"
        elif step_id == active_id:
            status = "active"
        else:
            status = "pending"
        row: dict[str, Any] = {"id": step_id, "label": label, "status": status}
        if value:
            row["value"] = value
        items.append(row)

    done_count = sum(1 for i in items if i["status"] == "done")
    percent = min(99, int(round((done_count / max(len(items), 1)) * 100)))
    if has_preview:
        percent = max(percent, 58)

    hint = (record.next_step_hint or "").strip()
    vector_now: list[str] = []
    if hint:
        vector_now.append(f"⏳ {hint}")
    elif active_id:
        active_label = dict(_PANEL_STEPS).get(active_id, active_id)
        vector_now.append(f"⏳ {active_label}")
    else:
        vector_now.append("✓ проект в работе")

    return {
        "items": items,
        "percent": percent,
        "active_step_id": active_id,
        "status_label": f"🟡 {status_label(record)}",
        "vector_now": vector_now,
    }


JOURNEY_STEP_HINTS: dict[str, str] = {
    "goal": "уточняем цель сайта",
    "company": "уточняем компанию",
    "country": "уточняем страну или рынок",
    "structure": "согласуем структуру",
    "design": "выбираем стиль",
    "colors": "согласуем цвета",
    "logo": "жду логотип или решение без него",
    "content": "собираем материалы для первой концепции",
    "draft": "готовим первую концепцию",
    "revisions": "вносим правки",
    "launch": "готовим к запуску",
}


def journey_next_step_hint(record: ProjectRecord) -> str | None:
    journey = build_project_journey_state(record)
    if not journey:
        return None
    active = journey.get("active_step_id")
    if active:
        return JOURNEY_STEP_HINTS.get(str(active))
    return None
