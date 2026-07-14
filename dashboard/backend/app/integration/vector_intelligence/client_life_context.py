"""Client life context — who they are, where they stopped, what comes next."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.customer_identity.schema import CustomerCard, WelcomeSession
from app.integration.customer_identity.store import CustomerIdentityStore
from app.integration.genesis_brain.layers.memory import GenesisMemoryLayer
from app.integration.project_platform.service import ProjectPlatformService

_SERVICE_JOURNEY: dict[str, str] = {
    "website": "crm",
    "crm": "automation",
    "automation": "analytics",
    "business_plan": "website",
    "presentation": "website",
    "document_analysis": "business_plan",
}

_NEXT_STEP_LABELS: dict[str, str] = {
    "crm": "подключить CRM и учёт клиентов",
    "automation": "автоматизировать рутину и заказы",
    "analytics": "настроить аналитику и отчёты",
    "website": "подготовить сайт или лендинг",
    "business_plan": "оформить бизнес-план в структурированный документ",
}


def _parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _days_between(older: datetime | None, newer: datetime | None) -> float | None:
    if not older or not newer:
        return None
    return (newer - older).total_seconds() / 86400.0


def _find_card_by_visitor(store: CustomerIdentityStore, visitor_id: str) -> CustomerCard | None:
    root = store._cards  # noqa: SLF001 — same package, index scan only
    for path in root.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("platform_visitor_id") == visitor_id:
            from app.integration.customer_identity.schema import MarketingConsent

            marketing = data.pop("marketing", {})
            card = CustomerCard(**data)
            card.marketing = MarketingConsent(**marketing) if marketing else MarketingConsent()
            return card
    return None


def _infer_business_label(
    memory: dict[str, Any],
    welcome: WelcomeSession | None,
    project: dict[str, Any] | None,
) -> str | None:
    if welcome and welcome.wizard_answers.get("occupation"):
        return welcome.wizard_answers["occupation"].strip()
    title = (project or {}).get("identity", {}).get("title") or (project or {}).get("title")
    if title and title not in ("Мой проект", "Моя компания"):
        return str(title)
    for fact in reversed(memory.get("facts") or []):
        text = fact.get("text") if isinstance(fact, dict) else str(fact)
        low = text.lower()
        if "кофейн" in low or "кафе" in low:
            return "кофейня"
        if "салон" in low:
            return "салон красоты"
        if "магазин" in low:
            return "магазин"
    return None


def _infer_market(
    memory: dict[str, Any],
    card: CustomerCard | None,
    project: dict[str, Any] | None,
) -> str | None:
    if card and card.country:
        return card.country
    market = (project or {}).get("identity", {}).get("market") or (project or {}).get("market")
    if market and market != "Не указан":
        return str(market)
    for fact in reversed(memory.get("facts") or []):
        text = fact.get("text") if isinstance(fact, dict) else str(fact)
        if "герман" in text.lower() or "berlin" in text.lower():
            return "Германия"
    return None


@dataclass(frozen=True)
class ClientLifeContext:
    visitor_id: str
    name: str | None = None
    business_label: str | None = None
    market: str | None = None
    days_since_last_seen: float | None = None
    has_project: bool = False
    project_title: str | None = None
    project_mode: str = "conversation"
    stage_label: str | None = None
    progress_percent: int = 0
    last_activity_summary: str | None = None
    last_stop_summary: str | None = None
    next_step_hint: str | None = None
    next_logical_service: str | None = None
    next_logical_label: str | None = None
    active_service_id: str | None = None
    version_count: int = 0
    journey_services: tuple[str, ...] = ()
    interests: tuple[str, ...] = ()
    visit_count: int = 0
    is_return_after_days: bool = False
    is_inactive_week: bool = False
    first_version_ready: bool = False
    active_path_summary: str | None = None

    def to_prompt_block(self) -> str:
        lines = [
            "## КОНТЕКСТ ЖИЗНИ КЛИЕНТА (Intelligence Layer)",
            "Vector — цифровой сотрудник. Один человек, один диалог. Проект — рабочий стол, не отдельный режим.",
        ]
        if self.name:
            lines.append(f"- Имя: {self.name}")
        if self.business_label:
            lines.append(f"- Бизнес / занятость: {self.business_label}")
        if self.market:
            lines.append(f"- Рынок / страна: {self.market}")
        if self.journey_services:
            lines.append(f"- Путь развития: {' → '.join(self.journey_services)}")
        if self.has_project and self.project_title:
            lines.append(f"- Активный проект: {self.project_title}")
            if self.stage_label:
                lines.append(f"- Этап: {self.stage_label} ({self.progress_percent}% готовности)")
            if self.last_stop_summary:
                lines.append(f"- Где остановились: {self.last_stop_summary}")
            if self.last_activity_summary:
                lines.append(f"- Последняя активность: {self.last_activity_summary}")
        if self.next_step_hint:
            lines.append(f"- Следующий шаг по проекту: {self.next_step_hint}")
        if self.next_logical_label:
            lines.append(f"- Логичное продолжение пути: {self.next_logical_label}")
        if self.days_since_last_seen is not None and self.days_since_last_seen >= 1:
            lines.append(f"- Не виделись: {int(self.days_since_last_seen)} дн.")
        return "\n".join(lines)


def build_client_life_context(
    visitor_id: str,
    *,
    memory_dir: Path,
    now: datetime | None = None,
) -> ClientLifeContext:
    vid = (visitor_id or "anonymous").strip()[:64]
    now = now or datetime.now(timezone.utc)

    mem_layer = GenesisMemoryLayer(memory_dir)
    memory = mem_layer.load(vid)

    last_seen = _parse_iso(memory.get("last_seen_at")) or _parse_iso(memory.get("updated_at"))
    days_away = _days_between(last_seen, now)

    store = CustomerIdentityStore(memory_dir)
    card = _find_card_by_visitor(store, vid)
    welcome: WelcomeSession | None = None
    if card:
        welcome = store.load_welcome(card.customer_id)

    platform = ProjectPlatformService(memory_dir).get_for_visitor(vid)
    project = platform.get("project") if platform.get("has_project") else None

    business = _infer_business_label(memory, welcome, project)
    market = _infer_market(memory, card, project)

    journey: list[str] = []
    if project and project.get("identity", {}).get("type_label"):
        journey.append(str(project["identity"]["type_label"]))
    if card:
        for interest in card.interests[:5]:
            if interest not in journey:
                journey.append(interest)
    if welcome:
        goal = welcome.wizard_answers.get("goal", "").strip()
        if goal and goal not in journey:
            journey.append(goal)

    active_service = None
    if project:
        active_service = project.get("identity", {}).get("type_id") or project.get("service_id")

    next_logical = _SERVICE_JOURNEY.get(active_service or "", None)
    next_logical_label = _NEXT_STEP_LABELS.get(next_logical or "", None)

    progress = (project or {}).get("progress") or {}
    activity = (project or {}).get("activity") or {}
    identity = (project or {}).get("identity") or {}
    versions = (project or {}).get("versions") or []

    stage = progress.get("current_stage_label") or identity.get("status")
    last_stop = stage or platform.get("vector_hint") or (project or {}).get("next_step_hint")

    version_count = len(versions)
    first_ready = version_count >= 1 and int(progress.get("percent") or 0) < 85

    from app.integration.vector_intelligence.person_memory.service import PersonMemoryService

    path_summary = PersonMemoryService(memory_dir).active_path_summary(vid)

    return ClientLifeContext(
        visitor_id=vid,
        name=memory.get("name") or (card.name if card else None),
        business_label=business,
        market=market,
        days_since_last_seen=days_away,
        has_project=bool(platform.get("has_project")),
        project_title=identity.get("title") or (project or {}).get("title"),
        project_mode=str(platform.get("mode") or "conversation"),
        stage_label=stage,
        progress_percent=int(progress.get("percent") or 0),
        last_activity_summary=activity.get("summary"),
        last_stop_summary=last_stop,
        next_step_hint=(project or {}).get("next_step_hint") or platform.get("vector_hint"),
        next_logical_service=next_logical,
        next_logical_label=next_logical_label,
        active_service_id=active_service,
        version_count=version_count,
        journey_services=tuple(journey[:6]),
        interests=tuple(card.interests[:6]) if card else (),
        visit_count=int(memory.get("visit_count") or 0),
        is_return_after_days=bool(days_away is not None and days_away >= 2),
        is_inactive_week=bool(days_away is not None and days_away >= 7),
        first_version_ready=first_ready,
        active_path_summary=path_summary,
    )
