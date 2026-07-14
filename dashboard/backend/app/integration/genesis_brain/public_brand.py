"""
Public brand identity — Virtus Core · Vector · by Virtus Core.

Canonical hierarchy for all user-facing surfaces.
Genesis is internal only — never the public assistant name.
"""

from __future__ import annotations

import re

BRAND_NAME = "Virtus Core"
ASSISTANT_NAME = "Vector"
INTERNAL_CORE_NAME = "Genesis"
BRAND_SIGNATURE = "by Virtus Core"
ASSISTANT_TAGLINE = "Digital Company"
STUDIO_NAME = "Virtus Studio"
CHAT_FEATURE = ASSISTANT_NAME

PUBLIC_WELCOME = (
    f"Здравствуйте! Я {ASSISTANT_NAME} — ваш цифровой сотрудник в {BRAND_NAME}.\n\n"
    "Расскажите идею, вопрос по бизнесу или задачу — обсудим спокойно, как в обычном разговоре. "
    "Когда понадобится хранить материалы, предложу оформить это как проект."
)

# Ordered — specific phrases before bare word.
_PUBLIC_BRAND_SCRUB: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"Genesis\s+AI\s+Engine", re.I), BRAND_NAME),
    (re.compile(r"Genesis\s+Company\s+OS", re.I), BRAND_NAME),
    (re.compile(r"Genesis\s+Company", re.I), BRAND_NAME),
    (re.compile(r"Genesis\s+Marketplace", re.I), f"{BRAND_NAME} Marketplace"),
    (re.compile(r"Genesis\s+Factory", re.I), f"Factory · {BRAND_NAME}"),
    (re.compile(r"Genesis\s+Studio", re.I), STUDIO_NAME),
    (re.compile(r"Genesis\s+AI", re.I), ASSISTANT_NAME),
    (re.compile(r"Genesis\s+OS", re.I), BRAND_NAME),
    (re.compile(r"Genesis\s+Mind", re.I), f"{ASSISTANT_NAME} Mind"),
    (re.compile(r"\bGenesis\b", re.I), BRAND_NAME),
    (re.compile(r"\bгенезис\b", re.I), BRAND_NAME),
    (re.compile(r"\bгенезес\b", re.I), BRAND_NAME),
)


def brand_signature_lines(*, include_tagline: bool = False) -> tuple[str, ...]:
    """Premium signature block — Vector / [tagline] / by Virtus Core."""
    if include_tagline:
        return (ASSISTANT_NAME, ASSISTANT_TAGLINE, BRAND_SIGNATURE)
    return (ASSISTANT_NAME, BRAND_SIGNATURE)


def brand_signature_text(*, include_tagline: bool = False, separator: str = "\n") -> str:
    return separator.join(brand_signature_lines(include_tagline=include_tagline))


def scrub_public_brand_text(text: str) -> str:
    """Remove internal codename Genesis from user-visible assistant replies."""
    out = (text or "").strip()
    if not out:
        return out
    for pattern, repl in _PUBLIC_BRAND_SCRUB:
        out = pattern.sub(repl, out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()
