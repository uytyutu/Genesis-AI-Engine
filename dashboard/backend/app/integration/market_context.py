"""Project market detection — target market drives pricing, language, and legal context.

Never use IP, VPN, or browser geolocation as primary signals.
Primary factor: **target market of the deliverable**, not where the user sits.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from app.integration.locale_service import detect_locale_from_text, resolve_locale
from app.integration.market_registry import (
    MARKET_DE,
    MARKET_DEFAULT,
    MARKET_ES,
    MARKET_FR,
    MARKET_GB,
    MARKET_JP,
    MARKET_PL,
    MARKET_UA,
    MARKET_US,
    MARKET_ZA,
    get_market,
)

_COUNTRY_ALIASES: dict[str, str] = {
    "germany": MARKET_DE,
    "германи": MARKET_DE,
    "deutschland": MARKET_DE,
    "bundesrepublik": MARKET_DE,
    "poland": MARKET_PL,
    "польш": MARKET_PL,
    "polska": MARKET_PL,
    "ukraine": MARKET_UA,
    "украин": MARKET_UA,
    "usa": MARKET_US,
    "сша": MARKET_US,
    "united states": MARKET_US,
    "america": MARKET_US,
    "америк": MARKET_US,
    "united kingdom": MARKET_GB,
    "britain": MARKET_GB,
    "великобритан": MARKET_GB,
    "англи": MARKET_GB,
    "france": MARKET_FR,
    "франци": MARKET_FR,
    "spain": MARKET_ES,
    "испани": MARKET_ES,
    "south africa": MARKET_ZA,
    "южн африк": MARKET_ZA,
    "япони": MARKET_JP,
    "japan": MARKET_JP,
    "росси": "RU",
    "russia": "RU",
    "австри": "AT",
    "austria": "AT",
}

_TLD_MARKET: dict[str, str] = {
    "de": MARKET_DE,
    "pl": MARKET_PL,
    "ua": MARKET_UA,
    "us": MARKET_US,
    "uk": MARKET_GB,
    "fr": MARKET_FR,
    "es": MARKET_ES,
    "za": MARKET_ZA,
    "jp": MARKET_JP,
    "at": "AT",
    "ru": "RU",
}

_TARGET_MARKET_PATTERNS: tuple[tuple[re.Pattern[str], str, int], ...] = (
    (re.compile(r"(?i)для\s+(?:рынка\s+)?(\w[\w\s-]{2,30})", re.U), "target_explicit_ru", 90),
    (re.compile(r"(?i)for\s+(?:the\s+)?(\w[\w\s-]{2,30})\s+market", re.U), "target_explicit_en", 90),
    (re.compile(r"(?i)(?:сайт|website|продукт|product|бизнес|business)\s+для\s+(\w[\w\s-]{2,20})", re.U), "deliverable_for", 85),
    (re.compile(r"(?i)(?:opening|open|register|launch)(?:ing)?\s+(?:a\s+)?(?:company|business)\s+in\s+(\w+)", re.U), "business_in", 80),
    (re.compile(r"(?i)(?:открыва|регистрир|запуска).{0,20}(?:компани|бизнес).{0,20}в\s+(\w[\w-]+)", re.U), "business_in_ru", 80),
    (re.compile(r"(?i)target(?:ing)?\s+(\w[\w\s-]{2,20})", re.U), "targeting", 75),
)

_CLIENT_LOCATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)(?:я\s+)?(?:живу|нахожусь|сейчас)\s+в\s+(\w[\w\s-]{2,20})", re.U),
    re.compile(r"(?i)i(?:'m|\s+am)\s+(?:in|from|based in)\s+(\w[\w\s-]{2,20})", re.U),
)

_LEGAL_MARKET_HINTS: dict[str, str] = {
    "impressum": MARKET_DE,
    "datenschutz": MARKET_DE,
    "dsgvo": MARKET_DE,
    "gdpr": MARKET_DE,
    "rodo": MARKET_PL,
}

_CURRENCY_MARKET_HINT: dict[str, str] = {
    "€": MARKET_DE,
    "eur": MARKET_DE,
    "евро": MARKET_DE,
    "$": MARKET_US,
    "usd": MARKET_US,
    "доллар": MARKET_US,
    "zł": MARKET_PL,
    "pln": MARKET_PL,
    "грн": MARKET_UA,
    "uah": MARKET_UA,
    "£": MARKET_GB,
    "gbp": MARKET_GB,
}


@dataclass
class MarketSignal:
    kind: str
    market_code: str
    weight: int
    source: str


@dataclass
class ProjectMarketContext:
    """Three market concepts — target_market is primary for commerce."""

    client_country: str | None = None
    business_country: str | None = None
    target_market: str | None = None
    target_market_code: str = MARKET_DEFAULT
    project_language: str | None = None
    currency_hint: str | None = None
    signals: list[MarketSignal] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    confidence: str = "unknown"  # unknown | low | medium | high
    needs_clarification: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "client_country": self.client_country,
            "business_country": self.business_country,
            "target_market": self.target_market,
            "target_market_code": self.target_market_code,
            "project_language": self.project_language,
            "currency_hint": self.currency_hint,
            "confidence": self.confidence,
            "needs_clarification": self.needs_clarification,
            "conflicts": list(self.conflicts),
            "signals": [
                {"kind": s.kind, "market_code": s.market_code, "weight": s.weight, "source": s.source}
                for s in self.signals
            ],
        }


def _normalize_country_token(token: str) -> str | None:
    t = token.strip().lower().rstrip(".,;:")
    if not t or len(t) < 2:
        return None
    for alias, code in _COUNTRY_ALIASES.items():
        if alias in t or t in alias:
            return code
    return None


def _country_name_for_code(code: str, *, locale: str = "ru") -> str:
    return get_market(code).name(locale)


def extract_market_signals(text: str) -> list[MarketSignal]:
    """Parse user text for market signals — no IP or browser locale."""
    if not text or not text.strip():
        return []
    signals: list[MarketSignal] = []
    sample = text.strip()

    for pattern, kind, weight in _TARGET_MARKET_PATTERNS:
        m = pattern.search(sample)
        if m:
            code = _normalize_country_token(m.group(1))
            if code:
                signals.append(MarketSignal(kind=kind, market_code=code, weight=weight, source=m.group(0)[:80]))

    for pattern in _CLIENT_LOCATION_PATTERNS:
        m = pattern.search(sample)
        if m:
            code = _normalize_country_token(m.group(1))
            if code:
                signals.append(MarketSignal(kind="client_location", market_code=code, weight=40, source=m.group(0)[:80]))

    for tld, code in _TLD_MARKET.items():
        if re.search(rf"(?i)\.{re.escape(tld)}\b", sample):
            signals.append(MarketSignal(kind="tld", market_code=code, weight=55, source=f".{tld}"))

    low = sample.lower()
    for term, code in _LEGAL_MARKET_HINTS.items():
        if term in low:
            signals.append(MarketSignal(kind="legal_term", market_code=code, weight=70, source=term))

    for token, code in _CURRENCY_MARKET_HINT.items():
        if token in low:
            signals.append(MarketSignal(kind="currency", market_code=code, weight=35, source=token))

    for alias, code in _COUNTRY_ALIASES.items():
        if re.search(rf"(?i)\b{re.escape(alias)}\b", low):
            signals.append(MarketSignal(kind="country_mention", market_code=code, weight=50, source=alias))

    return signals


def resolve_market_context(
    messages: list[dict[str, str]] | None = None,
    *,
    text: str | None = None,
    ui_locale: str | None = None,
) -> ProjectMarketContext:
    """Resolve project market from dialogue. Target market wins over client location."""
    ctx = ProjectMarketContext()
    chunks: list[str] = []
    if text:
        chunks.append(text)
    if messages:
        for m in messages:
            if m.get("role") == "user":
                chunks.append((m.get("content") or "").strip())

    combined = "\n".join(c for c in chunks if c)
    if not combined.strip():
        ctx.project_language = resolve_locale(ui_locale)
        return ctx

    all_signals: list[MarketSignal] = []
    for chunk in chunks:
        all_signals.extend(extract_market_signals(chunk))
    ctx.signals = all_signals

    detected_lang = detect_locale_from_text(combined)
    ctx.project_language = resolve_locale(detected_lang or ui_locale)

    target_signals = [s for s in all_signals if s.kind in {
        "target_explicit_ru", "target_explicit_en", "deliverable_for",
        "business_in", "business_in_ru", "targeting",
    }]
    business_signals = [s for s in all_signals if s.kind in {"business_in", "business_in_ru"}]
    client_signals = [s for s in all_signals if s.kind == "client_location"]
    supporting = [s for s in all_signals if s.kind in {"legal_term", "tld", "country_mention", "currency"}]

    def _best(sigs: list[MarketSignal]) -> str | None:
        if not sigs:
            return None
        ranked = sorted(sigs, key=lambda s: s.weight, reverse=True)
        return ranked[0].market_code

    if target_signals:
        ctx.target_market_code = _best(target_signals) or MARKET_DEFAULT
        ctx.confidence = "high"
    elif business_signals:
        ctx.target_market_code = _best(business_signals) or MARKET_DEFAULT
        ctx.business_country = _country_name_for_code(ctx.target_market_code)
        ctx.confidence = "medium"
    elif supporting:
        ctx.target_market_code = _best(supporting) or MARKET_DEFAULT
        ctx.confidence = "medium"
    elif client_signals:
        ctx.client_country = _country_name_for_code(_best(client_signals) or MARKET_DEFAULT)
        ctx.target_market_code = _best(client_signals) or MARKET_DEFAULT
        ctx.confidence = "low"

    if business_signals:
        bc = _best(business_signals)
        if bc:
            ctx.business_country = _country_name_for_code(bc)
    if client_signals:
        cc = _best(client_signals)
        if cc:
            ctx.client_country = _country_name_for_code(cc)

    ctx.target_market = _country_name_for_code(ctx.target_market_code)
    if ctx.target_market_code == MARKET_DEFAULT:
        ctx.target_market = None

    codes_seen = {s.market_code for s in all_signals if s.weight >= 50}
    if len(codes_seen) > 1:
        names = [_country_name_for_code(c) for c in sorted(codes_seen)]
        ctx.conflicts.append(f"Сигналы указывают на разные рынки: {', '.join(names)}")
        ctx.needs_clarification = True
        if ctx.confidence != "high":
            ctx.confidence = "low"

    if ctx.confidence == "unknown" and not ctx.target_market:
        ctx.needs_clarification = True

    return ctx


def market_clarification_question(ctx: ProjectMarketContext, *, locale: str = "ru") -> str | None:
    """Polite clarification when signals conflict or target market unknown."""
    if not ctx.needs_clarification:
        return None
    loc = resolve_locale(locale)
    if ctx.conflicts:
        conflict = ctx.conflicts[0]
        if loc == "de":
            return (
                f"Ich sehe widersprüchliche Hinweise ({conflict}). "
                "Für welchen Markt soll das Projekt genutzt werden — wo arbeitet Ihr Business?"
            )
        if loc == "en":
            return (
                f"I noticed mixed signals ({conflict}). "
                "Which market is this project for — where will the business operate?"
            )
        return (
            f"Я заметил, что часть информации указывает на разные рынки ({conflict}).\n\n"
            "**Для какого рынка будет использоваться этот проект?**\n"
            "(Где будет работать бизнес и где клиенты увидят результат — не обязательно там, где вы сейчас.)"
        )
    if loc == "de":
        return "Für welches Land / welchen Markt erstellen wir dieses Projekt?"
    if loc == "en":
        return "Which country or market is this project for?"
    return (
        "**Для какой страны / рынка создаётся этот проект?**\n"
        "Это определяет язык, валюту, юридические требования и ориентировочную стоимость."
    )


def market_detection_rules_for_vector() -> str:
    """Injected into Vector commerce / system knowledge."""
    return """## Глобальная локализация и определение рынка

