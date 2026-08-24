"""B4.2 — READ Business Companion (context-grounded conversation).

Authenticated client → B4.1 tenant-safe Context → READ reply.
No ACTION, Web Research, data mutation, or invented metrics.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Literal

from app.integration.genesis_brain.language_constitution import (
    apply_language_constitution,
    resolve_response_locale,
)
from app.integration.vector.companion_context import CompanionContextService
from app.integration.vector.companion_contracts import (
    ASSISTANT_NAME,
    B4_ENGINE,
    DEFAULT_GREETING_DE,
    ENTRY_SURFACE,
)

B4_2_SLICE = "B4.2"
COMPANION_TURN_PATH = "/api/client/vector/companion-turn"

ReadIntent = Literal[
    "welcome",
    "connected",
    "analytics",
    "next_steps",
    "unknown",
]

_WELCOME_TRIGGERS = frozenset({"__welcome__", "/start", ""})

_CONNECTED_PATTERNS = re.compile(
    r"(?:"
    r"что\s+(?:у\s+меня\s+)?(?:сейчас\s+)?(?:подключ|актив|есть)|"
    r"какие\s+продукт|мои\s+продукт|"
    r"was\s+(?:ist|habe\s+ich)(?:\s+bei\s+mir)?\s+(?:verbunden|aktiv|angeschlossen)|"
    r"welche\s+produkte|meine\s+produkte|"
    r"what(?:'s|\s+is)\s+connected|my\s+products"
    r")",
    re.I,
)

_ANALYTICS_PATTERNS = re.compile(
    r"(?:"
    r"зачем\s+(?:мне\s+)?аналитик|почему\s+аналитик|"
    r"warum\s+(?:brauche\s+ich\s+)?analytics|"
    r"why\s+(?:do\s+i\s+need\s+)?analytics|"
    r"analytics\s+(?:nutzen|vorteil|bringt)"
    r")",
    re.I,
)

_NEXT_STEPS_PATTERNS = re.compile(
    r"(?:"
    r"что\s+(?:мне\s+)?(?:лучше\s+)?(?:сделать|делать)\s+(?:сейчас|дальше|для\s+развития)|"
    r"следующ(?:ий|ие)\s+шаг|развит(?:ие|ия)\s+бизнес|"
    r"was\s+(?:soll\s+ich|kann\s+ich)\s+(?:jetzt|als\s+n(?:ä|ae)chstes)|"
    r"n(?:ä|ae)chster\s+schritt|"
    r"what\s+should\s+i\s+do\s+next|grow\s+my\s+business"
    r")",
    re.I,
)


@dataclass(frozen=True)
class ProductSnapshot:
    company_name: str
    niche: str
    website_owned: bool
    shop_owned: bool
    ai_owned: bool
    analytics_state: str
    analytics_title: str
    analytics_body: str
    analytics_hint: str
    metric_ids: tuple[str, ...]

    def active_labels(self, locale: str) -> list[str]:
        labels: list[str] = []
        if self.website_owned:
            labels.append(_label("website", locale, active=True))
        if self.shop_owned:
            labels.append(_label("shop", locale, active=True))
        if self.ai_owned:
            labels.append(_label("ai", locale, active=True))
        return labels

    def inactive_labels(self, locale: str) -> list[str]:
        labels: list[str] = []
        if not self.website_owned:
            labels.append(_label("website", locale, active=False))
        if not self.shop_owned:
            labels.append(_label("shop", locale, active=False))
        if not self.ai_owned:
            labels.append(_label("ai", locale, active=False))
        return labels


def _label(product: str, locale: str, *, active: bool) -> str:
    loc = (locale or "de")[:2].lower()
    names = {
        "website": {"de": "Website", "ru": "Сайт", "en": "Website"},
        "shop": {"de": "Online-Shop", "ru": "Интернет-магазин", "en": "Online Shop"},
        "ai": {"de": "AI Assistant", "ru": "AI Assistant", "en": "AI Assistant"},
    }
    return names.get(product, {}).get(loc) or names[product]["en"]


def snapshot_from_context(context: dict[str, Any]) -> ProductSnapshot:
    business = context.get("business") or {}
    products = context.get("products") or {}
    analytics = context.get("analytics") or {}
    copy = analytics.get("copy") or {}
    metrics = analytics.get("metrics") or []
    return ProductSnapshot(
        company_name=str(
            business.get("company_name") or business.get("name") or ""
        ).strip(),
        niche=str(business.get("primary_niche") or "").strip(),
        website_owned=bool((products.get("website") or {}).get("owned")),
        shop_owned=bool((products.get("shop") or {}).get("owned")),
        ai_owned=bool((products.get("ai") or {}).get("owned")),
        analytics_state=str(analytics.get("analytics_state") or "not_connected"),
        analytics_title=str(copy.get("title") or ""),
        analytics_body=str(copy.get("body") or ""),
        analytics_hint=str(copy.get("hint") or ""),
        metric_ids=tuple(
            str(m.get("metric_id") or "")
            for m in metrics
            if m.get("metric_id")
        ),
    )


def detect_read_intent(message: str) -> ReadIntent:
    text = (message or "").strip()
    if text in _WELCOME_TRIGGERS:
        return "welcome"
    if _CONNECTED_PATTERNS.search(text):
        return "connected"
    if _ANALYTICS_PATTERNS.search(text):
        return "analytics"
    if _NEXT_STEPS_PATTERNS.search(text):
        return "next_steps"
    return "unknown"


def build_context_brief(snapshot: ProductSnapshot) -> dict[str, Any]:
    """Structured facts for optional LLM grounding — no secrets, no other tenants."""
    return {
        "company_name": snapshot.company_name or None,
        "niche": snapshot.niche or None,
        "products": {
            "website": {"owned": snapshot.website_owned},
            "shop": {"owned": snapshot.shop_owned},
            "ai": {"owned": snapshot.ai_owned},
        },
        "analytics": {
            "state": snapshot.analytics_state,
            "title": snapshot.analytics_title,
            "body": snapshot.analytics_body,
            "hint": snapshot.analytics_hint,
            "metric_ids": list(snapshot.metric_ids),
        },
        "rules": [
            "READ ONLY — never claim changes were applied",
            "Never invent visitors, revenue, or rankings",
            "If a fact is missing, say so or ask one clarifying question",
        ],
    }


def compose_read_reply(
    *,
    message: str,
    snapshot: ProductSnapshot,
    intent: ReadIntent,
    locale: str,
    location: str = "dashboard",
) -> tuple[str, str | None]:
    """Deterministic READ reply from Context facts. Returns (reply, clarify_question)."""
    loc = (locale or "de")[:2].lower()
    if loc not in ("de", "ru", "en"):
        loc = "de"

    if intent == "welcome":
        return _welcome_reply(snapshot, loc, location), None
    if intent == "connected":
        return _connected_reply(snapshot, loc), None
    if intent == "analytics":
        return _analytics_reply(snapshot, loc), None
    if intent == "next_steps":
        return _next_steps_reply(snapshot, loc), None
    return _unknown_reply(message, snapshot, loc)


def _welcome_reply(snapshot: ProductSnapshot, loc: str, location: str) -> str:
    company = snapshot.company_name or _t(loc, "your_business")
    active = snapshot.active_labels(loc)
    inactive = snapshot.inactive_labels(loc)

    if not active:
        return _t(
            loc,
            "welcome_empty",
            company=company,
            greeting=DEFAULT_GREETING_DE if loc == "de" else ASSISTANT_NAME,
        )

    active_txt = ", ".join(active)
    lines = [
        DEFAULT_GREETING_DE if loc == "de" else f"{ASSISTANT_NAME} — Business Assistant.",
        _t(loc, "welcome_active", company=company, active=active_txt, location=location),
    ]
    if snapshot.analytics_state == "not_connected":
        lines.append(_t(loc, "welcome_analytics_not_connected"))
    elif snapshot.analytics_state == "coming_soon":
        lines.append(_t(loc, "welcome_analytics_coming_soon"))
    elif inactive:
        lines.append(
            _t(loc, "welcome_inactive", inactive=", ".join(inactive))
        )
    return "\n\n".join(lines)


def _connected_reply(snapshot: ProductSnapshot, loc: str) -> str:
    active = snapshot.active_labels(loc)
    inactive = snapshot.inactive_labels(loc)
    if not active and not inactive:
        return _t(loc, "connected_none")

    parts = [_t(loc, "connected_intro")]
    if active:
        parts.append(_t(loc, "connected_active", items=", ".join(active)))
    if inactive:
        parts.append(_t(loc, "connected_inactive", items=", ".join(inactive)))
    if snapshot.analytics_state == "not_connected":
        parts.append(_t(loc, "connected_analytics_note"))
    elif snapshot.analytics_state in ("connected_no_data", "connected_with_data"):
        parts.append(_t(loc, "connected_analytics_live"))
    return "\n\n".join(parts)


def _analytics_reply(snapshot: ProductSnapshot, loc: str) -> str:
    state = snapshot.analytics_state
    if state == "coming_soon":
        return _t(loc, "analytics_coming_soon", body=snapshot.analytics_body)
    if not snapshot.website_owned and not snapshot.shop_owned:
        return _t(loc, "analytics_need_product_first")
    if state == "not_connected":
        return _t(
            loc,
            "analytics_not_connected",
            title=snapshot.analytics_title or _t(loc, "analytics_default_title"),
            body=snapshot.analytics_body or _t(loc, "analytics_default_body"),
            hint=snapshot.analytics_hint or _t(loc, "analytics_default_hint"),
        )
    if state == "connected_no_data":
        return _t(loc, "analytics_no_data_yet", hint=snapshot.analytics_hint)
    # connected_with_data — cite only known metric ids, no invented values
    ids = ", ".join(snapshot.metric_ids) if snapshot.metric_ids else _t(loc, "no_metrics_yet")
    return _t(loc, "analytics_with_data", metrics=ids, hint=snapshot.analytics_hint)


def _next_steps_reply(snapshot: ProductSnapshot, loc: str) -> str:
    steps: list[str] = []
    if not snapshot.website_owned:
        steps.append(_t(loc, "step_add_website"))
    elif snapshot.analytics_state == "not_connected":
        steps.append(_t(loc, "step_connect_analytics"))
    if snapshot.website_owned and not snapshot.shop_owned:
        steps.append(_t(loc, "step_consider_shop"))
    if snapshot.website_owned and not snapshot.ai_owned:
        steps.append(_t(loc, "step_consider_ai"))
    if snapshot.website_owned:
        steps.append(_t(loc, "step_improve_site"))
    if snapshot.niche:
        steps.append(_t(loc, "step_local_seo", niche=snapshot.niche))
    if not steps:
        steps.append(_t(loc, "step_review_products"))
    intro = _t(loc, "next_steps_intro")
    return intro + "\n\n" + "\n".join(f"• {s}" for s in steps[:4])


def _unknown_reply(message: str, snapshot: ProductSnapshot, loc: str) -> tuple[str, str | None]:
    clarify = _t(loc, "clarify_question")
    reply = _t(loc, "unknown_preface", company=snapshot.company_name or _t(loc, "your_business"))
    return reply, clarify


def _t(loc: str, key: str, **kwargs: str) -> str:
    table: dict[str, dict[str, str]] = {
        "your_business": {
            "de": "Ihr Unternehmen",
            "ru": "ваш бизнес",
            "en": "your business",
        },
        "welcome_empty": {
            "de": "{greeting}\n\nIch sehe bei {company} noch keine aktiven Virtus-Produkte. Unter „Meine Produkte“ können Sie Website, Shop oder AI Assistant hinzufügen.",
            "ru": "Здравствуйте! Я Vector, ваш Business Assistant.\n\nУ {company} пока нет активных продуктов Virtus Core. В разделе «Мои продукты» можно добавить сайт, магазин или AI Assistant.",
            "en": "Hello! I'm Vector, your Business Assistant.\n\nI don't see active Virtus products for {company} yet. Open My Products to add Website, Shop, or AI Assistant.",
        },
        "welcome_active": {
            "de": "Bei {company} ist aktiv: {active}.",
            "ru": "У {company} сейчас активно: {active}.",
            "en": "For {company}, these are active: {active}.",
        },
        "welcome_analytics_not_connected": {
            "de": "Analytics ist noch nicht verbunden. Wenn Sie möchten, erkläre ich, welche echten Kennzahlen Sie nach dem Verbinden sehen — ohne erfundene Besucherzahlen.",
            "ru": "Analytics ещё не подключён. Могу объяснить, какие реальные показатели появятся после подключения — без выдуманных посещений.",
            "en": "Analytics is not connected yet. I can explain which real metrics you'll see after connecting — no invented visitor numbers.",
        },
        "welcome_analytics_coming_soon": {
            "de": "Das Analytics-Modul ist derzeit Coming Soon — ich zeige keine Beispieldaten.",
            "ru": "Модуль Analytics пока Coming Soon — я не показываю демо-цифры.",
            "en": "The Analytics module is Coming Soon — I won't show sample data.",
        },
        "welcome_inactive": {
            "de": "Noch nicht verbunden: {inactive}.",
            "ru": "Пока не подключено: {inactive}.",
            "en": "Not connected yet: {inactive}.",
        },
        "connected_intro": {
            "de": "Basierend auf Ihrem Virtus-Core-Konto:",
            "ru": "По данным вашего аккаунта Virtus Core:",
            "en": "Based on your Virtus Core account:",
        },
        "connected_active": {
            "de": "Aktiv: {items}.",
            "ru": "Активно: {items}.",
            "en": "Active: {items}.",
        },
        "connected_inactive": {
            "de": "Noch nicht aktiviert: {items}.",
            "ru": "Ещё не активировано: {items}.",
            "en": "Not activated yet: {items}.",
        },
        "connected_none": {
            "de": "Ich sehe noch keine aktiven Produkte. Starten Sie unter „Meine Produkte“ mit Website oder Shop.",
            "ru": "Активных продуктов пока нет. Начните в «Мои продукты» — сайт или магазин.",
            "en": "No active products yet. Start under My Products with Website or Shop.",
        },
        "connected_analytics_note": {
            "de": "Analytics: noch nicht verbunden — keine Besucher-Grafiken, bis echte Quellen angebunden sind.",
            "ru": "Analytics: не подключён — графиков посещений не будет, пока не подключены реальные источники.",
            "en": "Analytics: not connected — no visitor charts until real sources are linked.",
        },
        "connected_analytics_live": {
            "de": "Analytics: verbunden — Kennzahlen stammen nur aus angebundenen Quellen.",
            "ru": "Analytics: подключён — показатели только из подключённых источников.",
            "en": "Analytics: connected — metrics come only from linked sources.",
        },
        "analytics_need_product_first": {
            "de": "Analytics lohnt sich, sobald Website oder Shop aktiv ist. Aktuell fehlt noch ein Basisprodukt.",
            "ru": "Analytics имеет смысл, когда активен сайт или магазин. Сейчас базового продукта ещё нет.",
            "en": "Analytics makes sense once Website or Shop is active. You don't have a base product yet.",
        },
        "analytics_not_connected": {
            "de": "{title}\n\n{body}\n\n{hint}",
            "ru": "{title}\n\n{body}\n\n{hint}",
            "en": "{title}\n\n{body}\n\n{hint}",
        },
        "analytics_default_title": {
            "de": "Analytics noch nicht verbunden",
            "ru": "Analytics ещё не подключён",
            "en": "Analytics not connected yet",
        },
        "analytics_default_body": {
            "de": "Nach dem Verbinden sehen Sie echte Kennzahlen aus Shop-Bestellungen und Inbox — keine synthetischen Besucher.",
            "ru": "После подключения вы увидите реальные метрики из заказов магазина и Inbox — без синтетических посетителей.",
            "en": "After connecting you'll see real metrics from shop orders and inbox — no synthetic visitors.",
        },
        "analytics_default_hint": {
            "de": "Website kann aktiv sein — ohne Quelle keine Besucher-Grafiken.",
            "ru": "Сайт может быть активен — без источника не будет графиков посещений.",
            "en": "Website can be active — without a source there are no visitor charts.",
        },
        "analytics_coming_soon": {
            "de": "Analytics ist derzeit Coming Soon.\n\n{body}",
            "ru": "Analytics сейчас Coming Soon.\n\n{body}",
            "en": "Analytics is Coming Soon.\n\n{body}",
        },
        "analytics_no_data_yet": {
            "de": "Analytics ist verbunden, aber es liegen noch keine Ereignisse vor. {hint}",
            "ru": "Analytics подключён, но событий пока нет. {hint}",
            "en": "Analytics is connected but there are no events yet. {hint}",
        },
        "analytics_with_data": {
            "de": "Verfügbare Kennzahlen (nur aus Context): {metrics}.\n\n{hint}",
            "ru": "Доступные метрики (только из Context): {metrics}.\n\n{hint}",
            "en": "Available metrics (Context only): {metrics}.\n\n{hint}",
        },
        "no_metrics_yet": {
            "de": "noch keine Metriken",
            "ru": "метрик пока нет",
            "en": "no metrics yet",
        },
        "next_steps_intro": {
            "de": "Mein Vorschlag basierend auf Ihrem aktuellen Stand:",
            "ru": "Мои рекомендации по вашему текущему состоянию:",
            "en": "My suggestions based on your current state:",
        },
        "step_add_website": {
            "de": "Website hinzufügen — Grundlage für Sichtbarkeit und Vertrauen.",
            "ru": "Добавить сайт — основа для видимости и доверия.",
            "en": "Add a Website — foundation for visibility and trust.",
        },
        "step_connect_analytics": {
            "de": "Analytics verbinden, um echte Kennzahlen zu sehen (keine Demo-Besucher).",
            "ru": "Подключить Analytics, чтобы видеть реальные показатели (не демо-посещения).",
            "en": "Connect Analytics to see real metrics (not demo visitors).",
        },
        "step_consider_shop": {
            "de": "Online-Shop prüfen, wenn Sie Produkte direkt verkaufen möchten.",
            "ru": "Рассмотреть интернет-магазин, если хотите продавать товары онлайн.",
            "en": "Consider Online Shop if you want to sell products online.",
        },
        "step_consider_ai": {
            "de": "AI Assistant hinzufügen für 24/7-Anfragen auf Website und Telegram.",
            "ru": "Добавить AI Assistant для ответов 24/7 на сайте и в Telegram.",
            "en": "Add AI Assistant for 24/7 replies on website and Telegram.",
        },
        "step_improve_site": {
            "de": "Website-Inhalte und CTA schärfen — stärkerer erster Eindruck.",
            "ru": "Улучшить контент и CTA на сайте — сильнее первое впечатление.",
            "en": "Sharpen website content and CTA — stronger first impression.",
        },
        "step_local_seo": {
            "de": "Lokales SEO für Ihre Nische ({niche}) — Google-Sichtbarkeit in der Region.",
            "ru": "Локальное SEO для ниши ({niche}) — видимость в Google в регионе.",
            "en": "Local SEO for your niche ({niche}) — regional Google visibility.",
        },
        "step_review_products": {
            "de": "Meine Produkte öffnen und nächstes Modul wählen.",
            "ru": "Открыть «Мои продукты» и выбрать следующий модуль.",
            "en": "Open My Products and pick the next module.",
        },
        "unknown_preface": {
            "de": "Zu „{company}“ habe ich dazu noch keine sicheren Daten im Context. Ich antworte nur aus verifizierten Virtus-Daten.",
            "ru": "По «{company}» у меня пока нет надёжных данных в Context по этому вопросу. Я отвечаю только из проверенных данных Virtus.",
            "en": "For {company}, I don't have reliable Context data for that yet. I only answer from verified Virtus data.",
        },
        "clarify_question": {
            "de": "Geht es um Ihre Produkte, Analytics, Website oder nächste Schritte?",
            "ru": "Речь о продуктах, Analytics, сайте или следующих шагах?",
            "en": "Is this about your products, Analytics, website, or next steps?",
        },
    }
    template = table.get(key, {}).get(loc) or table.get(key, {}).get("en", key)
    return template.format(**kwargs)


def _maybe_llm_read_reply(
    *,
    message: str,
    brief: dict[str, Any],
    locale: str,
) -> str | None:
    """Optional LLM for unknown intents — skipped when no provider (tests use rules)."""
    try:
        from app.integration.genesis_brain.providers import build_provider_registry

        provider = None
        reg = build_provider_registry()
        for pid in ("groq", "openai", "gemini"):
            p = reg.get(pid)
            if p is not None and p.available():
                provider = p
                break
        if provider is None:
            return None
        system = (
            "You are Vector, Virtus Core Business Assistant. READ ONLY. "
            "Use ONLY facts from CONTEXT JSON. Never invent metrics or apply changes. "
            f"Reply in locale {locale}. Keep under 120 words."
        )
        prompt = (
            f"CONTEXT:\n{json.dumps(brief, ensure_ascii=False)}\n\n"
            f"USER:\n{message}\n\n"
            "Answer as Vector using only CONTEXT facts."
        )
        result = provider.chat(
            system=system,
            messages=[{"role": "user", "content": prompt}],
        )
        text = (getattr(result, "answer", None) or "").strip()
        return text or None
    except Exception:
        return None


class CompanionReadService:
    """B4.2 READ turns — tenant-safe Context → reply (rules + optional LLM)."""

    def __init__(
        self,
        memory_dir: Any,
        *,
        sales: Any | None = None,
        llm_enabled: bool = True,
    ) -> None:
        from pathlib import Path

        self._context = CompanionContextService(Path(memory_dir), sales=sales)
        self._llm_enabled = llm_enabled

    def turn(
        self,
        *,
        auth_customer_id: str,
        auth_email: str | None = None,
        me: dict[str, Any] | None = None,
        message: str,
        page_path: str | None = None,
        period: str = "30d",
        requested_customer_id: str | None = None,
        ui_locale: str | None = None,
    ) -> dict[str, Any]:
        session = self._context.load_for_session(
            auth_customer_id=auth_customer_id,
            auth_email=auth_email,
            me=me,
            period=period,
            page_path=page_path,
            requested_customer_id=requested_customer_id,
        )
        ctx = session.get("context") or {}
        snapshot = snapshot_from_context(ctx)
        intent = detect_read_intent(message)
        if message.strip() in _WELCOME_TRIGGERS:
            locale = "de"
        else:
            locale = resolve_response_locale(user_message=message, ui_locale=ui_locale)
        brief = build_context_brief(snapshot)

        llm_used = False
        reply, clarify = compose_read_reply(
            message=message,
            snapshot=snapshot,
            intent=intent,
            locale=locale,
            location=str(session.get("location") or "dashboard"),
        )

        if self._llm_enabled and intent == "unknown":
            llm_text = _maybe_llm_read_reply(message=message, brief=brief, locale=locale)
            if llm_text:
                reply = llm_text
                clarify = None
                llm_used = True

        reply = apply_language_constitution(
            reply,
            user_message=message if message.strip() not in _WELCOME_TRIGGERS else "Guten Tag",
            ui_locale=ui_locale or "de",
        )

        return {
            "ok": True,
            "engine": B4_ENGINE,
            "slice": B4_2_SLICE,
            "assistant": ASSISTANT_NAME,
            "entry_surface": ENTRY_SURFACE,
            "intent": "read",
            "read_intent": intent,
            "mode": "read",
            "reply": reply,
            "clarify_question": clarify,
            "customer_id": session.get("customer_id"),
            "location": session.get("location"),
            "context_ref": session.get("context_ref"),
            "context_brief": brief,
            "llm_used": llm_used,
            "llm": llm_used,
            "research": False,
            "action": False,
            "modes_enabled": ["context_read", "read_conversation"],
            "honesty": (
                "READ-only Vector. Facts from Client Context only. "
                "No ACTION, Web Research, or invented metrics."
            ),
        }
