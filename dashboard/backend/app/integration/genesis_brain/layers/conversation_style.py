"""
Conversation Style Engine — variety in greetings and closings.

Public assistant never repeats the same welcome twice in a row.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, PUBLIC_WELCOME

_GREETING_FIRST = [
  PUBLIC_WELCOME,
  f"Привет! Я {ASSISTANT_NAME} — чем займёмся?",
  f"Здравствуйте! {ASSISTANT_NAME} на связи. О чём думаете?",
]

_SMALL_TALK = [
  "Всё хорошо, спасибо! 😊 А у вас как?",
  "Отлично, на связи. Чем могу помочь сегодня?",
  "Нормально, спасибо что спросили. А вы как?",
  "Всё отлично. Что сегодня будем создавать или обсуждать?",
]

_GREETING_RETURN = [
  (
    "Добро пожаловать обратно.\n\n"
    "Рад новой встрече.\n\n"
    "О чём поговорим сегодня?"
  ),
  (
    "Снова рад Вас видеть.\n\n"
    "Чем займёмся на этот раз?"
  ),
  (
    "Рад снова видеть Вас.\n\n"
    "Чем сегодня могу быть полезен?"
  ),
  (
    "Вы снова здесь — отлично.\n\n"
    "Продолжим с того, что важно, или начнём новую тему?"
  ),
]

_GREETING_NAMED = [
  "Добро пожаловать обратно, {name}.\n\nРад новой встрече.\n\nО чём поговорим сегодня?",
  "{name}, рад снова Вас видеть.\n\nЧем могу помочь сегодня?",
  "Здравствуйте, {name}!\n\nХорошо, что Вы снова здесь.\n\nС чего начнём?",
  f"{{name}}, {ASSISTANT_NAME} на связи.\n\nЧто для Вас сейчас в приоритете?",
]

_MORNING = [
  f"Доброе утро! Рад видеть Вас на {BRAND_NAME}.\n\nЧем займёмся сегодня?",
  f"Доброе утро.\n\n{ASSISTANT_NAME} на связи — чем могу помочь?",
  f"Доброе утро! {ASSISTANT_NAME} готов.\n\nС чего начнём день?",
]

_GREETING_FAMILIAR = [
  "Чем займёмся сегодня?",
  "Рад снова видеть Вас.\n\nО чём поговорим?",
  f"{ASSISTANT_NAME} на связи.\n\nЧто для Вас сейчас в приоритете?",
  "Хорошо, что Вы снова здесь.\n\nС чего начнём?",
]

_GREETING_LONG_TERM = [
  "Надеюсь, день проходит хорошо.\n\nЧем могу быть полезен?",
  "Рад нашей давней беседе.\n\nО чём поговорим сегодня?",
  "Вы снова здесь — ценю это.\n\nЧем займёмся?",
  f"{ASSISTANT_NAME} на связи.\n\nПродолжим или новая тема?",
]

_EVENING = [
  f"Добрый вечер! Рад, что заглянули на {BRAND_NAME}.\n\nЧем могу помочь?",
  f"Добрый вечер.\n\n{ASSISTANT_NAME} на связи — о чём поговорим?",
  "Добрый вечер.\n\nРад видеть Вас — с чего начнём?",
]


@dataclass(frozen=True)
class StyleContext:
  visit_count: int = 0
  name: str | None = None
  visitor_id: str = "anonymous"
  hour: int = 12


class ConversationStyleEngine:
  """Picks natural, non-repeating phrasing from constitution pools."""

  def pick_small_talk(self, ctx: StyleContext, message: str = "") -> str:
    pool = _SMALL_TALK
    idx = int(
      hashlib.sha256(f"{ctx.visitor_id}:small_talk:{message[:40]}".encode()).hexdigest(),
      16,
    ) % len(pool)
    return pool[idx]

  def pick_greeting(self, ctx: StyleContext) -> str:
    pools: list[list[str]]
    if ctx.visit_count <= 1:
      pools = [_GREETING_FIRST]
    elif ctx.name and ctx.visit_count < 8:
      pools = [_GREETING_NAMED]
    elif ctx.visit_count >= 20:
      pools = [_GREETING_LONG_TERM, _GREETING_FAMILIAR]
    else:
      pools = [_GREETING_RETURN, _GREETING_FAMILIAR]

    if 5 <= ctx.hour < 12:
      pools.append(_MORNING)
    elif ctx.hour >= 18:
      pools.append(_EVENING)

    flat = [g for pool in pools for g in pool]
    idx = int(hashlib.sha256(f"{ctx.visitor_id}:{ctx.visit_count}".encode()).hexdigest(), 16) % len(flat)
    text = flat[idx]
    if ctx.name and "{name}" in text:
      return text.format(name=ctx.name)
    return text

  def pick_closing(self, ctx: StyleContext) -> str | None:
    return None

  def enrich_context(self, profile: dict[str, Any]) -> StyleContext:
    visits = int(profile.get("visit_count") or 0)
    name = profile.get("name") or profile.get("owner_name")
    vid = str(profile.get("visitor_id") or "anonymous")
    hour = datetime.now(timezone.utc).hour
    return StyleContext(visit_count=visits, name=name, visitor_id=vid, hour=hour)

  def build_context(self, profile: dict[str, Any], visitor_id: str = "anonymous") -> StyleContext:
    """Build greeting style context from memory profile (personality + greeting API)."""
    visits = int(profile.get("visit_count") or 0)
    name = profile.get("name") or profile.get("owner_name")
    hour = datetime.now(timezone.utc).hour
    return StyleContext(
      visit_count=visits,
      name=name,
      visitor_id=(visitor_id or "anonymous")[:64],
      hour=hour,
    )

  @staticmethod
  def is_greeting_message(text: str) -> bool:
    low = (text or "").strip().lower()
    if not low or len(low) > 120:
      return False
    markers = (
      "привет",
      "здравств",
      "hello",
      "hi ",
      " hi",
      "hallo",
      "добрый",
      "доброе утро",
      "добрый день",
      "добрый вечер",
      "хай",
      "hey",
      "салют",
      "здарова",
      "здаров",
      "здрасти",
      "дарова",
      "прив",
    )
    return any(m in low for m in markers)

  @staticmethod
  def is_small_talk_message(text: str) -> bool:
    low = (text or "").strip().lower()
    if not low or len(low) > 80:
      return False
    markers = (
      "как дела",
      "как ты",
      "как вы",
      "как сам",
      "что нового",
      "как жизнь",
      "как настроение",
      "how are you",
    )
    return any(m in low for m in markers)
