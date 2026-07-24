"""
Conversation State — facts extracted from dialogue (not raw messages).

Pipeline: messages → Fact Extraction → state → Reasoning → Response
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_COUNTRY_MAP: dict[str, str] = {
    "герман": "Германия",
    "germany": "Германия",
    "росси": "Россия",
    "украин": "Украина",
    "польш": "Польша",
    "казах": "Казахстан",
    "сша": "США",
    "америк": "США",
    "беларус": "Беларусь",
    "австр": "Австрия",
}

_CITY_MAP: dict[str, str] = {
    "москв": "Москва",
    "спб": "Санкт-Петербург",
    "петербург": "Санкт-Петербург",
    "берлин": "Берлин",
    "киев": "Киев",
    "вен": "Вена",
}

_CITY_COUNTRY: dict[str, str] = {
    "Берлин": "Германия",
    "Вена": "Австрия",
    "Москва": "Россия",
    "Санкт-Петербург": "Россия",
    "Киев": "Украина",
}

_BUDGET_EUR = re.compile(
    r"(\d[\d\s.,]*)\s*€|€\s*(\d[\d\s.,]*)|(\d[\d\s.,]*)\s*(?:eur|евро)",
    re.I,
)
_BUDGET_RUB = re.compile(
    r"(\d+)\s*к\s*(?:руб|rub|₽|р\.?\s*уб)|"
    r"(\d[\d\s.,]*)\s*(?:тыс\.?|000)?\s*(?:руб|rub|₽|р\.?\s*уб)",
    re.I,
)
_BUDGET_PLAIN = re.compile(
    r"бюджет\s+(?:только\s+|около\s+|в\s+)?(\d[\d\s.,]*)",
    re.I,
)


@dataclass
class ConversationState:
    """Structured facts — what Genesis knows, not what user said verbatim."""

    country: str | None = None
    city: str | None = None
    budget_amount: int | None = None
    budget_currency: str | None = None  # RUB | EUR
    budget_minimal: bool = False
    goal: str | None = None  # open_business | website | studio | ai_company
    life_goal: str | None = None  # financial_independence | family_time
    motivation: str | None = None
    business_type: str | None = None  # coffee | salon | car_wash | online
    prefers_online: bool = False
    avoids_people: bool = False
    active_topic: str | None = None
    background_topics: list[str] = field(default_factory=list)
    rejected_types: list[str] = field(default_factory=list)
    asked_gaps: list[str] = field(default_factory=list)
    wants_automation: bool | None = None
    user_name: str | None = None
    user_age: int | None = None
    uncertain_niche: bool = False
    needs_website: bool = False
    needs_app: bool = False
    needs_marketing: bool = False
    wants_studio: bool = False
    # Product Consultant v1 — sticky sales goal (not questionnaire facts)
    consultant_intent: str | None = None
    package_choice: str | None = None  # basic | business | premium
    consultant_niche: str | None = None

    @classmethod
    def from_messages(cls, messages: list[dict[str, str]]) -> ConversationState:
        state = cls()
        for m in messages:
            if m.get("role") != "user":
                continue
            state._apply((m.get("content") or "").strip())
        return state

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ConversationState:
        if not data:
            return cls()
        return cls(
            country=data.get("country"),
            city=data.get("city"),
            budget_amount=data.get("budget_amount"),
            budget_currency=data.get("budget_currency"),
            budget_minimal=bool(data.get("budget_minimal")),
            goal=data.get("goal"),
            life_goal=data.get("life_goal"),
            motivation=data.get("motivation"),
            business_type=data.get("business_type"),
            prefers_online=bool(data.get("prefers_online")),
            avoids_people=bool(data.get("avoids_people")),
            active_topic=data.get("active_topic"),
            background_topics=list(data.get("background_topics") or []),
            rejected_types=list(data.get("rejected_types") or []),
            asked_gaps=list(data.get("asked_gaps") or []),
            wants_automation=data.get("wants_automation"),
            user_name=data.get("user_name"),
            user_age=data.get("user_age"),
            uncertain_niche=bool(data.get("uncertain_niche")),
            needs_website=bool(data.get("needs_website")),
            needs_app=bool(data.get("needs_app")),
            needs_marketing=bool(data.get("needs_marketing")),
            wants_studio=bool(data.get("wants_studio")),
            consultant_intent=data.get("consultant_intent"),
            package_choice=data.get("package_choice"),
            consultant_niche=data.get("consultant_niche"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "country": self.country,
            "city": self.city,
            "budget_amount": self.budget_amount,
            "budget_currency": self.budget_currency,
            "budget_minimal": self.budget_minimal,
            "goal": self.goal,
            "life_goal": self.life_goal,
            "motivation": self.motivation,
            "business_type": self.business_type,
            "prefers_online": self.prefers_online,
            "avoids_people": self.avoids_people,
            "active_topic": self.active_topic,
            "background_topics": self.background_topics,
            "rejected_types": self.rejected_types,
            "asked_gaps": self.asked_gaps,
            "wants_automation": self.wants_automation,
            "user_name": self.user_name,
            "user_age": self.user_age,
            "uncertain_niche": self.uncertain_niche,
            "needs_website": self.needs_website,
            "needs_app": self.needs_app,
            "needs_marketing": self.needs_marketing,
            "wants_studio": self.wants_studio,
            "consultant_intent": self.consultant_intent,
            "package_choice": self.package_choice,
            "consultant_niche": self.consultant_niche,
        }

    def merge(self, other: ConversationState) -> ConversationState:
        d = self.to_dict()
        for k, v in other.to_dict().items():
            if k in ("rejected_types", "asked_gaps", "background_topics"):
                merged = list(set((d.get(k) or []) + (v or [])))
                if merged:
                    d[k] = merged
            elif v is not None and v is not False:
                d[k] = v
        return ConversationState.from_dict(d)

    def _apply(self, raw: str) -> None:
        low = raw.lower()

        nm = re.search(r"меня\s+зовут\s+([A-Za-zА-Яа-яЁё\-]+)", raw, re.I)
        if nm:
            self.user_name = nm.group(1).strip()

        age_m = re.search(r"мне\s+(\d{1,2})\s*(?:лет|года|год)?", low)
        if age_m:
            self.user_age = int(age_m.group(1))
        elif re.search(r"мне\s+двадцать\s+семь|мне\s+27", low):
            self.user_age = 27

        if re.search(r"финансов.*независ|financial", low):
            self.life_goal = "financial_independence"
        if re.search(r"семь[ёе]|семей|family", low) and re.search(r"время|провод", low):
            self.life_goal = "family_time"
        if re.search(r"не\s+люблю\s+работать\s+с\s+люд|без\s+людей|не\s+хочу\s+.*люд", low):
            self.avoids_people = True
            self.prefers_online = True
        if re.search(r"лучше\s+онлайн|только\s+онлайн|online", low):
            self.prefers_online = True

        if re.search(r"передумал|передумала", low):
            if self.business_type:
                self.rejected_types.append(self.business_type)
            self.business_type = None
            self.uncertain_niche = True

        if re.search(r"не\s+кофейн|не\s+кафе|не\s+кофе", low):
            if self.business_type == "coffee":
                self.rejected_types.append("coffee")
            self.business_type = None
            self.uncertain_niche = True

        if "автомойк" in low or "car wash" in low:
            self.business_type = "car_wash"
            self.goal = "open_business"
        if re.search(r"ai\s+компан|ии\s+компан|искусственн.*компан", low):
            self.goal = "ai_company"
            self.prefers_online = True

        if re.search(r"бюджет\s+вырос|больше\s+денег|увелич", low) and self.budget_amount:
            pass  # new amount extracted below if present

        if re.search(r"живу\s+в\s+герман|я\s+из\s+герман|германи", low):
            self.country = "Германия"
        if re.search(r"теперь\s+.*австр|живу\s+.*австр|переехал.*австр|переехал\s+в\s+австр", low):
            self.country = "Австрия"
        if re.search(
            r"открыть бизнес|начать бизнес|хочу бизнес|бизнес открыть|открыть дело|хочу открыть",
            low,
        ):
            self.goal = "open_business"
        if re.search(r"у меня\s+(?:есть\s+)?(?:автомойк|кофейн|кафе|салон|магазин|клиник)", low):
            self.goal = "open_business"
        if re.search(r"интернет-магазин|онлайн-магазин", low):
            self.business_type = "shop"
            self.goal = "website"
            self.needs_website = True
        if re.search(r"придумай|идея бизнес|бизнес проект|бизнесс", low):
            self.goal = "open_business"
            if "не знаю" in low or "какой" in low:
                self.uncertain_niche = True
        if self.goal == "open_business" and re.search(r"не\s+знаю\s+как", low):
            self.uncertain_niche = True

        for key, country in _COUNTRY_MAP.items():
            if key in low or f"страна {key}" in low or f"страна {country.lower()}" in low:
                self.country = country

        for key, city in _CITY_MAP.items():
            if key in low:
                self.city = city
        cm = re.search(r"город\s+([A-Za-zА-Яа-яЁё\-]+)", raw, re.I)
        if cm:
            self.city = cm.group(1).strip().capitalize()
        if self.city and not self.country:
            self.country = _CITY_COUNTRY.get(self.city)

        if "минимальн" in low and "бюджет" in low:
            self.budget_minimal = True

        rub = _BUDGET_RUB.search(raw)
        if rub:
            val = next(g for g in rub.groups() if g)
            self.budget_amount = _parse_amount(val, low)
            self.budget_currency = "RUB"
            self.budget_minimal = False

        eur = _BUDGET_EUR.search(raw)
        if eur:
            val = next(g for g in eur.groups() if g)
            self.budget_amount = _parse_amount(val, low)
            self.budget_currency = "EUR"
            self.budget_minimal = False

        bp = _BUDGET_PLAIN.search(raw)
        if bp and not self.budget_amount:
            self.budget_amount = _parse_amount(bp.group(1), low)
            self.budget_currency = self.budget_currency or "EUR"
            self.budget_minimal = False
        elif bp and re.search(r"только|около|если|измен", low):
            self.budget_amount = _parse_amount(bp.group(1), low)
            self.budget_currency = self.budget_currency or "EUR"
            self.budget_minimal = False

        if any(w in low for w in ("кофейн", "кофе", "кафе")) and not re.search(
            r"не\s+(кофейн|кофе|кафе)", low
        ):
            self.business_type = "coffee"
            self.goal = self.goal or "open_business"
        if any(w in low for w in ("салон", "красот", "барбер")):
            self.business_type = "salon"
        if re.search(r"магазин|e-?commerce", low) and ("интернет" in low or "онлайн" in low):
            self.business_type = "shop"
            self.needs_website = True

        if re.search(r"нужен сайт|хочу сайт|сайт для|хачу сайт", low):
            self.needs_website = True
            self.goal = self.goal or "website"
            self.consultant_intent = self.consultant_intent or "website"
        if "приложен" in low or "app" in low:
            self.needs_app = True
        if any(w in low for w in ("продвижен", "реклам", "маркетинг")):
            self.needs_marketing = True
        if "studio" in low:
            self.wants_studio = True

        if "автоматиз" in low:
            self.wants_automation = True
        if re.search(r"сам\s+управл|каждый день", low):
            self.wants_automation = False

        # Product Consultant sticky goal (Intent / Package / niche)
        try:
            from app.integration.genesis_brain.product_consultant import _absorb_turn

            _absorb_turn(self, raw)
        except Exception:
            pass

    def has_country(self) -> bool:
        if self.country:
            return True
        return bool(self.city and self.city in _CITY_COUNTRY)

    def has_budget(self) -> bool:
        return self.budget_amount is not None or self.budget_minimal

    def has_business_context(self) -> bool:
        """Structured facts beyond bare open_business intent (state-based routing)."""
        return (
            self.has_country()
            or self.has_budget()
            or bool(self.business_type)
            or self.uncertain_niche
            or bool(self.life_goal)
            or self.prefers_online
            or self.avoids_people
        )

    def ready_for_advise_mode(self) -> bool:
        """Country + budget — leave propose loop, switch to advise/follow-ups."""
        return self.has_country() and self.has_budget()

    def has_location(self) -> bool:
        return bool(self.country or self.city)

    def ready_for_business_advice(self) -> bool:
        """Enough facts to recommend — do NOT re-ask country/budget."""
        if self.goal != "open_business":
            return False
        if self.has_budget():
            return True
        return self.has_country() and bool(self.business_type)

    def ready_for_proposal(self) -> bool:
        """Enough context to offer directions — questions optional."""
        if self.goal == "ai_company":
            return True
        if self.goal != "open_business":
            return False
        return bool(
            self.life_goal
            or self.prefers_online
            or self.avoids_people
            or self.has_location()
            or self.has_budget()
        )

    def question_already_asked(
        self, gap: str, messages: list[dict[str, str]] | None = None
    ) -> bool:
        if gap in self.asked_gaps:
            return True
        if not messages:
            return False
        patterns = {
            "country": r"в какой стране",
            "budget": r"какой бюджет",
            "niche": r"офлайн или онлайн",
        }
        pat = patterns.get(gap)
        if not pat:
            return False
        for m in messages:
            if m.get("role") == "assistant" and re.search(
                pat, (m.get("content") or "").lower()
            ):
                return True
        return False

    def mark_question_asked(self, gap: str) -> None:
        if gap not in self.asked_gaps:
            self.asked_gaps.append(gap)

    def missing_critical(
        self, messages: list[dict[str, str]] | None = None
    ) -> list[str]:
        """Gaps worth one optional question — skip gaps already asked in dialogue."""
        if self.goal != "open_business":
            return []
        gaps: list[str] = []
        if self.uncertain_niche and not self.business_type:
            gaps.append("niche")
        if not self.has_country():
            gaps.append("country")
        if not self.has_budget():
            gaps.append("budget")
        if messages:
            gaps = [g for g in gaps if not self.question_already_asked(g, messages)]
        return gaps[:1]

    def budget_display(self) -> str:
        if self.budget_amount and self.budget_currency == "RUB":
            return f"{self.budget_amount:,}".replace(",", " ") + " ₽"
        if self.budget_amount and self.budget_currency == "EUR":
            return f"{self.budget_amount:,}".replace(",", " ") + " €"
        if self.budget_minimal:
            return "минимальный"
        return ""

    def to_prompt_block(self) -> str:
        lines = []
        if self.user_name:
            lines.append(f"Имя: {self.user_name}")
        if self.user_age:
            lines.append(f"Возраст: {self.user_age}")
        if self.country:
            lines.append(f"Страна: {self.country}")
        if self.city:
            lines.append(f"Город: {self.city}")
        bd = self.budget_display()
        if bd:
            lines.append(f"Бюджет: {bd}")
        if self.goal:
            lines.append(f"Цель: {self.goal}")
        if self.life_goal:
            lg = {
                "financial_independence": "финансовая независимость",
                "family_time": "больше времени с семьёй",
            }.get(self.life_goal, self.life_goal)
            lines.append(f"Жизненная цель: {lg}")
        if self.motivation:
            lines.append(f"Мотивация: {self.motivation}")
        if self.prefers_online:
            lines.append("Предпочитает онлайн")
        if self.avoids_people:
            lines.append("Не любит работать с людьми лично")
        if self.business_type:
            lines.append(f"Тип бизнеса: {self.business_type}")
        if self.consultant_intent:
            lines.append(f"Цель диалога (Intent): {self.consultant_intent}")
        if self.package_choice:
            lines.append(f"Пакет: {self.package_choice}")
        elif self.consultant_intent == "website" or self.needs_website:
            lines.append("Пакет: ещё не выбран — помочь выбрать, не спрашивать «какой сайт» снова")
        if self.consultant_niche:
            lines.append(f"Ниша: {self.consultant_niche}")
        if self.active_topic:
            lines.append(f"Активная тема сейчас: {self.active_topic}")
        if self.background_topics:
            lines.append(
                "Завершённые темы (не продолжать, пока человек сам не вернётся): "
                + ", ".join(self.background_topics[-3:])
            )
        if self.rejected_types:
            lines.append(f"Отклонено: {', '.join(self.rejected_types)}")
        if not lines:
            return ""
        return "Известные факты о пользователе (не переспрашивать):\n" + "\n".join(f"- {l}" for l in lines)

    def update_topic_focus(self, last_user: str) -> None:
        topic = self._detect_topic(last_user)
        if not topic:
            return
        if self.active_topic and topic != self.active_topic:
            bg = list(self.background_topics)
            if self.active_topic not in bg:
                bg.append(self.active_topic)
            self.background_topics = bg[-4:]
        self.active_topic = topic

    @staticmethod
    def _detect_topic(text: str) -> str | None:
        low = (text or "").strip().lower()
        if len(low) < 3:
            return None
        rules: tuple[tuple[str, str], ...] = (
            (r"космос|чёрн.*дыр|черн.*дыр|вселенн|галактик|планет", "космос"),
            (r"автомойк|car wash", "бизнес автомойки"),
            (r"миллион|разбогат|богатств|финанс", "финансы и будущее"),
            (r"unity|unreal|игровой движок|геймдев", "разработка игр"),
            (r"\bкод\b|python|javascript|программ", "программирование"),
            (r"политик|выбор|партия", "политика"),
            (r"отношен|любов|семь", "отношения"),
            (r"психолог|тревог|депресс|устал", "психология"),
            (r"кофейн|кафе|ресторан", "бизнес общепита"),
            (r"сайт|лендинг|магазин", "сайт и digital"),
            (r"музык|песн|гитар", "музыка"),
            (r"кино|фильм|сериал", "кино"),
            (r"авто|машин|bmw|mercedes", "автомобили"),
            (r"^(привет|здравствуй|как дела|hello|hi)\b", "small talk"),
        )
        for pattern, label in rules:
            if re.search(pattern, low):
                return label
        if "?" in low and len(low) > 12:
            return low[:48].rstrip("?.! ") + "…"
        return None


def _parse_amount(raw: str, low: str) -> int:
    s = raw.replace(" ", "").replace(",", ".")
    try:
        base = float(s)
    except ValueError:
        digits = re.sub(r"[^\d]", "", raw)
        base = float(digits) if digits else 0
    if re.search(r"(?:\d+\s*к\b|тыс\.?|\bтысяч)", low) and base < 1000:
        base *= 1000
    return int(base)


def pick_opening(visitor_id: str, turn: int) -> str:
    """Service openers disabled — answers start with substance, not filler."""
    return ""


_SERVICE_PREFIXES = (
    "понятно.",
    "ясно.",
    "записал.",
    "записал:",
    "хорошо.",
    "отлично.",
    "спасибо, теперь картина яснее.",
    "теперь уже можно что-то предложить.",
    "спасибо, этого достаточно для старта.",
    "слышу вас.",
    "тогда я бы рекомендовал:",
)


def strip_service_openers(text: str) -> str:
    """Remove automatic service prefixes if they appear at the start of a reply."""
    out = (text or "").strip()
    if not out:
        return out
    while True:
        low = out.lower()
        stripped = False
        for prefix in _SERVICE_PREFIXES:
            if low.startswith(prefix):
                out = out[len(prefix) :].lstrip()
                stripped = True
                break
        if not stripped:
            break
    return out.strip()


class ConversationStateLayer:
    """Extract facts, merge with persisted state, save."""

    def __init__(self, memory_layer: Any, session_store: Any | None = None) -> None:
        self._memory = memory_layer
        self._sessions = session_store

    def process(
        self,
        visitor_id: str,
        messages: list[dict[str, str]],
        *,
        session_id: str | None = None,
    ) -> ConversationState:
        if session_id and self._sessions is not None:
            persisted = ConversationState.from_dict(
                self._sessions.get_conversation_state(session_id)
            )
        else:
            persisted = ConversationState.from_dict(
                (self._memory.load(visitor_id).get("conversation_state") or {})
            )
        extracted = ConversationState.from_messages(messages)
        merged = persisted.merge(extracted)
        last_user = ""
        for m in reversed(messages):
            if m.get("role") == "user":
                last_user = (m.get("content") or "").strip()
                break
        if last_user:
            merged.update_topic_focus(last_user)
        self.persist(visitor_id, merged, session_id=session_id)
        return merged

    def persist(
        self,
        visitor_id: str,
        state: ConversationState,
        *,
        session_id: str | None = None,
    ) -> None:
        if session_id and self._sessions is not None:
            self._sessions.set_conversation_state(session_id, state.to_dict())
            return
        data = self._memory.load(visitor_id)
        data["conversation_state"] = state.to_dict()
        self._memory.save(visitor_id, data)
