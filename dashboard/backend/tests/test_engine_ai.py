from app.config import env_config_file
from app.env_loader import _apply_key_aliases
from app.integration.engine_ai_service import EngineAIService


def test_ai_brain_setup_not_configured():
    status = EngineAIService(use_env=False).setup_status()
    assert status["configured"] is False
    assert status["brain_ready"] is False
    assert status["recommended_provider"] == "groq"
    assert status["primary_config_file"] == env_config_file()


def test_ai_brain_setup_groq_ready_via_constructor():
    status = EngineAIService(
        api_keys={"GENESIS_GROQ_API_KEY": "gsk-test"},
        use_env=False,
    ).setup_status()
    assert status["configured"] is True
    assert status["brain_ready"] is True


def test_classify_niche_heuristic_without_llm():
    result = EngineAIService(use_env=False).classify_niche(
        analysis={"issues": ["Autowerkstatt ohne HTTPS"], "title": "Garage Müller"},
        company="Garage Müller",
        url="https://garage.example",
    )
    assert result["niche"] == "auto_repair"
    assert result["source"] in ("heuristic", "heuristic_fallback")


def test_env_loader_groq_alias(monkeypatch):
    monkeypatch.delenv("GENESIS_GROQ_API_KEY", raising=False)
    monkeypatch.setenv("GROQ_API_KEY", "gsk-alias-test")
    _apply_key_aliases()
    import os

    assert os.getenv("GENESIS_GROQ_API_KEY") == "gsk-alias-test"
