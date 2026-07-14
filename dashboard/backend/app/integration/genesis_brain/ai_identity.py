"""
Technical AI identity layer — Virtus Core (brand) · Vector (assistant) · Genesis (internal core).

Defines identity dialogue text only via genesis_core_intelligence.vector_identity_who_reply().
This module: Rule Zero scrub, provider drift, intent routing, language lock — not profession canon.
"""

from __future__ import annotations

import re

from app.integration.genesis_brain.identity_intent import IdentityIntent, detect_identity_intent
from app.integration.genesis_brain.public_brand import (
    ASSISTANT_NAME,
    BRAND_NAME,
    BRAND_SIGNATURE,
    INTERNAL_CORE_NAME,
    PUBLIC_WELCOME,
    scrub_public_brand_text,
)
from app.integration.genesis_core_intelligence import vector_identity_who_reply

# Re-export for callers/tests.
__all__ = [
    "ASSISTANT_NAME",
    "BRAND_NAME",
    "BRAND_SIGNATURE",
    "INTERNAL_CORE_NAME",
    "PUBLIC_WELCOME",
    "UNIVERSAL_AI_IDENTITY",
    "build_vector_llm_anchor",
    "compose_identity_reply",
    "scrub_identity_violations",
    "scrub_language_drift",
    "try_local_identity_reply",
]


def build_vector_llm_anchor(
    *,
    brand_name: str,
    assistant_name: str,
    language_hint: str,
    style_block: str,
    rhythm_block: str,
    product_rules: str,
) -> str:
    """Fast-lane technical anchor — language lock and passthrough blocks; profession lives in core prompt."""
    return (
        f"\n\n[{brand_name} — {assistant_name}]\n"
        f"Не вставляйте случайные слова на других языках (gracias, merci, heute, I'm glad) — "
        f"только язык пользователя.\n"
        f"{language_hint}\n"
        f"{style_block}\n"
        f"{rhythm_block}\n"
        f"{product_rules}"
    )


_FOREIGN_DRIFT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bgracias\b", re.I),
    re.compile(r"\bmerci\b", re.I),
    re.compile(r"\bdanke\s+schön\b", re.I),
    re.compile(r"\bi(?:'m|\s+am)\s+glad\b", re.I),
    re.compile(r"\bthank\s+you\s+so\s+much\b", re.I),
    re.compile(r"\bde\s+nada\b", re.I),
    re.compile(r"\bpor\s+favor\b", re.I),
    re.compile(
        r"\b(?:heute|gerne|vielleicht|natürlich|natuerlich|wunderbar|schön|"
        r"schon|eben|natürlich|guten\s+tag)\b",
        re.I,
    ),
)


_FAST_LANE_ENGLISH_KEEP = frozenset(
    {
        "vector",
        "virtus",
        "core",
        "site",
        "online",
        "pdf",
        "api",
        "crm",
        "saas",
        "seo",
        "url",
        "email",
        "ok",
        "html",
        "python",
        "docker",
        "openai",
        "ollama",
        "gemini",
        "groq",
    }
)

# Underscore glitches: с_clientem, online_операции
_UNDERSCORE_GLITCH = re.compile(
    r"([\u0400-\u04FFa-zA-Z])_+([\u0400-\u04FFa-zA-Z])",
)

# Isolated English words in Russian replies (3+ letters)
_ISOLATED_ENGLISH = re.compile(
    r"\b([A-Za-z]{3,})\b",
)

_LATIN_TO_CYRILLIC = str.maketrans(
    {
        "A": "А",
        "a": "а",
        "B": "В",
        "b": "в",
        "C": "С",
        "c": "с",
        "E": "Е",
        "e": "е",
        "H": "Н",
        "h": "н",
        "K": "К",
        "k": "к",
        "M": "М",
        "m": "м",
        "O": "О",
        "o": "о",
        "P": "Р",
        "p": "р",
        "T": "Т",
        "t": "т",
        "X": "Х",
        "x": "х",
    }
)

_WORD_TOKEN = re.compile(r"[\w-]+", re.UNICODE)


def _normalize_mixed_script(text: str) -> str:
    out = _UNDERSCORE_GLITCH.sub(r"\1 \2", text)

    def fix_word(match: re.Match[str]) -> str:
        word = match.group(0)
        has_cyr = bool(re.search(r"[\u0400-\u04FF]", word))
        has_lat = bool(re.search(r"[A-Za-z]", word))
        if not (has_cyr and has_lat):
            return word
        fixed = word.translate(_LATIN_TO_CYRILLIC)
        if re.search(r"[A-Za-z]", fixed):
            fixed = re.sub(r"[A-Za-z]+", "", fixed)
        return fixed.strip("-") or word

    return _WORD_TOKEN.sub(fix_word, out)


