"""Genesis TTS service tests."""

from app.integration.genesis_tts import GenesisTtsService, VOICE_BUILD


def test_tts_status_includes_browser_fallback():
    svc = GenesisTtsService()
    st = svc.status_payload()
    assert st["voice_build"] == VOICE_BUILD
    ids = [p["id"] for p in st["providers"]]
    assert "browser" in ids
    assert ids.index("openai-tts") < ids.index("browser")


def test_tts_synthesize_without_keys_returns_none():
    svc = GenesisTtsService()
    if svc.cloud_available():
        return
    assert svc.synthesize("Привет, это Genesis.") is None
