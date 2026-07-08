"""Cloud TTS providers — OpenAI, ElevenLabs, Google, Azure."""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from typing import Any
from xml.sax.saxutils import escape

import httpx

from app.integration.genesis_tts.types import TtsResult
from app.integration.genesis_tts.voice_profile import (
    AZURE_TTS_VOICE,
    ELEVENLABS_MODEL,
    ELEVENLABS_VOICE_ID,
    GOOGLE_TTS_LANGUAGE,
    GOOGLE_TTS_VOICE,
    MAX_CHARS,
    OPENAI_TTS_MODEL,
    OPENAI_TTS_VOICE,
)

logger = logging.getLogger(__name__)


def _clamp_speed(speed: float) -> float:
    return max(0.85, min(1.25, speed))


def _clean_text(text: str) -> str:
    out = re.sub(r"\*\*", "", text or "")
    out = re.sub(r"#{1,6}\s", "", out)
    out = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out[:MAX_CHARS]


class TtsProvider(ABC):
    provider_id: str

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def synthesize(self, text: str, *, speed: float = 1.1, locale: str = "ru-RU") -> TtsResult: ...


class OpenAITtsProvider(TtsProvider):
    provider_id = "openai-tts"

    def __init__(self) -> None:
        self._api_key = (
            os.getenv("GENESIS_TTS_OPENAI_API_KEY", "").strip()
            or os.getenv("GENESIS_LLM_API_KEY", "").strip()
            or os.getenv("OPENAI_API_KEY", "").strip()
        )
        self._base_url = os.getenv(
            "GENESIS_LLM_BASE_URL", "https://api.openai.com/v1"
        ).rstrip("/")
        self._timeout = float(os.getenv("GENESIS_TTS_TIMEOUT_SEC", "30"))

    def available(self) -> bool:
        return bool(self._api_key)

    def synthesize(self, text: str, *, speed: float = 1.1, locale: str = "ru-RU") -> TtsResult:
        if not self._api_key:
            raise RuntimeError("OpenAI TTS not configured")
        payload = {
            "model": OPENAI_TTS_MODEL,
            "input": _clean_text(text),
            "voice": OPENAI_TTS_VOICE,
            "speed": _clamp_speed(speed),
            "response_format": "mp3",
        }
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self._base_url}/audio/speech"
        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            audio = res.content
        return TtsResult(
            audio=audio,
            provider_id=self.provider_id,
            content_type="audio/mpeg",
            voice_label=f"Genesis ({OPENAI_TTS_VOICE})",
        )


class ElevenLabsTtsProvider(TtsProvider):
    provider_id = "elevenlabs"

    def __init__(self) -> None:
        self._api_key = os.getenv("GENESIS_TTS_ELEVENLABS_API_KEY", "").strip() or os.getenv(
            "ELEVENLABS_API_KEY", ""
        ).strip()
        self._voice_id = ELEVENLABS_VOICE_ID
        self._timeout = float(os.getenv("GENESIS_TTS_TIMEOUT_SEC", "30"))

    def available(self) -> bool:
        return bool(self._api_key and self._voice_id)

    def synthesize(self, text: str, *, speed: float = 1.1, locale: str = "ru-RU") -> TtsResult:
        if not self._api_key:
            raise RuntimeError("ElevenLabs not configured")
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{self._voice_id}"
        # ElevenLabs speed via voice_settings — stability + style
        payload: dict[str, Any] = {
            "text": _clean_text(text),
            "model_id": ELEVENLABS_MODEL,
            "voice_settings": {
                "stability": 0.55,
                "similarity_boost": 0.78,
                "style": 0.15,
                "use_speaker_boost": True,
            },
        }
        headers = {
            "xi-api-key": self._api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            audio = res.content
        return TtsResult(
            audio=audio,
            provider_id=self.provider_id,
            content_type="audio/mpeg",
            voice_label="Genesis (ElevenLabs)",
        )


class GoogleTtsProvider(TtsProvider):
    provider_id = "google-cloud-tts"

    def __init__(self) -> None:
        self._api_key = os.getenv("GENESIS_GOOGLE_TTS_API_KEY", "").strip()
        self._timeout = float(os.getenv("GENESIS_TTS_TIMEOUT_SEC", "30"))

    def available(self) -> bool:
        return bool(self._api_key)

    def synthesize(self, text: str, *, speed: float = 1.1, locale: str = "ru-RU") -> TtsResult:
        if not self._api_key:
            raise RuntimeError("Google TTS not configured")
        lang = locale if locale else GOOGLE_TTS_LANGUAGE
        payload = {
            "input": {"text": _clean_text(text)},
            "voice": {
                "languageCode": lang,
                "name": GOOGLE_TTS_VOICE,
                "ssmlGender": "FEMALE",
            },
            "audioConfig": {
                "audioEncoding": "MP3",
                "speakingRate": _clamp_speed(speed),
                "pitch": 0.0,
                "volumeGainDb": 0.0,
            },
        }
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self._api_key}"
        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, json=payload)
            res.raise_for_status()
            data = res.json()
        import base64

        audio = base64.b64decode(data["audioContent"])
        return TtsResult(
            audio=audio,
            provider_id=self.provider_id,
            content_type="audio/mpeg",
            voice_label=f"Genesis ({GOOGLE_TTS_VOICE})",
        )


class AzureTtsProvider(TtsProvider):
    provider_id = "azure-neural"

    def __init__(self) -> None:
        self._key = os.getenv("GENESIS_AZURE_SPEECH_KEY", "").strip() or os.getenv(
            "AZURE_SPEECH_KEY", ""
        ).strip()
        self._region = os.getenv("GENESIS_AZURE_SPEECH_REGION", "").strip() or os.getenv(
            "AZURE_SPEECH_REGION", ""
        ).strip()
        self._voice = AZURE_TTS_VOICE
        self._timeout = float(os.getenv("GENESIS_TTS_TIMEOUT_SEC", "30"))

    def available(self) -> bool:
        return bool(self._key and self._region)

    def synthesize(self, text: str, *, speed: float = 1.1, locale: str = "ru-RU") -> TtsResult:
        if not self._key or not self._region:
            raise RuntimeError("Azure Speech not configured")
        rate = f"{_clamp_speed(speed):.2f}"
        clean = escape(_clean_text(text))
        ssml = (
            f'<speak version="1.0" xml:lang="{locale or "ru-RU"}">'
            f'<voice name="{self._voice}">'
            f'<prosody rate="{rate}">{clean}</prosody>'
            f"</voice></speak>"
        )
        url = f"https://{self._region}.tts.speech.microsoft.com/cognitiveservices/v1"
        headers = {
            "Ocp-Apim-Subscription-Key": self._key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
        }
        with httpx.Client(timeout=self._timeout) as client:
            res = client.post(url, headers=headers, content=ssml.encode("utf-8"))
            res.raise_for_status()
            audio = res.content
        return TtsResult(
            audio=audio,
            provider_id=self.provider_id,
            content_type="audio/mpeg",
            voice_label=f"Genesis ({self._voice})",
        )


def build_tts_chain() -> list[TtsProvider]:
    return [
        OpenAITtsProvider(),
        ElevenLabsTtsProvider(),
        GoogleTtsProvider(),
        AzureTtsProvider(),
    ]