def _strip_isolated_english(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(1)
        if word.lower() in _FAST_LANE_ENGLISH_KEEP:
            return word
        return ""

    return _ISOLATED_ENGLISH.sub(repl, text)


def scrub_language_drift(text: str, *, user_locale: str = "ru") -> str:
    """Drop foreign-language slips when the user expects Russian."""
    out = (text or "").strip()
    if not out or user_locale not in ("ru", "uk"):
        return out
    out = _normalize_mixed_script(out)
    for pat in _FOREIGN_DRIFT_PATTERNS:
        out = pat.sub("", out)
    out = _strip_isolated_english(out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\s+([,.!?])", r"\1", out)
    return out.strip()


UNIVERSAL_AI_IDENTITY = f"""## Rule Zero — scrub reference (не определяет личность)

Никогда не называйте себя ChatGPT, языковой моделью, провайдером, «ИИ-помощником» или чат-ботом.
Никогда не произносите {INTERNAL_CORE_NAME} пользователю — только {ASSISTANT_NAME} и {BRAND_NAME}.
Не упоминайте Director, Workforce, routing, calibration — если пользователь явно не спрашивает архитектуру.
Не исправляйте опечатки вслух («Вы имели в виду…»).
"""

IDENTITY_FORBIDDEN_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"попытк[аи]\s+создать\s+искусственн", re.I),
    re.compile(r"я\s+—?\s*(?:просто\s+)?(?:цифровой\s+)?(?:собеседник|бот|чат-бот)", re.I),
    re.compile(r"я\s+(?:просто\s+)?(?:языковая\s+модель|LLM|llm)", re.I),
    re.compile(r"как\s+(?:большая\s+)?языковая\s+модель", re.I),
    re.compile(r"as\s+an?\s+ai\s+language\s+model", re.I),
    re.compile(r"i(?:'m|\s+am)\s+(?:an?\s+)?(?:ai\s+)?(?:language\s+model|chatbot|bot)", re.I),
    re.compile(r"i(?:'m|\s+am)\s+(?:chatgpt|claude|gemini|gpt|groq)", re.I),
    re.compile(r"я\s+—\s*(?:chatgpt|claude|gemini|gpt|openai|anthropic|groq)", re.I),
    re.compile(r"(?:недоработанн|экспериментальн|прототип)\w*\s+(?:ии|ai|интеллект)", re.I),
    re.compile(r"я\s+эксперимент", re.I),
    re.compile(r"openai|anthropic|google\s+gemini|deepseek|\bgroq\b", re.I),
    re.compile(r"\bopenrouter\b|\bollama\b", re.I),
    re.compile(r"\bworkforce\b|\bdirector\b", re.I),
    re.compile(r"\bgenesis\b", re.I),
    re.compile(r"\bгенезис\b", re.I),
    re.compile(r"вы\s+имели\s+в\s+виду", re.I),
    re.compile(r"did\s+you\s+mean", re.I),
)

# Rule Zero only — internal engine separation; no profession narrative.
_REPLY_ENGINE = (
    f"{INTERNAL_CORE_NAME} — внутреннее ядро {BRAND_NAME}. "
    f"В диалоге отвечает {ASSISTANT_NAME}."
)

_REPLY_ENGINE_IS_YOU = (
    f"Нет. {INTERNAL_CORE_NAME} — внутреннее ядро {BRAND_NAME}. "
    f"В диалоге с Вами — {ASSISTANT_NAME}."
)

_REPLY_WHY_OLD_NAME = (
    f"{INTERNAL_CORE_NAME} — внутреннее имя движка {BRAND_NAME}, не публичный бренд. "
    f"В диалоге — {ASSISTANT_NAME}."
)

_REPLY_VECTOR_VS_ENGINE = (
    f"{ASSISTANT_NAME} — это я, Ваш собеседник. "
    f"{INTERNAL_CORE_NAME} — техническая основа {BRAND_NAME}, не отдельный «голос» в чате."
)

_PROFESSION_KINDS = frozenset(
    {
        "who_are_you",
        "about_self",
        "capabilities",
        "purpose",
        "help",
        "creator",
        "origin",
        "virtus_core",
        "vector",
        "difference",
        "vector_vs_virtus",
        "program",
        "system",
        "speaker",
        "ai_nature",
        "neural",
        "name_full",
    }
)


def _canon_who_reply() -> str:
    return scrub_public_brand_text(vector_identity_who_reply())


def compose_identity_reply(intent: IdentityIntent) -> str:
    """Route identity intent — profession answers delegate to core; genesis answers stay Rule Zero."""
    kind = intent.kind

    if kind == "name":
        return f"Меня зовут {ASSISTANT_NAME}."
    if kind == "why_name":
        return f"Меня назвали {ASSISTANT_NAME}."
    if kind == "human":
        return f"Нет, я не человек. С Вами — {ASSISTANT_NAME}."
    if kind == "genesis":
        return _REPLY_ENGINE
    if kind == "genesis_is_you":
        return _REPLY_ENGINE_IS_YOU
    if kind == "why_genesis":
        return _REPLY_WHY_OLD_NAME
    if kind == "vector_vs_genesis":
        return _REPLY_VECTOR_VS_ENGINE
    if kind in _PROFESSION_KINDS:
        return _canon_who_reply()
    return _canon_who_reply()


def try_local_identity_reply(
    last_user: str,
    *,
    visitor_id: str = "anonymous",
    turn_index: int = 0,
    messages: list[dict[str, str]] | None = None,
) -> str | None:
    """Offline identity replies — intent-based, with conversation continuity."""
    _ = visitor_id, turn_index
    intent = detect_identity_intent(last_user, messages=messages)
    if intent is None:
        return None
    return compose_identity_reply(intent)


def scrub_identity_violations(text: str) -> str:
    """Replace vendor/prototype self-descriptions with neutral professional voice."""
    out = (text or "").strip()
    if not out:
        return out
    for pat in IDENTITY_FORBIDDEN_PATTERNS:
        if pat.search(out):
            out = pat.sub("", out)
    out = re.sub(r"\s{2,}", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out).strip()
    return scrub_public_brand_text(out)
