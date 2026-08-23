"""Kling adapter — DISABLED until CEO enables live spend + paid media budget."""

from __future__ import annotations

import os
from typing import Any

from app.integration.cinematic_media.config import provider_flags
from app.integration.cinematic_media.providers.base import MediaJobRequest, MediaJobResult


class KlingMediaProvider:
    provider_id = "kling"

    def enabled(self) -> bool:
        flags = provider_flags().get("kling") or {}
        return bool(flags.get("enabled"))

    def credentials_configured(self) -> bool:
        flags = provider_flags().get("kling") or {}
        aliases = list(flags.get("env_aliases") or [])
        for name in aliases:
            if (os.getenv(name) or "").strip():
                return True
        return False

    def status(self) -> dict[str, Any]:
        return {
            "provider": self.provider_id,
            "enabled": self.enabled(),
            "credentials_configured": self.credentials_configured(),
            "status": "DISABLED" if not self.enabled() else "ENABLED",
            "live_calls": False,
            "note": "No network calls while enabled=false — even if credentials exist",
        }

    def submit(self, request: MediaJobRequest) -> MediaJobResult:
        # Absolute ban: never call network while disabled
        return MediaJobResult(
            provider=self.provider_id,
            job_id="",
            estimated_cost_eur=request.estimated_cost_eur,
            status="DISABLED",
            error="kling_provider_disabled",
            network_called=False,
            metadata={"capability": request.capability, "order_id": request.order_id},
        )
