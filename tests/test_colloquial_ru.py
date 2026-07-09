"""Colloquial Russian — Slice 1 natural speech understanding."""

from app.integration.genesis_brain.colloquial_ru import (
    expand_colloquial_ru,
    is_colloquial_register,
)
from app.integration.genesis_brain.user_text_normalizer import normalize_user_text


def test_zdarova_to_privet():
    assert "привет" in normalize_user_text("здарова")


def test_che_kak_variants():
    for phrase in ("че как", "чё как", "чо как"):
        out = normalize_user_text(phrase)
        assert "как дела" in out


def test_slang_tokens():
    cases = {
        "го": "давай",
        "харош": "хорошо",
        "изи": "легко",
        "рил": "правда",
        "кринж": "неловко",
        "вайб": "атмосфера",
        "ща": "сейчас",
        "спс": "спасибо",
        "окей": "ок",
        "лан": "ладно",
    }
    for src, needle in cases.items():
        assert needle in normalize_user_text(src)


def test_combined_greeting_and_task():
    out = normalize_user_text("Здарова, брат, го сделаем сайт")
    assert "привет" in out.lower()
    assert "давай" in out.lower()
    assert "сделаем" in out.lower()
    assert "брат" in out.lower()


def test_typo_program_invisible():
    out = normalize_user_text("сделай мне преграму")
    assert out == "сделай мне программу"
    assert "имели в виду" not in out.lower()


def test_colloquial_register_detection():
    assert is_colloquial_register("здарова брат")
    assert is_colloquial_register("го сайт")
    assert not is_colloquial_register("Подготовь коммерческое предложение")


def test_no_meta_correction_phrase():
    out = normalize_user_text("здарова че как")
    assert "имели в виду" not in out.lower()
