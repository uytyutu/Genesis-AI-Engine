"""Swarm types — worker flow and labeling payloads."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class WorkerFlowStep(str, Enum):
    TRIGGER = "trigger"
    COMPUTE = "compute"
    EXECUTION = "execution"
    RESULT = "result"


@dataclass
class LabelTask:
    """Raw item waiting for AI labeling."""

    id: str
    source_id: str
    raw_text: str
    company: str = ""
    url: str = ""
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class LabelResult:
    """Labeled output ready for export / micro-payment."""

    task_id: str
    ok: bool
    labels: dict[str, Any]
    confidence: float
    pay_eur: float
    llm_cost_eur: float = 0.0
    detail: str = ""
    flow: list[str] = field(default_factory=list)
    duration_ms: float = 0.0
    cached: bool = False
    router_task: str = ""


@dataclass
class BatchResult:
    tasks_done: int
    earned_eur: float
    llm_cost_eur: float
    results: list[LabelResult]
    message: str
