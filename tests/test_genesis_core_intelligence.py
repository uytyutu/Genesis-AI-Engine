"""Genesis Core Intelligence v2 — prompt contract."""

from app.integration.genesis_core_intelligence import ROLES, build_core_system_prompt


def test_roles_defined():
    assert "universal" in ROLES
    assert "digital" in ROLES
    assert "platform" in ROLES


def test_prompt_universal_not_questionnaire():
    prompt = build_core_system_prompt([])
    assert "Core Intelligence v2" in prompt
    assert "Никогда не задавай вопрос" in prompt
    assert "хорошо поспал" in prompt.lower() or "поспал" in prompt
    assert "салон" in prompt.lower()
    assert "GENESIS_ACTION" in prompt


def test_prompt_includes_packages():
    prompt = build_core_system_prompt(
        [{"id": "basic", "name": "Basic", "price_eur": 350, "deliverables": ["a"]}]
    )
    assert "Basic" in prompt
    assert "350" in prompt
