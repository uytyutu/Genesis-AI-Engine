"""Production release policy — Normal Launch vs Development Update (Steam model)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from launcher.deps import (
    frontend_build_integrity,
    frontend_build_ready,
    frontend_build_stale,
)
from launcher.launch_mode import LAUNCH_MODE_DEVELOPMENT, LAUNCH_MODE_OWNER, normalize_launch_mode

BuildStatus = Literal["ready", "stale", "missing", "corrupt"]
BuildPolicy = Literal["launch_stable", "rebuild_now"]

STATUS_READY = "ready"
STATUS_STALE = "stale"
STATUS_MISSING = "missing"
STATUS_CORRUPT = "corrupt"

POLICY_LAUNCH_STABLE = "launch_stable"
POLICY_REBUILD_NOW = "rebuild_now"


@dataclass(frozen=True)
class ProductionBuildState:
    status: BuildStatus
    can_launch_without_rebuild: bool
    detail: str


def assess_production_build(root=None) -> ProductionBuildState:
    """Classify production state for CEO launch — stale ≠ unusable."""
    if not frontend_build_ready(root):
        return ProductionBuildState(
            status=STATUS_MISSING,
            can_launch_without_rebuild=False,
            detail="стабильный релиз недоступен — production отсутствует",
        )
    if not frontend_build_integrity(root):
        return ProductionBuildState(
            status=STATUS_CORRUPT,
            can_launch_without_rebuild=False,
            detail="стабильный релиз повреждён — production неполный",
        )
    if frontend_build_stale(root):
        return ProductionBuildState(
            status=STATUS_STALE,
            can_launch_without_rebuild=True,
            detail="исходники изменены — активный релиз не обновлён",
        )
    return ProductionBuildState(
        status=STATUS_READY,
        can_launch_without_rebuild=True,
        detail="production соответствует активному релизу",
    )


def needs_recovery_mode(launch_mode: str | None, state: ProductionBuildState) -> bool:
    """Recovery only when CEO cannot open the last Stable Release."""
    if state.status not in (STATUS_MISSING, STATUS_CORRUPT):
        return False
    return normalize_launch_mode(launch_mode) == LAUNCH_MODE_OWNER


def default_policy_for_launch(launch_mode: str | None, state: ProductionBuildState) -> BuildPolicy:
    """Development mode may rebuild; CEO never auto-rebuilds on stale alone."""
    mode = normalize_launch_mode(launch_mode)
    if state.status in (STATUS_MISSING, STATUS_CORRUPT):
        return POLICY_REBUILD_NOW
    if state.status == STATUS_STALE and mode == LAUNCH_MODE_DEVELOPMENT:
        return POLICY_REBUILD_NOW
    return POLICY_LAUNCH_STABLE


def needs_stale_choice(launch_mode: str | None, state: ProductionBuildState) -> bool:
    """CEO chooses when sources changed but the last Stable Release still runs."""
    if state.status != STATUS_STALE:
        return False
    return normalize_launch_mode(launch_mode) == LAUNCH_MODE_OWNER

