"""Adapter contracts — providers are replaceable."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AdapterResult:
    ok: bool
    provider: str
    data: Any = None
    error: str | None = None
    stage1_disabled: bool = False
    meta: dict[str, Any] = field(default_factory=dict)


class ExternalAdapter(ABC):
    provider_id: str = "base"

    @abstractmethod
    def health(self) -> AdapterResult:
        raise NotImplementedError
