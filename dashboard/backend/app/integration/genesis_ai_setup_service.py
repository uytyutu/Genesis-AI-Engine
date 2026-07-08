"""Owner setup flow — Genesis Setup v2 (AI Workforce, not OpenAI-only)."""

from __future__ import annotations

from app.integration.workforce_setup import WorkforceSetupService


class GenesisAISetupService:
    """Backward-compatible facade for setup routes."""

    def __init__(self) -> None:
        self._workforce = WorkforceSetupService()

    def status(self) -> dict:
        return self._workforce.status()

    def configure(
        self,
        *,
        api_key: str = "",
        model: str | None = None,
        provider: str = "groq",
    ) -> dict:
        return self._workforce.configure(provider=provider, api_key=api_key, model=model)
