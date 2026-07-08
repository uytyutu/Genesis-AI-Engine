"""TTS result types."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TtsResult:
    audio: bytes
    provider_id: str
    content_type: str = "audio/mpeg"
    voice_label: str = "Genesis"
