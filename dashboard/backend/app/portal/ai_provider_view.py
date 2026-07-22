"""AI Platform AP1.1 — AI Provider View."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.portal.ai_provider import AIProvider

ENGINE_ID = "ai_provider_view_v1"


@dataclass(frozen=True)
class AIProviderView:
    provider_id: str
    provider_type: str
    display_name: str
    status: str
    configuration: dict[str, str]
    is_active: bool
    created_at: str
    updated_at: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "provider_type": self.provider_type,
            "display_name": self.display_name,
            "status": self.status,
            "configuration": dict(self.configuration),
            "is_active": self.is_active,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def build_provider_view(
    row: AIProvider, *, is_active: bool = False
) -> AIProviderView:
    return AIProviderView(
        provider_id=row.provider_id,
        provider_type=row.provider_type,
        display_name=row.display_name,
        status=row.status,
        configuration=dict(row.configuration),
        is_active=is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )
