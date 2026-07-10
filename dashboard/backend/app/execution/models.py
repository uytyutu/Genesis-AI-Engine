"""Execution Layer — core models (Phase 1)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Literal

PermissionKind = Literal[
    "read",
    "write",
    "network",
    "filesystem",
    "terminal",
    "deployment",
    "external_api",
]

CapabilityAvailability = Literal["available", "unavailable", "planned"]

ExecutionStatus = Literal[
    "pending",
    "running",
    "completed",
    "failed",
    "blocked",
    "rolled_back",
    "cancelled",
]


class RollbackStrategy(str, Enum):
    NONE = "none"
    REVERT_LAST_STEP = "revert_last_step"
    REVERT_ALL = "revert_all"


@dataclass(frozen=True)
class PermissionGrant:
    """Granted permissions for one execution run."""

    kinds: frozenset[str]
    workspace_id: str
    actor: str = "system"

    def allows(self, required: frozenset[str]) -> bool:
        return required.issubset(self.kinds)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kinds": sorted(self.kinds),
            "workspace_id": self.workspace_id,
            "actor": self.actor,
        }


@dataclass(frozen=True)
class VerificationRule:
    """Post-step verification — Brain must not assume success."""

    id: str
    description: str
    required_output_keys: tuple[str, ...] = ()
    expect_status: ExecutionStatus | None = "completed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ExecutionStep:
    id: str
    capability_id: str
    title: str
    inputs: dict[str, Any]
    depends_on: tuple[str, ...] = ()
    parallel_group: str | None = None
    verification: VerificationRule | None = None
    max_retries: int = 1
    timeout_sec: float | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        if self.verification:
            d["verification"] = self.verification.to_dict()
        return d


@dataclass(frozen=True)
class ExecutionPlan:
    goal: str
    steps: tuple[ExecutionStep, ...]
    required_permissions: frozenset[str] = field(default_factory=frozenset)
    rollback: RollbackStrategy = RollbackStrategy.REVERT_LAST_STEP
    workspace_id: str = ""
    plan_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "workspace_id": self.workspace_id,
            "rollback": self.rollback.value,
            "required_permissions": sorted(self.required_permissions),
            "steps": [s.to_dict() for s in self.steps],
        }


@dataclass
class StepExecutionRecord:
    step_id: str
    capability_id: str
    status: ExecutionStatus
    started_at: str
    finished_at: str | None = None
    duration_ms: float | None = None
    inputs: dict[str, Any] = field(default_factory=dict)
    outputs: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    retry_count: int = 0
    verified: bool = False
    verification_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExecutionResult:
    plan_id: str
    goal: str
    workspace_id: str
    status: ExecutionStatus
    steps: list[StepExecutionRecord] = field(default_factory=list)
    started_at: str = ""
    finished_at: str | None = None
    duration_ms: float | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "goal": self.goal,
            "workspace_id": self.workspace_id,
            "status": self.status,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "steps": [s.to_dict() for s in self.steps],
        }
