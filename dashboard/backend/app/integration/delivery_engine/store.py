"""Delivery state persistence — separate from project_platform internals."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class DeliveryEvent:
    type: str
    label: str
    at: str
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DeliveryState:
    visitor_id: str
    stage: str = "conversation"
    service_id: str | None = None
    workspace_id: str | None = None
    purchase_type: str | None = None  # one_time | subscription
    product_phase: str | None = None
    version_count: int = 0
    goal_summary: str = ""
    created_at: str = ""
    updated_at: str = ""
    events: list[DeliveryEvent] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "visitor_id": self.visitor_id,
            "stage": self.stage,
            "service_id": self.service_id,
            "workspace_id": self.workspace_id,
            "purchase_type": self.purchase_type,
            "product_phase": self.product_phase,
            "version_count": self.version_count,
            "goal_summary": self.goal_summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "events": [e.to_dict() for e in self.events],
        }


class DeliveryStore:
    def __init__(self, memory_dir: Path) -> None:
        self._dir = memory_dir / "delivery"
        self._dir.mkdir(parents=True, exist_ok=True)

    def _path(self, visitor_id: str) -> Path:
        safe = visitor_id.replace("/", "_")[:64]
        return self._dir / f"{safe}.json"

    def load(self, visitor_id: str) -> DeliveryState | None:
        path = self._path(visitor_id)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        events = [
            DeliveryEvent(**e) if isinstance(e, dict) else e
            for e in data.get("events") or []
        ]
        return DeliveryState(
            visitor_id=str(data.get("visitor_id") or visitor_id),
            stage=str(data.get("stage") or "conversation"),
            service_id=data.get("service_id"),
            workspace_id=data.get("workspace_id"),
            purchase_type=data.get("purchase_type"),
            product_phase=data.get("product_phase"),
            version_count=int(data.get("version_count") or 0),
            goal_summary=str(data.get("goal_summary") or ""),
            created_at=str(data.get("created_at") or ""),
            updated_at=str(data.get("updated_at") or ""),
            events=events,
        )

    def save(self, state: DeliveryState) -> None:
        state.updated_at = _utc_now()
        if not state.created_at:
            state.created_at = state.updated_at
        self._path(state.visitor_id).write_text(
            json.dumps(state.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def ensure(self, visitor_id: str) -> DeliveryState:
        existing = self.load(visitor_id)
        if existing:
            return existing
        now = _utc_now()
        state = DeliveryState(visitor_id=visitor_id, created_at=now, updated_at=now)
        self.save(state)
        return state
