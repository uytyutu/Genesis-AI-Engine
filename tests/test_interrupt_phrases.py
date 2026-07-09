"""Mirror interrupt phrase rules from dashboard/frontend/app/lib/interruptPhrases.ts."""

from __future__ import annotations

import re

INTERRUPT_EXACT_RE = re.compile(
    r"^(стоп|остановись|подожди|подождите|не надо|хватит|стой|stop|wait|нет|тише|замолчи)[.!?,]*$",
    re.IGNORECASE,
)
INTERRUPT_PREFIX_RE = re.compile(
    r"^(стоп|остановись|подожди|не надо|хватит|стой|замолчи)\b",
    re.IGNORECASE,
)


def is_interrupt_phrase(text: str) -> bool:
    t = text.strip()
    if not t:
        return False
    if INTERRUPT_EXACT_RE.match(t):
        return True
    return bool(INTERRUPT_PREFIX_RE.match(t)) and len(t) < 48


def test_interrupt_phrases_recognized():
    for phrase in ("стоп", "Стоп!", "остановись", "хватит", "замолчи", "stop"):
        assert is_interrupt_phrase(phrase), phrase


def test_interrupt_ignored_when_not_speaking_context_is_caller():
    assert not is_interrupt_phrase("")
    assert not is_interrupt_phrase("   ")
    assert not is_interrupt_phrase("расскажи про стоп-кран на кухне")


def test_long_phrase_with_prefix_not_interrupt():
    assert not is_interrupt_phrase("стоп " + "x" * 50)
