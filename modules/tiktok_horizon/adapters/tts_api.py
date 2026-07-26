"""TTS adapter — Stage 1 disabled (Human Review can still pick a voice preference)."""

from __future__ import annotations

from typing import Any

from modules.tiktok_horizon.adapters.base import AdapterResult, ExternalAdapter


class TtsAdapter(ExternalAdapter):
    provider_id = "tts_stub"

    def health(self) -> AdapterResult:
        return AdapterResult(
            ok=True,
            provider=self.provider_id,
            stage1_disabled=True,
            data={"enabled": False, "voices_available": []},
        )

    def synthesize(self, _text: str, *, voice: str | None = None) -> AdapterResult:
        return AdapterResult(
            ok=False,
            provider=self.provider_id,
            stage1_disabled=True,
            error="tts_disabled_stage1",
            meta={"requested_voice": voice},
        )
