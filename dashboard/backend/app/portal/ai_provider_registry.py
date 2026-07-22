"""AI Platform AP1.1 — AIProviderRegistry."""

from __future__ import annotations

from app.portal.ai_provider import AIProvider, AIProviderError
from app.portal.ai_provider_protocol import AIProviderProtocol
from app.portal.ai_provider_stubs import build_stub_runtime

ENGINE_ID = "ai_provider_registry_v1"


class AIProviderRegistry:
    """Maps provider records to Protocol runtimes; tracks active provider."""

    def __init__(self) -> None:
        self._active_id: str | None = None

    def bind(self, record: AIProvider) -> AIProviderProtocol:
        return build_stub_runtime(record)

    def set_active(self, provider_id: str | None) -> None:
        self._active_id = provider_id

    def active_id(self) -> str | None:
        return self._active_id

    def resolve_active(
        self, records: tuple[AIProvider, ...]
    ) -> AIProviderProtocol | None:
        if self._active_id:
            for row in records:
                if row.provider_id == self._active_id:
                    if row.status != "enabled":
                        raise AIProviderError("active_provider_not_enabled")
                    return self.bind(row)
        enabled = [row for row in records if row.status == "enabled"]
        if not enabled:
            return None
        if len(enabled) == 1:
            return self.bind(enabled[0])
        # Prefer explicit active; otherwise first enabled by type order.
        order = {"openai": 0, "anthropic": 1, "ollama": 2, "custom": 3}
        enabled.sort(key=lambda item: order.get(item.provider_type, 99))
        return self.bind(enabled[0])

    def resolve_by_type(
        self, records: tuple[AIProvider, ...], provider_type: str
    ) -> AIProviderProtocol | None:
        for row in records:
            if row.provider_type == provider_type:
                return self.bind(row)
        return None
