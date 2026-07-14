"""Universal project lifecycle — same phases for every service."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.product_line import LIFECYCLE_APPROVAL, LIFECYCLE_CHOICE

from app.execution.project_bridge.context import existing_workspace_id, project_record


def project_lifecycle_phase(memory_dir: Path, visitor_id: str) -> str | None:
    _, record = project_record(memory_dir, visitor_id)
    return record.lifecycle_phase if record else None


def mark_project_lifecycle(memory_dir: Path, visitor_id: str, phase: str) -> None:
    ws_id = existing_workspace_id(memory_dir, visitor_id)
    if not ws_id:
        return
    try:
        from app.integration.project_platform.store import ProjectStore
        from app.integration.project_platform.schema import TimelineEvent

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
            record.next_step_hint = "Оформление — фиксируем согласованную версию"
        record.updated_at = datetime.now(timezone.utc).isoformat()
        ProjectStore(memory_dir).save(record)
    except Exception:
        pass


def project_client_approved(memory_dir: Path, visitor_id: str) -> bool:
    phase = project_lifecycle_phase(memory_dir, visitor_id)
    return phase in (LIFECYCLE_APPROVAL, LIFECYCLE_CHOICE, "handoff", "subscription")
