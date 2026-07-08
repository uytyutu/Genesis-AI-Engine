"""Genesis Public Voice — calm, confident, intellectual female assistant."""

from __future__ import annotations

import os

VOICE_BUILD = "voice-v2"

# OpenAI — primary when LLM key is present
OPENAI_TTS_MODEL = os.getenv("GENESIS_TTS_OPENAI_MODEL", "tts-1-hd").strip()
OPENAI_TTS_VOICE = os.getenv("GENESIS_TTS_OPENAI_VOICE", "nova").strip()  # female, natural

# ElevenLabs — multilingual, high quality
ELEVENLABS_MODEL = os.getenv("GENESIS_TTS_ELEVENLABS_MODEL", "eleven_multilingual_v2").strip()
ELEVENLABS_VOICE_ID = os.getenv(
    "GENESIS_TTS_ELEVENLABS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"
).strip()  # Sarah — works well for RU

# Google Cloud TTS
GOOGLE_TTS_VOICE = os.getenv("GENESIS_TTS_GOOGLE_VOICE", "ru-RU-Wavenet-A").strip()
GOOGLE_TTS_LANGUAGE = os.getenv("GENESIS_TTS_GOOGLE_LANGUAGE", "ru-RU").strip()

# Azure Neural Voices
AZURE_TTS_VOICE = os.getenv("GENESIS_TTS_AZURE_VOICE", "ru-RU-SvetlanaNeural").strip()

DEFAULT_SPEED = 1.1
MIN_SPEED = 0.85
MAX_SPEED = 1.25
MAX_CHARS = 1200
