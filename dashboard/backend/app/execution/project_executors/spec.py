"""Executor registration spec — plug-in contract for VOS."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.execution.project_executors.base import ProjectExecutor

_REGISTRY: list["ExecutorSpec"] = []


@dataclass(frozen=True)
class ExecutorSpec:
    """One executor file = one spec. Project Bridge never branches on product name."""

    executor: ProjectExecutor
    service_ids: frozenset[str]
    intent_patterns: tuple[tuple[re.Pattern[str], str], ...] = field(default_factory=tuple)

    def matches_service(self, service_id: str) -> bool:
        return service_id in self.service_ids


def register_spec(spec: ExecutorSpec) -> None:
    _REGISTRY.append(spec)


def all_specs() -> list[ExecutorSpec]:
    return list(_REGISTRY)


def intent_patterns_from_specs() -> tuple[tuple[re.Pattern[str], str], ...]:
    seen: set[str] = set()
    out: list[tuple[re.Pattern[str], str]] = []
    for spec in _REGISTRY:
        for pattern, sid in spec.intent_patterns:
            if sid in seen:
                continue
            out.append((pattern, sid))
            seen.add(sid)
    return tuple(out)
