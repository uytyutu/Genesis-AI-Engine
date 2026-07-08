"""
Identity Intent Detector — semantic recognition of questions about Vector / Virtus Core.

Works on normalized text, tolerates typos and speech-recognition errors.
Supports follow-up turns inside an identity conversation thread.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from app.integration.genesis_brain.fuzzy_nlp import contains_any, normalize_for_intent
from app.integration.genesis_brain.user_text_normalizer import normalize_user_text

IdentityKind = Literal[
    "who_are_you",
    "name",
    "name_full",
    "capabilities",
    "about_self",
    "origin",
    "creator",
    "purpose",
    "virtus_core",
    "vector",
    "genesis",
    "genesis_is_you",
    "ai_nature",
    "neural",
    "human",
    "difference",
    "vector_vs_virtus",
    "vector_vs_genesis",
    "why_name",
    "why_genesis",
    "help",
    "system",
    "program",
    "speaker",
]

_IDENTITY_MARKERS = (
    "vector",
    "virtus core",
    "virtus",
    "интеллектуальный ии-помощник",
    "интеллектуальная платформа",
    "внутреннее ядро",
)

_KTO_TAKOY_OTHER = re.compile(
    r"кто\s+так(?:ой|ая|ие)\s+(?!ты\b|вы\b)(?:[\w«\"]|томас|шелби|наполеон|путин|маск)",
    re.I,
)

_WHAT_IS_OTHER = re.compile(
    r"что\s+такое\s+(?!vector|virtus|genesis|генезис|генезес|ты\b|вы\b|это\b|ии\b|бот\b|"
    r"систем|программ|платформ|помощник|ассистент)",
    re.I,
)

_FOLLOWUP_PREFIX = re.compile(
    r"^(?:а|и|ну|ок|ладно|хорошо|так|ещё|еще)\b",
    re.I,
)

_SUBJECT_LEFT = re.compile(
    r"\b(?:погод|температур|дожд|солнц|рецепт|напиши\s+код|исправь\s+баг|"
    r"ошибк[аи]\s+в|томас\s+шелби|наполеон|биткоин|курс\s+доллар|"
    r"придумай\s+истори|сочини\s+стих|посчитай|сколько\s+будет)\b",
    re.I,
)

_INTENT_SIGNALS: dict[IdentityKind, tuple[str, ...]] = {
    "who_are_you": (
        "кто ты",
        "ты кто",
        "что ты такое",
        "что ты из себя",
        "кто вы",
        "кто ты такой",
        "кто такой ты",
        "кто такой",
        "who are you",
        "what are you",
    ),
    "name": (
        "как тебя зовут",
        "как вас зовут",
        "твое имя",
        "твоё имя",
        "ваше имя",
        "как тебя называть",
        "как называется этот ии",
        "как называется эта система",
        "what is your name",
    ),
    "name_full": (
        "как тебя зовут полностью",
        "полное имя",
        "твоё полное имя",
    ),
    "capabilities": (
        "что ты умеешь",
        "что вы умеете",
        "что умеешь",
        "твои возможности",
        "какие возможности",
        "какие у тебя возможности",
        "какие возможности у тебя",
        "что можешь делать",
        "что ты можешь",
        "what can you do",
        "умеешь в целом",
    ),
    "about_self": (
        "расскажи о себе",
        "расскажи про себе",
        "раскажи о себе",
        "расскажи немного о себе",
        "представься",
        "представь себя",
        "tell me about yourself",
    ),
    "origin": (
        "откуда ты",
        "как ты появился",
        "когда ты появился",
        "когда появился",
        "где ты родился",
        "where are you from",
    ),
    "creator": (
        "кто тебя создал",
        "кто тебя сделал",
        "кто вас создал",
        "кто тебя разработал",
        "кто тебя написал",
        "кем ты создан",
        "зачем тебя создали",
        "who created you",
        "who made you",
    ),
    "purpose": (
        "для чего ты создан",
        "зачем ты существуешь",
        "какова твоя цель",
        "в чем твоя задача",
        "в чём твоя задача",
        "твоя цель",
        "твоя задача",
        "зачем ты нужен",
    ),
    "virtus_core": (
        "что такое virtus core",
        "что такое virtus",
        "что за virtus",
        "virtus core это",
    ),
    "vector": (
        "что такое vector",
        "кто такой vector",
        "что значит vector",
    ),
    "why_name": (
        "почему тебя так зовут",
        "почему vector",
        "почему такое название",
        "откуда имя vector",
    ),
    "genesis": (
        "что такое genesis",
        "genesis тогда что",
        "а genesis",
        "что за genesis",
        "genesis это",
        "что такое генезис",
        "что такое генезес",
        "что за генезис",
    ),
    "genesis_is_you": (
        "genesis это ты",
        "genesis — это ты",
        "ты genesis",
        "genesis тогда ты",
        "это ты genesis",
    ),
    "why_genesis": (
        "почему genesis",
        "зачем genesis",
        "откуда название genesis",
    ),
    "ai_nature": (
        "ты искусственный интеллект",
        "ты ии",
        "ты чат бот",
        "ты чат-бот",
        "ты бот",
        "ты программа",
        "ты языковая модель",
        "are you an ai",
        "are you a chatbot",
    ),
    "neural": (
        "ты нейросеть",
        "ты настоящий ии",
        "настоящий ии",
        "ты реальный ии",
    ),
    "human": (
        "ты человек",
        "ты живой",
        "ты реальный человек",
    ),
    "difference": (
        "чем ты отличаешься",
        "чем отличаешься от других",
        "чем лучше других ии",
        "чем ты лучше",
    ),
    "vector_vs_virtus": (
        "чем vector отличается от virtus",
        "чем virtus core отличается",
        "чем virtus отличается от vector",
        "vector и virtus core",
    ),
    "vector_vs_genesis": (
        "чем vector отличается от genesis",
        "vector и genesis",
        "genesis и vector",
    ),
    "help": (
        "чем занимаешься",
        "чем занимаешся",
        "чем ты занимаешься",
        "чем можешь помочь",
        "чем можешь мне помочь",
        "как ты можешь помочь",
        "чем полезен",
        "how can you help",
    ),
    "system": (
        "что это за система",
        "что это за ии",
        "что за система",
        "что за ии",
        "что это за платформа",
        "what is this system",
    ),
    "program": (
        "что это за программа",
        "что за программа",
        "что это за приложение",
        "какая это программа",
    ),
    "speaker": (
        "кто со мной разговаривает",
        "кто со мной говорит",
        "кто мне отвечает",
        "кто отвечает мне",
        "с кем я говорю",
        "who am i talking to",
    ),
}

_CONTINUATION_FRAGMENTS = (
    "чем занимаешь",
    "чем занимаешся",
    "что умеешь",
    "кто создал",
    "кто сделал",
    "кто тебя",
    "откуда ты",
    "как появил",
    "когда появил",
    "почему так зовут",
    "зачем",
    "цель",
    "задача",
    "возможност",
    "помочь",
    "virtus",
    "vector",
    "genesis",
    "расскажи",
    "представь",
    "отличаешь",
    "создан",
    "существуешь",
)

_ASSISTANT_IDENTITY_HINT = re.compile(
    r"\bvector\b|virtus\s*core|внутренн\w+\s+ядр",
    re.I,
)


@dataclass(frozen=True)
class IdentityIntent:
    kind: IdentityKind
    confidence: float
    is_follow_up: bool = False


def _phrase_similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _best_kind(normalized: str) -> tuple[IdentityKind | None, float]:
    best_kind: IdentityKind | None = None
    best_score = 0.0

    for kind, phrases in _INTENT_SIGNALS.items():
        for phrase in phrases:
            if phrase in normalized:
                score = 2.0 + len(phrase) / 40.0
                if score > best_score:
                    best_score = score
                    best_kind = kind

    if best_kind is not None:
        return best_kind, min(1.0, best_score / 3.0)

    for kind, phrases in _INTENT_SIGNALS.items():
        for phrase in phrases:
            ratio = _phrase_similarity(normalized, phrase)
            if ratio >= 0.82 and ratio * len(phrase) > best_score:
                best_score = ratio * len(phrase)
                best_kind = kind
            tokens = normalized.split()
            if len(tokens) <= 8:
                for window in range(2, min(6, len(tokens) + 1)):
                    for i in range(len(tokens) - window + 1):
                        chunk = " ".join(tokens[i : i + window])
                        ratio = _phrase_similarity(chunk, phrase)
                        if ratio >= 0.86 and ratio * len(phrase) > best_score:
                            best_score = ratio * len(phrase)
                            best_kind = kind
    if best_kind is None:
        return None, 0.0
    confidence = min(1.0, best_score / 3.0)
    return best_kind, confidence


def _is_about_third_party(text: str, normalized: str) -> bool:
    if _KTO_TAKOY_OTHER.search(text):
        return True
    if _WHAT_IS_OTHER.search(normalized):
        return True
    if re.search(r"кто\s+так(?:ой|ая)\s+[\w«\"]", text, re.I):
        if not re.search(r"кто\s+так(?:ой|ая)\s+ты\b", text, re.I):
            if not contains_any(normalized, "vector", "virtus", "genesis"):
                return True
    return False


def _assistant_recently_on_identity(messages: list[dict[str, str]] | None) -> bool:
    if not messages:
        return False
    for msg in reversed(messages[-6:]):
        role = msg.get("role")
        content = (msg.get("content") or "").strip()
        if not content:
            continue
        if role == "assistant" and _ASSISTANT_IDENTITY_HINT.search(content):
            return True
        if role == "assistant" and any(m in content.lower() for m in _IDENTITY_MARKERS):
            return True
    return False


def _user_recently_on_identity(messages: list[dict[str, str]] | None) -> bool:
    if not messages:
        return False
    user_turns = [m for m in messages if m.get("role") == "user"][-3:]
    for msg in user_turns[:-1]:
        intent = detect_identity_intent(msg.get("content") or "", messages=None)
        if intent is not None:
            return True
    return False


def _in_identity_thread(messages: list[dict[str, str]] | None) -> bool:
    return _assistant_recently_on_identity(messages) or _user_recently_on_identity(messages)


def _follow_up_intent(normalized: str) -> IdentityIntent | None:
    if _SUBJECT_LEFT.search(normalized):
        return None
    if not any(frag in normalized for frag in _CONTINUATION_FRAGMENTS):
        if not _FOLLOWUP_PREFIX.search(normalized):
            return None
    kind, confidence = _best_kind(normalized)
    if kind is not None and confidence >= 0.35:
        return IdentityIntent(kind=kind, confidence=confidence, is_follow_up=True)
    if _FOLLOWUP_PREFIX.search(normalized) or len(normalized.split()) <= 8:
        for frag in _CONTINUATION_FRAGMENTS:
            if frag in normalized or _phrase_similarity(normalized, frag) >= 0.84:
                kind2, conf2 = _best_kind(normalized)
                if kind2:
                    return IdentityIntent(kind=kind2, confidence=max(conf2, 0.55), is_follow_up=True)
                if "занимаеш" in normalized:
                    return IdentityIntent(kind="help", confidence=0.6, is_follow_up=True)
                if "умеешь" in normalized or "возможност" in normalized:
                    return IdentityIntent(kind="capabilities", confidence=0.65, is_follow_up=True)
                if "создал" in normalized or "сделал" in normalized:
                    return IdentityIntent(kind="creator", confidence=0.65, is_follow_up=True)
                if "появил" in normalized or "откуда" in normalized:
                    return IdentityIntent(kind="origin", confidence=0.6, is_follow_up=True)
                if "genesis" in normalized:
                    return IdentityIntent(kind="genesis", confidence=0.7, is_follow_up=True)
                if "virtus" in normalized:
                    return IdentityIntent(kind="virtus_core", confidence=0.65, is_follow_up=True)
                if "зовут" in normalized or "vector" in normalized:
                    return IdentityIntent(kind="name", confidence=0.6, is_follow_up=True)
    return None


def detect_identity_intent(
    text: str,
    messages: list[dict[str, str]] | None = None,
) -> IdentityIntent | None:
    """Return identity intent when the user asks about Vector / Virtus Core / self."""
    raw = (text or "").strip()
    if not raw:
        return None

    normalized = normalize_for_intent(normalize_user_text(raw))
    if not normalized:
        return None

    if _is_about_third_party(raw, normalized):
        return None

    if _SUBJECT_LEFT.search(normalized) and not _in_identity_thread(messages):
        return None

    in_thread = _in_identity_thread(messages)

    kind, confidence = _best_kind(normalized)
    if kind is not None and confidence >= 0.33:
        return IdentityIntent(kind=kind, confidence=confidence, is_follow_up=in_thread)

    # Short direct questions about assistant
    if re.search(r"^(?:кто|что|чем|как|где|зачем|откуда|какие)\b", normalized):
        if contains_any(
            normalized,
            "ты",
            "вы",
            "тебя",
            "вас",
            "собеседник",
            "систем",
            "ии",
            "бот",
            "возможност",
        ):
            if "кто ты" in normalized or normalized in {"кто ты", "ты кто", "что ты"}:
                return IdentityIntent(kind="who_are_you", confidence=0.9, is_follow_up=in_thread)
            if contains_any(normalized, "зовут", "имя"):
                return IdentityIntent(kind="name", confidence=0.75, is_follow_up=in_thread)
            if contains_any(normalized, "умеешь", "можешь", "возможност"):
                return IdentityIntent(kind="capabilities", confidence=0.75, is_follow_up=in_thread)
            if contains_any(normalized, "создал", "сделал", "разработал"):
                return IdentityIntent(kind="creator", confidence=0.75, is_follow_up=in_thread)
            if contains_any(normalized, "занимаешь", "делаешь", "работаешь"):
                return IdentityIntent(kind="help", confidence=0.7, is_follow_up=in_thread)
            if contains_any(normalized, "появил", "откуда", "родил"):
                return IdentityIntent(kind="origin", confidence=0.7, is_follow_up=in_thread)
            if contains_any(normalized, "цель", "задача", "зачем", "существуешь", "создан"):
                return IdentityIntent(kind="purpose", confidence=0.7, is_follow_up=in_thread)

    if in_thread:
        follow = _follow_up_intent(normalized)
        if follow is not None:
            return follow

    return None