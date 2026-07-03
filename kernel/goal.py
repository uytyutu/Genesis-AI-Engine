from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GoalType(str, Enum):
    """Universal goal types — kernel is not money-only."""

    REVENUE = "revenue"
    LEADS = "leads"
    TRAFFIC = "traffic"
    USERS = "users"
    DOWNLOADS = "downloads"
    SUBSCRIBERS = "subscribers"


@dataclass(frozen=True)
class Goal:
    type: GoalType
    target: float
    unit: str
    horizon_days: int | None = None

    def __str__(self) -> str:
        horizon = f" in {self.horizon_days}d" if self.horizon_days else ""
        return f"{self.type.value}: {self.target} {self.unit}{horizon}"
