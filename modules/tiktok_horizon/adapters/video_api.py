"""AI Video API adapter — Stage 1 permanently disabled."""

from __future__ import annotations

from typing import Any

from modules.tiktok_horizon.adapters.base import AdapterResult, ExternalAdapter


class VideoGeneratorAdapter(ExternalAdapter):
    provider_id = "video_stub"

    def health(self) -> AdapterResult:
        return AdapterResult(
            ok=True,
            provider=self.provider_id,
            stage1_disabled=True,
            data={"enabled": False},
            meta={"note": "Veo/Runway/Kling/etc. not connected in Stage 1."},
        )

    def generate(self, _prompt: dict[str, Any]) -> AdapterResult:
        return AdapterResult(
            ok=False,
            provider=self.provider_id,
            stage1_disabled=True,
            error="video_generation_disabled_stage1",
        )
