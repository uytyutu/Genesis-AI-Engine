"""
Conversation Type — what kind of talk this is (before business/product routing).

Executive Brain uses this to forbid unsolicited Factory/Studio/site pitches.
"""

from __future__ import annotations

import re
from typing import Literal

from app.integration.genesis_brain.fuzzy_nlp import contains_any, normalize_for_intent
from app.integration.genesis_brain.layers.conversation_state import ConversationState

ConversationKind = Literal[
    "casual_conversation",
    "emotional_support",
    "philosophy",
    "science",
    "education",
    "programming",
    "business_consulting",
    "product_creation",
    "general_question",
    "personal_reflection",
    "meta_correction",
    "humor",
    "creative",
]

_BUSINESS_KINDS = frozenset({"business_consulting", "product_creation"})
_PRODUCT_KINDS = frozenset({"product_creation"})

_PERSONAL = re.compile(
    r"как\s+думаешь|как\s+считаешь|как\s+ты\s+думаешь|"
    r"получится\s+ли|смогу\s+ли|"
    r"я\s+стану|стану\s+ли|"
    r"у\s+меня\s+получ|"
    r"думаешь.*(?:успеш|получ|выйд|справ)",
    re.I,
)
_MILLION = re.compile(r"миллионер|миллион|стать\s+богат|разбогат|богатств", re.I)
_PHILOSOPHY = re.compile(
    r"смысл\s+жизн|зачем\s+жить|существован|судьб|"
    r"кто\s+я\s+так|в\s+чём\s+смысл",
    re.I,
)
_EMOTION = re.compile(
    r"мне\s+плохо|тяжело|грустн|одинок|устал|боюсь|страшно|"
    r"не\s+могу|депресс|тревож|расстро",
    re.I,
)
_PROGRAMMING = re.compile(
    r"код|python|javascript|typescript|react|unity|игр[ауы]|"
    r"программ|debug|баг|api|алгоритм",
    re.I,
)
_CREATIVE = re.compile(
    r"придумай\s+(?:истори|сказк|сюжет|персонаж)|"
    r"напиши\s+(?:стих|рассказ|сказк)|"
    r"сочини",
    re.I,
)
_EXPLICIT_PRODUCT = re.compile(
    r"нужен\s+сайт|хочу\s+сайт|сделай\s+сайт|лендинг|"
    r"telegram|чатбот|telegram|factory|studio|"
    r"интернет-магазин|под\s+ключ",
    re.I,
)
_EXPLICIT_BUSINESS = re.compile(
    r"открыть\s+(?:бизнес|кофейн|кафе|салон|дело)|"
    r"хочу\s+(?:бизнес|открыть)|"
    r"придумай\s+(?:бизнес|идею)|"
    r"бизнес\s+(?:иде|план|проект)|"
    r"ниша\s+для",
    re.I,
)
_META_CORRECTION = re.compile(
    r"не\s+тот\s+вопрос|не\s+этот\s+вопрос|"
    r"я\s+задавал|задавал\s+не|"
    r"не\s+про\s+это|не\s+об\s+этом|"
    r"неверно\s+понял|не\s+то\s+ответ",
    re.I,
)
_PRODUCT_UNCERTAIN = re.compile(
    r"не\s+знаю.*(?:страниц|сколько\s+страниц|сайт)|"
    r"как\s+скажешь.*(?:страниц|сайт)|"
    r"на\s+тво[ёe]\s+усмотрение.*(?:сайт|страниц)|"
    r"сам\s+реши.*(?:сайт|страниц)",
    re.I,
)


def classify_conversation_type(
    last_user: str,
    messages: list[dict[str, str]] | None = None,
    state: ConversationState | None = None,
) -> ConversationKind:
    """Determine talk mode — personal reflection beats business heuristics."""
    raw = (last_user or "").strip()
    n = normalize_for_intent(raw)
    low = raw.lower()
    st = state or ConversationState.from_messages(messages or [])

    if _META_CORRECTION.search(low):
        return "meta_correction"

    if contains_any(n, "стой", "останов", "хватит", "прекрати", "стоп"):
        return "casual_conversation"

    if contains_any(n, "шутк", "анекдот", "посмея", "смешн"):
        return "humor"

    if _EMOTION.search(low):
        return "emotional_support"

    if _PERSONAL.search(raw) or _MILLION.search(low):
        return "personal_reflection"

    if _PHILOSOPHY.search(low):
        return "philosophy"

    if contains_any(n, "квантов", "физик", "космос", "чёрн", "черн", "наук") or (
        "чёрн" in low and "дыр" in low
    ):
        return "science"

    if contains_any(n, "объясни", "что такое", "как работает") and not _EXPLICIT_BUSINESS.search(
        low
    ):
        if contains_any(n, "урок", "учеб", "экзамен", "домашн"):
            return "education"
        if not contains_any(n, "сайт", "бизнес", "studio"):
            return "science" if contains_any(n, "физик", "космос", "атом") else "general_question"

    if _PROGRAMMING.search(low):
        return "programming"

    if _CREATIVE.search(low):
        return "creative"

    if _EXPLICIT_PRODUCT.search(low) or st.needs_website or st.needs_app or st.wants_studio:
        return "product_creation"

    if (
        _EXPLICIT_BUSINESS.search(low)
        or st.goal in ("open_business", "ai_company")
        or (st.business_type and _business_thread_active(messages))
    ):
        return "business_consulting"

    if _PRODUCT_UNCERTAIN.search(raw) and _business_thread_active(messages):
        return "product_creation"

    if contains_any(n, "привет", "здравствуй", "hello", "hi", "добрый", "доброе"):
        return "casual_conversation"

    if contains_any(n, "как дела", "как ты", "как вы", "что нового", "давай поговорим"):
        return "casual_conversation"

    if contains_any(n, "письм", "email", "резюме", "текст для"):
        return "creative"

    if _business_thread_active(messages) and not _PERSONAL.search(raw):
        return "business_consulting"

    return "general_question"


def is_business_mode(kind: ConversationKind) -> bool:
    return kind in _BUSINESS_KINDS


def is_product_mode(kind: ConversationKind) -> bool:
    return kind in _PRODUCT_KINDS


def allows_unsolicited_sales(kind: ConversationKind) -> bool:
    return kind in _BUSINESS_KINDS


def _business_thread_active(messages: list[dict[str, str]] | None) -> bool:
    if not messages:
        return False
    for m in reversed(messages):
        if m.get("role") != "user":
            continue
        t = (m.get("content") or "").lower()
        if _PERSONAL.search(m.get("content") or ""):
            return False
        if _EXPLICIT_BUSINESS.search(t) or _EXPLICIT_PRODUCT.search(t):
            return True
        if contains_any(normalize_for_intent(t), "бизнес", "кофейн", "сайт", "открыть"):
            return True
        if re.search(r"бюджет|€|евро|\d+\s*к\s*(?:руб|rub|₽)", t):
            return True
    return False
