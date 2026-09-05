"""OCR vision provider routing — key must match base URL (no OpenAI 401 with Groq key)."""

from __future__ import annotations

from app.integration.virtus_office import ocr_engine as ocr


def test_vision_candidates_prefer_coherent_groq(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_OFFICE_VISION_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_OFFICE_VISION_BASE_URL", raising=False)
    monkeypatch.delenv("GENESIS_OFFICE_VISION_MODEL", raising=False)
    monkeypatch.setenv("GENESIS_GROQ_API_KEY", "gsk_test_office_ocr")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    cands = ocr._vision_provider_candidates()
    assert cands
    assert cands[0]["provider"] == "groq"
    assert "groq.com" in cands[0]["base"]
    assert "llama-4-scout" in cands[0]["model"]
    assert ocr._vision_api_key().startswith("gsk_")


def test_vision_candidates_openai_and_groq_both(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-openai")
    monkeypatch.setenv("GENESIS_GROQ_API_KEY", "gsk_test_groq")
    monkeypatch.delenv("GENESIS_LLM_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_OFFICE_VISION_API_KEY", raising=False)

    cands = ocr._vision_provider_candidates()
    providers = [c["provider"] for c in cands]
    assert "openai" in providers
    assert "groq" in providers
    openai = next(c for c in cands if c["provider"] == "openai")
    groq = next(c for c in cands if c["provider"] == "groq")
    assert "openai.com" in openai["base"]
    assert "groq.com" in groq["base"]


def test_misplaced_gsk_in_genesis_llm_routed_to_groq(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("GENESIS_GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GENESIS_LLM_API_KEY", "gsk_misplaced_key")
    monkeypatch.delenv("GENESIS_OFFICE_VISION_API_KEY", raising=False)

    cands = ocr._vision_provider_candidates()
    assert any(c["provider"] == "groq" for c in cands)
    assert not any(c["provider"] == "openai" for c in cands)
