"""User Text Normalizer — invisible typo repair before classification."""

from app.integration.genesis_brain.fuzzy_nlp import normalize_for_intent
from app.integration.genesis_brain.user_text_normalizer import normalize_user_text


def test_pogola_to_pogoda():
    assert normalize_user_text("погола") == "погода"
    assert "погода" in normalize_for_intent("погола")


def test_rashifrovat_typo():
    assert normalize_user_text("рашифровать") == "расшифровать"


def test_thomas_shelby_name():
    assert normalize_user_text("кто такой томас шелби") == "кто такой Томас Шелби"


def test_rest_api_casing():
    assert normalize_user_text("расскажи про rest api") == "расскажи про REST API"


def test_mozhesh_typo():
    assert normalize_user_text("ты можеш помочь") == "ты можешь помочь"


def test_genesis_typo_maps_to_brand():
    assert normalize_user_text("что такое генезес") == "что такое virtus core"
    assert "virtus" in normalize_for_intent("что такое генезис")


def test_ii_modules():
    assert normalize_user_text("работаешь с ии модулями") == "работаешь с ИИ-модулями"


def test_program_and_server_typos():
    assert normalize_user_text("програма на север") == "программа на сервер"


def test_invisible_correction_no_meta_phrase():
    fixed = normalize_user_text("погола в москве")
    assert "имели в виду" not in fixed.lower()
    assert fixed == "погода в москве"


def test_slova_unchanged():
    assert normalize_user_text("словах") == "словах"


def test_preserves_money_amounts():
    assert normalize_user_text("Бюджет около 5000 евро") == "Бюджет около 5000 евро"
    assert normalize_user_text("У меня бюджет 1000 евро") == "У меня бюджет 1000 евро"
    assert normalize_user_text("до 100000 ₽") == "до 100000 ₽"
    assert normalize_user_text("1 000 €") == "1 000 €"


def test_preserves_percent_phone_and_ids():
    assert normalize_user_text("ставка 12.5%") == "ставка 12.5%"
    assert normalize_user_text("+7 (999) 123-45-67") == "+7 (999) 123-45-67"
    assert normalize_user_text("заказ ORD-2024-9912") == "заказ ORD-2024-9912"


def test_collapses_letter_repeats_not_digits():
    assert normalize_user_text("даааа") == "даа"
    assert normalize_user_text("оккк") == "окк"
    assert normalize_user_text("5000") == "5000"
