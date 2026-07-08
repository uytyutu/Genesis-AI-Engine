"""Genesis TTS service — cloud provider chain with browser fallback on client."""

from __future__ import annotations

import logging
from typing import Any

from app.integration.genesis_brain.public_brand import BRAND_NAME
from app.integration.genesis_tts.providers import build_tts_chain
from app.integration.genesis_tts.types import TtsResult
from app.integration.genesis_tts.voice_profile import DEFAULT_SPEED, VOICE_BUILD

logger = logging.getLogger(__name__)


class GenesisTtsService:
    """Try cloud TTS providers in priority order."""

    def __init__(self) -> None:
        self._chain = build_tts_chain()

    def provider_status(self) -> list[dict[str, Any]]:
        labels = {
            "openai-tts": f"OpenAI TTS ({BRAND_NAME})",
            "elevenlabs": "ElevenLabs",
            "google-cloud-tts": "Google Cloud TTS",
            "azure-neural": "Azure Neural Voices",
            "browser": "Browser SpeechSynthesis (fallback)",
        }
        out: list[dict[str, Any]] = []
        for p in self._chain:
            out.append(
                {
                    "id": p.provider_id,
                    "label": labels.get(p.provider_id, p.provider_id),
                    "available": p.available(),
                }
            )
        out.append({"id": "browser", "label": labels["browser"], "available": True})
        return out

    def preferred_provider(self) -> str:
        for p in self._chain:
            if p.available():
                return p.provider_id
        return "browser"

    def cloud_available(self) -> bool:
        return any(p.available() for p in self._chain)

    def synthesize(
        self,
        text: str,
        *,
        speed: float = DEFAULT_SPEED,
        locale: str = "ru-RU",
    ) -> TtsResult | None:
        errors: list[str] = []
        for provider in self._chain:
            if not provider.available():
                continue
            try:
                result = provider.synthesize(text, speed=speed, locale=locale)
                logger.info("Genesis TTS: %s (%d bytes)", provider.provider_id, len(result.audio))
                return result
            except Exception as exc:
                errors.append(f"{provider.provider_id}: {type(exc).__name__}")
                logger.warning("Genesis TTS provider failed %s: %s", provider.provider_id, exc)
        if errors:
            logger.info("Genesis TTS chain exhausted: %s", "; ".join(errors))
        return None

    def status_payload(self) -> dict[str, Any]:
        preferred = self.preferred_provider()
        return {
            "voice_build": VOICE_BUILD,
            "cloud_available": self.cloud_available(),
            "preferred_provider": preferred,
            "providers": self.provider_status(),
            "default_speed": DEFAULT_SPEED,
            "genesis_voice": {
                "style": "female_calm_intellectual",
                "openai_voice": "nova",
                "locale": "ru-RU",
            },
        }
