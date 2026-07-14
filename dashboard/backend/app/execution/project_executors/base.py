"""Project executor protocol — Virtus Core operational layer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(frozen=True)
class ProjectRouteContext:
    goal: str
    visitor_id: str
    memory_dir: Path
    service_id: str
    attachment_files: list[dict[str, Any]]
    history: list[dict[str, str]] | None
    ui_locale: str | None = None
    company_memory: Any = None
    expansion_mode: bool = False


class ProjectExecutor(Protocol):
    service_id: str

    def matches(self, service_id: str) -> bool: ...

    def detect_new_request(self, goal: str) -> bool: ...

    def try_route(self, ctx: ProjectRouteContext) -> dict[str, Any] | None: ...

    def preview_open_label(self) -> str: ...

    def workspace_title(self) -> str: ...
