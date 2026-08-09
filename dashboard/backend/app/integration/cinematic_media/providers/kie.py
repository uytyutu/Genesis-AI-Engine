"""KIE.ai gateway adapter — DISABLED (credentials may exist; no live spend)."""

from __future__ import annotations

import os
from typing import Any

from app.integration.cinematic_media.config import provider_flags
from app.integration.cinematic_media.providers.base import MediaJobRequest, MediaJobResult


class KieMediaProvider:
    """
    KIE.ai documents async image/video models (I2V, T2V, Veo, etc.).
    This adapter never performs HTTP while enabled=false.
    """

    provider_id = "kie"

    def enabled(self) -> bool:
        flags = provider_flags().get("kie") or {}
        return bool(flags.get("enabled"))

    def credentials_configured(self) -> bool:
        flags = provider_flags().get("kie") or {}
        for name in list(flags.get("env_aliases") or []):
            if (os.getenv(name) or "").strip():
                return True
        return False

    def status(self) -> dict[str, Any]:
        flags = provider_flags().get("kie") or {}
        return {
            "provider": self.provider_id,
            "enabled": self.enabled(),
            "credentials_configured": self.credentials_configured(),
            "status": "DISABLED" if not self.enabled() else "ENABLED",
            "live_calls": False,
            "capabilities_documented_publicly": [
                "IMAGE_GENERATION",
                "IMAGE_TO_VIDEO",
                "TEXT_TO_VIDEO",
            ],
            "note": flags.get("note")
            or "Gateway may route to Kling/Veo/Seedance — CEO must enable + budget gate",
        }

    def submit(self, request: MediaJobRequest) -> MediaJobResult:
        return MediaJobResult(
            provider=self.provider_id,
            job_id="",
            estimated_cost_eur=request.estimated_cost_eur,
            status="DISABLED",
            error="kie_provider_disabled",
            network_called=False,
            metadata={"capability": request.capability, "order_id": request.order_id},
        )
