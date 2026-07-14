"""
Language Constitution — post-generation speech quality for Vector.

NOT personality · NOT behavior · NOT Project Execution Journey.
Runs after draft generation; guarantees one coherent language per reply.

Rules (canonical):
1. Response language follows user messages (not browser/system locale).
2. One primary language per answer — no random foreign slips.
3. International names/tech (Vector, Virtus Core, HTML, Python…) are allowed.
4. Never correct user typos publicly.
5. Translation requests are exempt — multilingual output allowed.
6. Multilingual project work is not a violation.
7. Post-processing only — never defines who Vector is or how to behave.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.ai_identity import scrub_language_drift
from app.integration.locale_service import effective_chat_locale

__all__ = [
    "apply_language_constitution",
    "is_translation_request",
    "resolve_response_locale",
]

_TRANSLATION_REQUEST = re.compile(
    r"(?:перевед|перевод|translate|übersetz|tradui|traduc|traduire|"
    r"на\s+(?:русск|английск|немецк|украинск)|"
    r"into\s+(?:english|russian|german)|"
    r"auf\s+deutsch|in\s+english)",
    re.I,
)

_LANGUAGE_SWITCH = re.compile(
    r"(?:отвечай|пиши|говори|switch|reply|answer|write)\s+"
    r"(?:на|in|auf)\s+"
    r"(?:русск|английск|немецк|украинск|english|russian|german|deutsch|français)",
    re.I,
)


def resolve_response_locale(
    *,
    user_message: str,
    ui_locale: str | None = None,
) -> str:
    """Primary language for this turn — user text wins over UI locale."""
    return effective_chat_locale(ui_locale, user_message or "")


def is_translation_request(text: str) -> bool:
    """Rule 5 — translation is a separate task; scrub must not flatten it."""
    sample = (text or "").strip()
    if not sample:
        return False
    return bool(_TRANSLATION_REQUEST.search(sample))


def user_requested_language_switch(text: str) -> bool:
    """Rule 1 — explicit user request to change reply language."""
    return bool(_LANGUAGE_SWITCH.search(text or ""))


def apply_language_constitution(
    text: str,
    *,
    user_message: str,
    ui_locale: str | None = None,
) -> str:
    """
    Final language integrity pass — call from personality.finalize only.
    Skips scrub on translation turns (Rule 5).
    """
    out = (text or "").strip()
    if not out:
        return out
    if is_translation_request(user_message):
        return out
    locale = resolve_response_locale(user_message=user_message, ui_locale=ui_locale)
    return scrub_language_drift(out, user_locale=locale)
