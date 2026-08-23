"""MediaProvider contract — no live network in v1."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass
class MediaJobRequest:
    order_id: str
    capability: str  # IMAGE_GENERATION | IMAGE_TO_VIDEO | TEXT_TO_VIDEO | VIDEO_EDIT
    prompt: str = ""
    estimated_cost_eur: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class MediaJobResult:
    provider: str
    job_id: str
    estimated_cost_eur: float | None
    status: str
    asset_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    error: str | None = None
    network_called: bool = False

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class MediaProvider(Protocol):
    provider_id: str

    def enabled(self) -> bool: ...

    def credentials_configured(self) -> bool: ...

    def submit(self, request: MediaJobRequest) -> MediaJobResult: ...
