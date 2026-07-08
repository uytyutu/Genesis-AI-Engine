"""TTS result types."""

from __future__ import annotations

from dataclasses import dataclass

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME


@dataclass(frozen=True)
class TtsResult:
    audio: bytes
    provider_id: str
    content_type: str = "audio/mpeg"
    voice_label: str = ASSISTANT_NAME
