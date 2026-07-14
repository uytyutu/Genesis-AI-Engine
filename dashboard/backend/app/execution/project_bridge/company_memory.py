"""Company Memory — one digital company, many projects over time (VOS Cycle 18)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.integration.product_line import (
    SERVICE_AI_EMPLOYEE,
    SERVICE_SEO,
    SERVICE_WEBSITE,
    service_label_ru,
)
from app.integration.project_platform.journey_state import extract_company_name

from app.execution.project_bridge.context import (
    accumulated_project_text,
    project_record,
    workspace_has_deliverable_preview,
)


@dataclass
class CompanyMemory:
    company_name: str | None = None
    market: str | None = None
    description: str | None = None
    style: str | None = None
    palette: str | None = None
    audience: str | None = None
    goals: str | None = None
    active_service_id: str | None = None
    services: tuple[str, ...] = ()
    has_deliverable: bool = False

    @property
    def is_established(self) -> bool:
        return bool(self.company_name and self.services)

    def knows_company(self) -> bool:
        return bool(self.company_name)

    def prior_services_excluding(self, service_id: str) -> tuple[str, ...]:
        return tuple(s for s in self.services if s != service_id)


def _company_dir(memory_dir: Path) -> Path:
    path = memory_dir / "company_platform"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _company_path(memory_dir: Path, visitor_id: str) -> Path:
    vid = (visitor_id or "anonymous").strip()[:64]
    return _company_dir(memory_dir) / f"{vid}.json"


def load_company_memory(memory_dir: Path, visitor_id: str) -> CompanyMemory | None:
    path = _company_path(memory_dir, visitor_id)
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return CompanyMemory(
                company_name=data.get("company_name"),
                market=data.get("market"),
                description=data.get("description"),
                style=data.get("style"),
                palette=data.get("palette"),
                audience=data.get("audience"),
                goals=data.get("goals"),
                active_service_id=data.get("active_service_id"),
                services=tuple(data.get("services") or ()),
                has_deliverable=bool(data.get("has_deliverable")),
            )
        except (json.JSONDecodeError, OSError, TypeError):
            pass
    return _hydrate_from_project(memory_dir, visitor_id)


def save_company_memory(memory_dir: Path, visitor_id: str, mem: CompanyMemory) -> None:
    payload = {
        "company_name": mem.company_name,
        "market": mem.market,
        "description": mem.description,
        "style": mem.style,
        "palette": mem.palette,
        "audience": mem.audience,
        "goals": mem.goals,
        "active_service_id": mem.active_service_id,
        "services": list(mem.services),
        "has_deliverable": mem.has_deliverable,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _company_path(memory_dir, visitor_id).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _hydrate_from_project(memory_dir: Path, visitor_id: str) -> CompanyMemory | None:
    ws_id, record = project_record(memory_dir, visitor_id)
    if not record or record.mode != "project":
        return None
    text = accumulated_project_text(memory_dir, visitor_id)
    company = extract_company_name(text)
    if not company and record:
        title = (getattr(record, "title", "") or "").strip()
        if title and title not in ("Мой проект", "Хочу создать сайт для своей компании."):
            company = title
    if not company:
        return None
    services = (str(record.service_id or SERVICE_WEBSITE),)
    has_del = bool(ws_id and workspace_has_deliverable_preview(memory_dir, ws_id))
    mem = CompanyMemory(
        company_name=company,
        market=record.market if record.market and record.market != "Не указан" else None,
        description=(record.description or "")[:500] or None,
        active_service_id=str(record.service_id or SERVICE_WEBSITE),
        services=services,
        has_deliverable=has_del,
    )
    save_company_memory(memory_dir, visitor_id, mem)
    return mem


def sync_company_memory(memory_dir: Path, visitor_id: str) -> CompanyMemory | None:
    existing = load_company_memory(memory_dir, visitor_id) or CompanyMemory()
    ws_id, record = project_record(memory_dir, visitor_id)
    if not record:
        return existing if existing.company_name else None
    text = accumulated_project_text(memory_dir, visitor_id)
    company = extract_company_name(text) or existing.company_name
    if not company:
        return existing if existing.company_name else None
    svc = str(record.service_id or SERVICE_WEBSITE)
    services = tuple(dict.fromkeys((*existing.services, svc)))
    mem = CompanyMemory(
        company_name=company,
        market=record.market if record.market and record.market != "Не указан" else existing.market,
        description=(record.description or existing.description or "")[:500] or None,
        style=existing.style,
        palette=existing.palette,
        audience=existing.audience,
        goals=existing.goals,
        active_service_id=svc,
        services=services,
        has_deliverable=bool(
            ws_id and workspace_has_deliverable_preview(memory_dir, ws_id)
        ),
    )
    save_company_memory(memory_dir, visitor_id, mem)
    return mem


def detect_service_expansion(
    goal: str,
    *,
    memory_dir: Path,
    visitor_id: str,
    new_service_id: str,
) -> bool:
    """True when visitor asks for a new capability on an established company."""
    mem = load_company_memory(memory_dir, visitor_id)
    if not mem or not mem.knows_company():
        return False
    current = mem.active_service_id or (mem.services[-1] if mem.services else None)
    if new_service_id == current and mem.has_deliverable:
        return False
    if new_service_id in mem.services and mem.has_deliverable:
        return True
    if current and new_service_id != current:
        return True
    return False


def apply_service_expansion(
    memory_dir: Path,
    visitor_id: str,
    new_service_id: str,
) -> CompanyMemory | None:
    mem = sync_company_memory(memory_dir, visitor_id)
    if not mem:
        mem = CompanyMemory()
    services = tuple(dict.fromkeys((*mem.services, new_service_id)))
    mem = CompanyMemory(
        company_name=mem.company_name,
        market=mem.market,
        description=mem.description,
        style=mem.style,
        palette=mem.palette,
        audience=mem.audience,
        goals=mem.goals,
        active_service_id=new_service_id,
        services=services,
        has_deliverable=mem.has_deliverable,
    )
    save_company_memory(memory_dir, visitor_id, mem)
    try:
        from app.integration.project_platform.store import ProjectStore

        ws_id, record = project_record(memory_dir, visitor_id)
        if record and ws_id:
            record.service_id = new_service_id  # type: ignore[assignment]
            record.lifecycle_phase = "collaboration"  # type: ignore[assignment]
            record.next_step_hint = f"Развиваем компанию — {service_label_ru(new_service_id)}"
            ProjectStore(memory_dir).save(record)
    except Exception:
        pass
    return mem


def expansion_intro(
    mem: CompanyMemory,
    new_service_id: str,
) -> str:
    """Vector voice — continue the company, not a new purchase."""
    company = mem.company_name or "вашей компании"
    label = service_label_ru(new_service_id, fallback="новый проект").lower()
    prior = mem.prior_services_excluding(new_service_id)

    if new_service_id == SERVICE_SEO and SERVICE_WEBSITE in mem.services:
        return (
            f"Отлично.\n"
            f"Будем оптимизировать уже существующий сайт **{company}**.\n"
            "Данные компании, стиль и структура уже в системе — начнём с SEO-аудита этой версии."
        )

    if new_service_id == SERVICE_AI_EMPLOYEE and prior:
        linked = ", ".join(service_label_ru(s, fallback=s).lower() for s in prior[:3])
        return (
            f"Отлично.\n"
            f"Подключаем AI-сотрудника к **{company}**.\n"
            f"Используем то, что уже есть ({linked}) — не начинаем с нуля."
        )

    if prior:
        linked = ", ".join(service_label_ru(s, fallback=s).lower() for s in prior[:3])
        return (
            f"Отлично.\n"
            f"Тогда добавим {label} к уже существующей цифровой компании **{company}**.\n"
            f"Используем данные из {linked} — не создаём всё заново."
        )

    return (
        f"Отлично.\n"
        f"Продолжим развивать **{company}** — следующий шаг: {label}."
    )
