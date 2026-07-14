"""Universal AI Identity — prompt and scrub tests."""

from app.integration.genesis_brain.ai_identity import (
    ASSISTANT_NAME,
    BRAND_NAME,
    UNIVERSAL_AI_IDENTITY,
    scrub_identity_violations,
    try_local_identity_reply,
)
from app.integration.genesis_brain.public_brand import scrub_public_brand_text
from app.integration.genesis_core_intelligence import vector_identity_who_reply


def test_identity_block_rule_zero_scrub_only():
    low = UNIVERSAL_AI_IDENTITY.lower()
    assert "rule zero" in low
    assert "chatgpt" in low
    assert "цифровой руководитель" not in low
    assert "интеллектуальный помощник" not in low


def test_scrub_public_brand_removes_genesis():
    out = scrub_public_brand_text("Genesis Studio и Genesis AI — это мы.")
    assert "genesis" not in out.lower()
    assert "Virtus" in out


def test_scrub_identity_violations():
    bad = "Я — цифровой собеседник, скорее попытка создать искусственный интеллект."
    out = scrub_identity_violations(bad)
    assert "попытка создать" not in out.lower()


def test_local_identity_who_are_you():
    reply = try_local_identity_reply("Кто ты?", visitor_id="v1", turn_index=1)
    assert reply == vector_identity_who_reply()
    low = reply.lower()
    assert ASSISTANT_NAME.lower() in low
    assert BRAND_NAME.lower() in low
    assert "crm" not in low
    assert "studio" not in low


def test_local_capabilities_delegates_to_canon():
    reply = try_local_identity_reply("Что ты умеешь?", visitor_id="v1", turn_index=1)
    assert reply == vector_identity_who_reply()
    assert "•" not in reply
    assert "crm" not in reply.lower()
    assert "studio" not in reply.lower()


def test_local_identity_natural_wording():
    a = try_local_identity_reply("Кто ты?", visitor_id="v1", turn_index=1)
    b = try_local_identity_reply("Расскажи о себе", visitor_id="v1", turn_index=2)
    assert a and b
    assert a == b == vector_identity_who_reply()


def test_local_identity_genesis_explained_when_asked():
    reply = try_local_identity_reply("Что такое Genesis?", visitor_id="v1", turn_index=1)
    assert reply
    assert "genesis" in reply.lower()
    assert "внутренн" in reply.lower()
    assert ASSISTANT_NAME.lower() in reply.lower()


def test_local_identity_not_triggered_for_historical_figure():
    assert try_local_identity_reply("Кто такой Томас Шелби?", visitor_id="v1", turn_index=1) is None
    assert try_local_identity_reply("Кто такой Наполеон?", visitor_id="v1", turn_index=1) is None
