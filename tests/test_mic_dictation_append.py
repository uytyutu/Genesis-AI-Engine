"""Tests for mic dictation text helper - logic mirrored from micMode.ts."""

from __future__ import annotations


def append_dictation_text(previous: str, segment: str) -> str:
    chunk = segment.strip()
    if not chunk:
        return previous
    base = previous.rstrip()
    if not base:
        return chunk
    last = base[-1]
    if last in ("\n", " "):
        return f"{base}{chunk}"
    if last in ".!?…":
        return f"{base}\n{chunk}"
    return f"{base} {chunk}"


def test_append_first_segment():
    assert append_dictation_text("", "Привет") == "Привет"


def test_append_with_space():
    assert append_dictation_text("Привет", "мир") == "Привет мир"


def test_append_after_sentence_newline():
    out = append_dictation_text("Купить молоко.", "Позвонить маме")
    assert out == "Купить молоко.\nПозвонить маме"