**Virtus Core — глобальная цифровая компания.** Любая услуга адаптируется под рынок проекта.

### Три понятия (не путать)
1. **Страна клиента** — где человек сейчас (слабый сигнал).
2. **Страна регистрации бизнеса** — если уже есть.
3. **Целевой рынок проекта** — **главный** для цены, языка, юр. требований и структуры результата.

### Как определять рынок (без IP и VPN)
Используй **несколько сигналов вместе**:
- что сказал клиент («сайт для Германии», «компания во Франции»);
- язык проекта и переписки;
- валюта в запросе;
- адрес, контакты, домен (.de, .fr, .ua);
- юр. требования (Impressum, Datenschutz → Германия);
- целевая аудитория.

**Ни один сигнал сам по себе не решает.** VPN и местоположение ноутбука **не** определяют цену.

### Примеры
- Клиент в Польше, бизнес в Германии → рынок **Германия**, немецкий, DE-цены.
- Клиент в США (VPN), сайт для украинского НКО → рынок **Украина**.

### При противоречии
Не обвиняй. Уточни: «Для какого рынка будет использоваться проект?»

### Язык проекта
Один язык на весь проект — без смешивания. Язык диалога = язык результата.

### Юридические требования по стране
- Германия: Impressum, Datenschutz.
- Другие страны — соответствующие нормы.
- Если не уверен в полном соответствии закону — **честно скажи**, не создавай ложной уверенности.
"""
