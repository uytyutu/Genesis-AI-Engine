"""Universal AI Identity — prompt and scrub tests."""

from app.integration.genesis_brain.ai_identity import (
    UNIVERSAL_AI_IDENTITY,
    scrub_identity_violations,
    try_local_identity_reply,
)


def test_identity_block_forbids_prototype_language():
    low = UNIVERSAL_AI_IDENTITY.lower()
    assert "интеллектуальная" in low
    assert "доводить идеи до результата" in UNIVERSAL_AI_IDENTITY
    assert "не программа" in low and "бот" in low


def test_scrub_identity_violations():
    bad = "Я — цифровой собеседник, скорее попытка создать искусственный интеллект."
    out = scrub_identity_violations(bad)
    assert "попытка создать" not in out.lower()


def test_local_identity_varies_by_wording():
    a = try_local_identity_reply("Кто ты?", visitor_id="v1", turn_index=1)
    b = try_local_identity_reply("А ты вообще кто такой?", visitor_id="v1", turn_index=2)
    assert a and b
    assert any(w in a.lower() for w in ("интеллектуальн", "создан", "анализирую"))
    assert a != b


def test_local_identity_not_triggered_for_historical_figure():
    assert try_local_identity_reply("Кто такой Томас Шелби?", visitor_id="v1", turn_index=1) is None
    assert try_local_identity_reply("Кто такой Наполеон?", visitor_id="v1", turn_index=1) is None
