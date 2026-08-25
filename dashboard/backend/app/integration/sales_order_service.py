"""Sprint 1 — Genesis Sales: client orders and pricing (no payment gateway yet)."""

from __future__ import annotations

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.integration.commerce_engine import (
    resolve_checkout_market,
    resolve_checkout_packages,
    resolve_final_offer,
)
from app.integration.product_line import (
    BRAND_NAME,
    SERVICE_WEBSITE,
    project_awaiting_payment_message,
    project_client_current_step,
    project_client_next_step,
    project_client_timeline,
    project_launch_deliverables,
    project_order_created_message,
    service_label_ru,
)
from app.integration.client_review_service import new_review_token
from app.schemas import FactoryIntentRequest

logger = logging.getLogger(__name__)


def _normalize_order_brand_style(raw: object) -> str:
    from app.factory.brand_style import normalize_brand_style

    return normalize_brand_style(str(raw or ""))


# Ads-ready: Telegram replies are live; website chat embed comes later.
_BOT_CHANNELS_AVAILABLE = frozenset({"telegram"})
_BOT_CHANNELS_COMING_SOON = frozenset(
    {"website_chat", "whatsapp", "instagram", "facebook_messenger"}
)
_BOT_CAPABILITIES = frozenset(
    {
        "consult",
        "faq",
        "leads",
        "booking",
        "handoff",
        "always_on",
    }
)
_BOT_EXTRAS = frozenset(
    {
        "ai_enabled",
        "multilingual",
        "company_training",
        "website_integration",
    }
)
_BOT_KNOWLEDGE_SOURCES = frozenset(
    {
        "website",
        "pdf",
        "faq",
        "word",
        "manual_text",
        "later",
    }
)
_BOT_HANDOFF_RULES = frozenset(
    {
        "when_asks_manager",
        "when_unknown",
        "after_lead",
        "never",
    }
)
_BOT_LANGUAGES = frozenset({"de", "ru", "en", "uk", "other"})

# Legacy map kept for compatibility; channel addons are not billed (tier = AI-bot count).
_BOT_CHANNEL_ADDON_SETUP_EUR: dict[str, int] = {
    "telegram": 0,
    "website_chat": 0,
    "whatsapp": 0,
    "instagram": 0,
    "facebook_messenger": 0,
}


def bot_channel_addon_quote(channels: list[str]) -> dict:
    """Channels are not a tier limit — all selected channels are included (0 € addon)."""
    available = [c for c in channels if c in _BOT_CHANNELS_AVAILABLE]
    interest = [c for c in channels if c in _BOT_CHANNELS_COMING_SOON]
    lines = [
        {"channel": ch, "setup_eur": 0, "status": "included"} for ch in available
    ] + [
        {"channel": ch, "setup_eur": 0, "status": "interest"} for ch in interest
    ]
    return {
        "included_channels": available,
        "addon_channels": [],
        "addon_setup_total_eur": 0,
        "lines": lines,
        "expandable": True,
        "note_ru": (
            "Каналы не ограничивают тариф. Лимит пакета — число независимых AI-ботов. "
            "Подключение своих аккаунтов — после оплаты в личном кабинете."
        ),
    }


def _normalize_bot_config(raw: object) -> dict:
    """Bot order wizard payload — only available channels are orderable now."""
    data = raw if isinstance(raw, dict) else {}
    channels_in = data.get("channels") or []
    if isinstance(channels_in, str):
        channels_in = [x.strip() for x in channels_in.split(",") if x.strip()]
    channels: list[str] = []
    interest_from_channels: list[str] = []
    for ch in channels_in:
        key = str(ch).strip().lower()
        if key in _BOT_CHANNELS_AVAILABLE and key not in channels:
            channels.append(key)
        elif key in _BOT_CHANNELS_COMING_SOON and key not in interest_from_channels:
            interest_from_channels.append(key)
    if not channels:
        channels = ["telegram"]

    caps_in = data.get("capabilities") or []
    if isinstance(caps_in, str):
        caps_in = [x.strip() for x in caps_in.split(",") if x.strip()]
    capabilities = [
        str(c).strip().lower()
        for c in caps_in
        if str(c).strip().lower() in _BOT_CAPABILITIES
    ][:12]

    extras_in = data.get("extras") or []
    if isinstance(extras_in, str):
        extras_in = [x.strip() for x in extras_in.split(",") if x.strip()]
    extras = [
        str(e).strip().lower()
        for e in extras_in
        if str(e).strip().lower() in _BOT_EXTRAS
    ][:12]

    knowledge_in = data.get("knowledge_sources") or []
    if isinstance(knowledge_in, str):
        knowledge_in = [x.strip() for x in knowledge_in.split(",") if x.strip()]
    knowledge = [
        str(k).strip().lower()
        for k in knowledge_in
        if str(k).strip().lower() in _BOT_KNOWLEDGE_SOURCES
    ][:8]
    if not knowledge:
        knowledge = ["later"]
    if "later" in knowledge and len(knowledge) > 1:
        knowledge = [k for k in knowledge if k != "later"]

    handoff_in = data.get("handoff_rules") or []
    if isinstance(handoff_in, str):
        handoff_in = [x.strip() for x in handoff_in.split(",") if x.strip()]
    handoff = [
        str(h).strip().lower()
        for h in handoff_in
        if str(h).strip().lower() in _BOT_HANDOFF_RULES
    ][:6]
    if "never" in handoff and len(handoff) > 1:
        handoff = ["never"]
    if not handoff:
        handoff = ["when_asks_manager", "when_unknown"]

    langs_in = data.get("languages") or []
    if isinstance(langs_in, str):
        langs_in = [x.strip() for x in langs_in.split(",") if x.strip()]
    languages = [
        str(lang).strip().lower()
        for lang in langs_in
        if str(lang).strip().lower() in _BOT_LANGUAGES
    ][:8]
    legacy = str(data.get("reply_language") or "").strip().lower()
    if legacy in _BOT_LANGUAGES and legacy not in languages:
        languages.insert(0, legacy)
    if not languages:
        languages = ["de"]

    channel_quote = bot_channel_addon_quote(channels)
    tone = str(data.get("tone") or "").strip().lower()[:40] or None
    bot_display_name = str(data.get("bot_display_name") or data.get("bot_name") or "").strip()[:80] or None
    faq_text = str(data.get("faq") or data.get("faq_text") or "").strip()[:8000] or None
    ai_instructions = str(data.get("ai_instructions") or data.get("instructions") or "").strip()[:8000] or None

    return {
        "channels": channels,
        "channels_coming_soon_requested": (
            list(
                dict.fromkeys(
                    [
                        *[
                            str(c).strip().lower()
                            for c in (data.get("channels_interest") or [])
                            if str(c).strip().lower() in _BOT_CHANNELS_COMING_SOON
                        ],
                        *interest_from_channels,
                    ]
                )
            )[:6]
        ),
        "capabilities": capabilities,
        "extras": extras,
        "knowledge_sources": knowledge,
        "handoff_rules": handoff,
        "languages": languages,
        "activity": str(data.get("activity") or "").strip()[:200] or None,
        "country": str(data.get("country") or "").strip()[:80] or None,
        "reply_language": languages[0],
        "tone": tone,
        "bot_display_name": bot_display_name,
        "faq": faq_text,
        "ai_instructions": ai_instructions,
        "channel_pricing": channel_quote,
        "expandable_channels": True,
        "add_channel_path": "/client/bots?action=connect",
        "note_ru": (
            "AI Business Bot — цифровой сотрудник. Лимит тарифа — число AI-ботов, "
            "не каналов. После оплаты подключите свои аккаунты в личном кабинете."
        ),
    }


# Post-ZIP handoff (Assisted Deployment) — never store host passwords.
DEPLOYMENT_PREFERENCES = frozenset({"unset", "zip_only", "assisted"})
HOSTING_PROVIDERS = frozenset(
    {"ionos", "hetzner", "cloudflare_pages", "vercel", "other"}
)

_PACKAGES = {
    # Public Website ladder — must match /site (299 / 599 / 999)
    "basic": {
        "id": "basic",
        "name": "Website Basic",
        "price_eur": 299,
        "commerce_mode": "standalone",
        "tagline": "Moderner Website-Start — fertig für Ihre Branche, ohne Client-Panel",
        "included_summary": (
            "responsive Website, Kontakt & Legal, SEO-Grundlage, Social/Kontakt — "
            "kein Virtus Workspace (Änderungen über Auftrag/Support)"
        ),
        "deliverables": [
            "Fertige Website für Ihre Branche",
            "Responsive + Mobile",
            "Kontaktformular & Legal-Seiten",
            "SEO-Grundlage",
            "Standard-Medien & Kontakte",
            "Übergabe als fertiges Projekt",
            "Keine Virtus-Verwaltung",
        ],
    },
    "business": {
        "id": "business",
        "name": "Website Business",
        "price_eur": 599,
        "commerce_mode": "standalone",
        "tagline": "Website + Virtus Workspace — Inhalte und Medien selbst steuern",
        "included_summary": (
            "alles aus Basic plus Virtus Client Workspace: Texte, Medien, Seiten, "
            "Formulare, Analytics, Kontakte/Social, Version/Restore wo verfügbar"
        ),
        "deliverables": [
            "Alles aus Basic",
            "Virtus Client Workspace",
            "Inhalte & Texte bearbeiten",
            "Bilder / Medien ersetzen",
            "Seiten & Formulare",
            "Analytics-Grundlage",
            "Kontakte & Social Links",
            "Versionen / Restore (wo implementiert)",
        ],
    },
    "premium": {
        "id": "premium",
        "name": "Website Premium",
        "price_eur": 999,
        "commerce_mode": "connected",
        "tagline": "Premium Website — Workspace + Cinematic Creative Experience",
        "included_summary": (
            "alles aus Business plus Premium Art Direction, Cinematic Scroll, "
            "advanced Motion/Media, erweiterte Steuerung und Analytics"
        ),
        "deliverables": [
            "Alles aus Business",
            "Premium Art Direction",
            "Cinematic Scroll Experience (inkl.)",
            "Niche Storytelling & Motion",
            "Cinematic Media",
            "Erweiterte Content-Kontrolle",
            "Erweiterte Analytics",
            "Virtus Workspace + Premium Creative Controls",
        ],
    },
    # API aliases (old Standalone / Connected wording) → Business / Premium
    "standalone": {
        "id": "standalone",
        "name": "Website Business",
        "price_eur": 599,
        "commerce_mode": "standalone",
        "alias_of": "business",
        "tagline": "Alias — Website Business",
        "included_summary": "Alias of Website Business",
        "deliverables": ["See Website Business"],
    },
    "connected": {
        "id": "connected",
        "name": "Website Premium",
        "price_eur": 999,
        "commerce_mode": "connected",
        "alias_of": "premium",
        "tagline": "Alias — Website Premium",
        "included_summary": "Alias of Website Premium",
        "deliverables": ["See Website Premium"],
    },
    # Repair MVP — operator delivery after payment (no auto CMS surgery)
    "repair_lite": {
        "id": "repair_lite",
        "name": "Website Repair Lite",
        "price_eur": 199,
        "product_kind": "repair",
        "tagline": "Точечный ремонт по отчёту анализа",
        "included_summary": (
            "ремонт по отчёту Website Analysis, список правок, статус в кабинете; "
            "выполняет оператор Virtus Core"
        ),
        "deliverables": [
            "Ремонт по вашему отчёту Website Analysis",
            "Список выполненных и оставшихся пунктов",
            "Статус заказа в клиентском кабинете",
            "Сопровождение Vector до сдачи",
            "Без автоматического вмешательства в чужой CMS без вашего доступа",
        ],
    },
    "repair_standard": {
        "id": "repair_standard",
        "name": "Website Repair Standard",
        "price_eur": 349,
        "product_kind": "repair",
        "tagline": "Расширенный ремонт по отчёту",
        "included_summary": (
            "стандартный объём ремонта по анализу, отчёт до/после, кабинет; оператор Virtus Core"
        ),
        "deliverables": [
            "Расширенный ремонт по отчёту анализа",
            "Краткий before/after для клиента",
            "Статус и файлы в кабинете",
            "Сопровождение Vector",
        ],
    },
    "repair_complete": {
        "id": "repair_complete",
        "name": "Website Repair Complete",
        "price_eur": 499,
        "product_kind": "repair",
        "tagline": "Максимальный ремонт; при высокой цене часто выгоднее новый сайт",
        "included_summary": (
            "полный пакет ремонта по анализу или честная рекомендация нового сайта"
        ),
        "deliverables": [
            "Полный объём согласованных правок по отчёту",
            "Before/after и остаточные рекомендации",
            "Кабинет клиента + Vector",
        ],
    },
    # G2.X — standalone add-ons (orderable without buying a website)
    "ai_website_analysis": {
        "id": "ai_website_analysis",
        "name": "AI Website Analysis",
        "price_eur": 149,
        "product_kind": "addon",
        "tagline": "Анализ сайта с понятным отчётом",
        "included_summary": "AI-отчёт по сайту, приоритеты улучшений, рекомендации ремонта или нового сайта",
        "deliverables": [
            "Отчёт по безопасности, мобильной версии и скорости",
            "Приоритетный список улучшений",
            "Рекомендация: ремонт vs новый сайт",
        ],
        "eta_days": "1–3",
    },
    "seo_audit": {
        "id": "seo_audit",
        "name": "SEO Audit",
        "price_eur": 249,
        "product_kind": "addon",
        "tagline": "SEO-аудит для локального бизнеса",
        "included_summary": "техническое SEO, мета-теги, локальная видимость, план действий",
        "deliverables": [
            "Технический SEO-чек",
            "Мета / заголовки / структура",
            "План приоритетных правок",
        ],
        "eta_days": "2–4",
    },
    "speed_optimization": {
        "id": "speed_optimization",
        "name": "Speed Optimization",
        "price_eur": 199,
        "product_kind": "addon",
        "tagline": "Ускорение загрузки сайта",
        "included_summary": "изображения, кэш, критические правки скорости",
        "deliverables": [
            "Измерение до/после",
            "Оптимизация изображений и базового кэша",
            "Список остаточных улучшений",
        ],
        "eta_days": "2–5",
    },
    "security_check": {
        "id": "security_check",
        "name": "Security Check",
        "price_eur": 299,
        "product_kind": "addon",
        "tagline": "Проверка безопасности сайта",
        "included_summary": "HTTPS, формы, уязвимости, отчёт с приоритетами",
        "deliverables": [
            "Проверка HTTPS и базовых уязвимостей",
            "Проверка форм и контактов",
            "Отчёт с приоритетами",
        ],
        "eta_days": "1–3",
    },
    "google_business_setup": {
        "id": "google_business_setup",
        "name": "Google Business Profile Setup",
        "price_eur": 149,
        "product_kind": "addon",
        "tagline": "Настройка Google Business Profile",
        "included_summary": "карточка, категории, фото, часы работы, базовые посты",
        "deliverables": [
            "Настройка / восстановление профиля",
            "Категории, часы, контакты, фото",
            "Краткая инструкция для владельца",
        ],
        "eta_days": "3–7",
    },
    "website_migration": {
        "id": "website_migration",
        "name": "Website Migration",
        "price_eur": 299,
        "product_kind": "addon",
        "tagline": "Перенос сайта на новый хостинг",
        "included_summary": "перенос файлов/DNS-помощь, проверка после миграции",
        "deliverables": [
            "План миграции",
            "Перенос и проверка доступности",
            "Краткий отчёт после переноса",
        ],
        "eta_days": "3–10",
        "from_price": True,
    },
    "website_repair": {
        "id": "website_repair",
        "name": "Website Repair",
        "price_eur": 199,
        "product_kind": "addon",
        "tagline": "Ремонт существующего сайта",
        "included_summary": "старт с анализа или сразу repair lite — без покупки нового лендинга",
        "deliverables": [
            "Согласованный объём ремонта",
            "Статус в кабинете",
            "Сопровождение Vector",
        ],
        "eta_days": "2–5",
    },
    "reputation_audit": {
        "id": "reputation_audit",
        "name": "Reputation Audit",
        "price_eur": 149,
        "product_kind": "addon",
        "tagline": "Аудит репутации в интернете",
        "included_summary": "Google Reviews, карты, упоминания, рекомендации",
        "deliverables": [
            "Обзор отзывов и карт",
            "Список упоминаний",
            "План улучшений репутации",
        ],
        "eta_days": "1–2",
    },
    "ecommerce_shop": {
        "id": "ecommerce_shop",
        "name": "AI Store by Virtus Core",
        "price_eur": 799,
        "product_kind": "shop",
        "tagline": "AI Store — интернет-магазин под ваш бизнес",
        "included_summary": "анкета, кабинет, очередь Factory — от 799 €",
        "deliverables": [
            "Бриф магазина в кабинете",
            "Статусы Создаётся → Генерируется → Готов",
            "Хуки Factory (сборка магазина — R2)",
        ],
        "eta_days": "7–21",
        "billing": "one_time",
        "from_price": True,
    },
    "ai_chatbot": {
        "id": "ai_chatbot",
        "name": "AI Chatbot",
        "price_eur": 499,
        "product_kind": "addon",
        "tagline": "AI чат-бот для сайта и мессенджеров",
        "included_summary": "настройка AI-сотрудника — от 499 €",
        "deliverables": [
            "Конфигурация бота",
            "Подключение каналов",
            "Кабинет + статус",
        ],
        "eta_days": "3–10",
        "from_price": True,
    },
    "business_automation": {
        "id": "business_automation",
        "name": "Business Automation",
        "price_eur": 399,
        "product_kind": "addon",
        "tagline": "Автоматизация бизнес-процессов",
        "included_summary": "workflow для малого бизнеса — от 399 €",
        "deliverables": [
            "Карта процессов",
            "Автоматизации под задачу",
            "Статус в кабинете",
        ],
        "eta_days": "5–14",
        "from_price": True,
    },
    "ai_social_content": {
        "id": "ai_social_content",
        "name": "AI Social Content",
        "price_eur": 199,
        "product_kind": "addon",
        "tagline": "AI-контент для соцсетей (месяц)",
        "included_summary": "Reels, TikTok, Instagram, Facebook — первый месяц",
        "deliverables": [
            "Пакет контента за месяц",
            "AI-озвучка / дизайн по плану",
            "Статус в кабинете",
        ],
        "eta_days": "ongoing",
        "billing": "monthly",
        "from_price": True,
    },
    "site_maintenance": {
        "id": "site_maintenance",
        "name": "Website Maintenance",
        "price_eur": 49,
        "product_kind": "addon",
        "tagline": "Ежемесячная поддержка сайта",
        "included_summary": "обновления, бэкапы, мониторинг — первый месяц",
        "deliverables": [
            "План поддержки",
            "Резервные копии / мониторинг",
            "Статус в кабинете",
        ],
        "eta_days": "ongoing",
        "billing": "monthly",
        "from_price": True,
    },
    "ai_seo_monitoring": {
        "id": "ai_seo_monitoring",
        "name": "AI SEO Monitoring",
        "price_eur": 29,
        "product_kind": "addon",
        "tagline": "Мониторинг SEO (месяц)",
        "included_summary": "позиции и рекомендации — первый месяц",
        "deliverables": [
            "Снимок позиций",
            "Рекомендации улучшений",
            "Статус в кабинете",
        ],
        "eta_days": "ongoing",
        "billing": "monthly",
        "from_price": True,
    },
}

_REPAIR_PACKAGE_IDS = frozenset({"repair_lite", "repair_standard", "repair_complete"})
_ADDON_PACKAGE_IDS = frozenset(
    {
        "ai_website_analysis",
        "seo_audit",
        "speed_optimization",
        "security_check",
        "google_business_setup",
        "website_migration",
        "website_repair",
        "reputation_audit",
        "ecommerce_shop",
        "ai_chatbot",
        "business_automation",
        "ai_social_content",
        "site_maintenance",
        "ai_seo_monitoring",
    }
)


def package_included_summary(package_id: str | None) -> str:
    """One-line Layer A canon for ZIP / next-steps emails."""
    pid = (package_id or "basic").strip().lower()
    if pid.startswith("bot_"):
        from app.integration.pricing_engine import resolve_bot_offer

        bot = resolve_bot_offer(pid, "DE")
        return (
            f"AI bot setup {bot.setup_label} + {bot.monthly_label}/mo; "
            "channels from order; expandable later"
        )
    row = _PACKAGES.get(pid) or _PACKAGES["basic"]
    return str(row.get("included_summary") or "")


def package_display_name(package_id: str | None) -> str:
    pid = (package_id or "basic").strip().lower()
    if pid.startswith("bot_"):
        from app.integration.pricing_engine import resolve_bot_offer

        return resolve_bot_offer(pid, "DE").name
    row = _PACKAGES.get(pid) or _PACKAGES["basic"]
    return str(row.get("name") or "Landing Basic")



class SalesOrderService:
    def __init__(self, memory_dir: Path, factory_intent: object) -> None:
        self._memory = memory_dir
        self._factory_intent = factory_intent
        self._memory.mkdir(parents=True, exist_ok=True)

    def checkout_packages(
        self,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> dict:
        import os

        resolved = resolve_checkout_market(
            market_code=market_code,
            city=city,
            visitor_id=visitor_id,
            memory_dir=self._memory,
            extra_text=extra_text,
        )
        # Public website packages — Basic / Business / Premium (same as /site)
        site_ids = ("basic", "business", "premium")
        deliverables = {k: _PACKAGES[k]["deliverables"] for k in site_ids}
        names = {k: _PACKAGES[k]["name"] for k in site_ids}
        result = resolve_checkout_packages(
            resolved,
            deliverables_by_id=deliverables,
            names_by_id=names,
        )
        pkgs = list(result.get("packages") or [])
        enriched = []
        for p in pkgs:
            pid = str(p.get("id") or "")
            row = _PACKAGES.get(pid) or {}
            enriched.append(
                {
                    **p,
                    "commerce_mode": row.get("commerce_mode") or pid,
                    "monthly_eur": row.get("monthly_eur") or 0,
                    "tagline": row.get("tagline") or p.get("tagline") or "",
                    "virtus_workspace": pid in ("business", "premium"),
                    "cinematic_included": pid == "premium",
                }
            )
        result["packages"] = enriched
        result["commerce_model"] = "basic_business_premium"
        result["canon"] = "Website package ladder"
        # Stripe Smoke €1 — checkout via API when GENESIS_STRIPE_SMOKE=1.
        # Listed in UI only when GENESIS_SHOW_SMOKE_PACKAGE=1 (dev/debug). Never for normal buyers.
        if (
            os.getenv("GENESIS_STRIPE_SMOKE", "").strip() == "1"
            and os.getenv("GENESIS_SHOW_SMOKE_PACKAGE", "").strip() == "1"
        ):
            smoke_pkg, _ = self._package_offer("smoke")
            result = {
                **result,
                "packages": [
                    *result["packages"],
                    {
                        "id": "smoke",
                        "name": smoke_pkg["name"],
                        "price_eur": float(smoke_pkg["price_eur"]),
                        "currency": smoke_pkg["currency"],
                        "symbol": smoke_pkg["symbol"],
                        "market_code": smoke_pkg["market_code"],
                        "price_label": smoke_pkg["price_label"],
                        "deliverables": list(smoke_pkg.get("deliverables") or _PACKAGES["basic"]["deliverables"]),
                    },
                ],
            }
        return result

    def packages(
        self,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> list[dict]:
        return self.checkout_packages(
            market_code=market_code,
            visitor_id=visitor_id,
            city=city,
            extra_text=extra_text,
        )["packages"]

    def _package_offer(
        self,
        package_id: str,
        *,
        market_code: str | None = None,
        visitor_id: str | None = None,
        city: str | None = None,
        extra_text: str | None = None,
    ) -> tuple[dict, dict]:
        import os

        from app.integration.market_registry import format_amount, get_market

        pid = str(package_id or "basic").strip().lower()
        # CEO Stripe smoke — €1 live charge. Not listed in public packages.
        if pid == "smoke":
            if os.getenv("GENESIS_STRIPE_SMOKE", "").strip() != "1":
                raise ValueError("smoke_disabled")
            market = get_market("DE")
            package = {
                **_PACKAGES["basic"],
                "id": "smoke",
                "name": "Stripe Smoke €1",
                "price_eur": 1.0,
                "currency": "EUR",
                "symbol": market.symbol,
                "market_code": "DE",
                "price_label": format_amount(1, market.symbol),
            }
            return package, {
                "package_id": "smoke",
                "amount": 1,
                "currency": "EUR",
                "symbol": market.symbol,
                "market_code": "DE",
                "price_label": package["price_label"],
            }

        if pid in _REPAIR_PACKAGE_IDS:
            offer = resolve_final_offer(pid, (market_code or "DE").strip().upper() or "DE")
            base = _PACKAGES[pid]
            package = {
                **base,
                "price_eur": float(offer.amount),
                "currency": offer.currency,
                "symbol": offer.symbol,
                "market_code": offer.market_code,
                "price_label": offer.price_label,
            }
            return package, offer.as_dict()

        if pid in _ADDON_PACKAGE_IDS:
            from app.integration.market_registry import format_amount, get_market

            market = get_market((market_code or "DE").strip().upper() or "DE")
            base = _PACKAGES[pid]
            amount = int(base["price_eur"])
            price_label = format_amount(amount, market.symbol)
            package = {
                **base,
                "price_eur": float(amount),
                "currency": market.currency,
                "symbol": market.symbol,
                "market_code": market.code,
                "price_label": price_label,
            }
            return package, {
                "package_id": pid,
                "amount": amount,
                "currency": market.currency,
                "symbol": market.symbol,
                "market_code": market.code,
                "price_label": price_label,
            }

        from app.integration.pricing_engine import BOT_PACKAGE_IDS, resolve_bot_offer

        if pid in BOT_PACKAGE_IDS or str(pid).startswith("bot_"):
            from app.integration.market_registry import format_amount

            bot = resolve_bot_offer(pid, (market_code or "DE").strip().upper() or "DE")
            setup_label = format_amount(bot.setup_amount, bot.symbol)
            monthly_label = format_amount(bot.monthly_amount, bot.symbol)
            package = {
                "id": bot.package_id,
                "name": bot.name,
                "price_eur": float(bot.setup_amount),
                "currency": bot.currency,
                "symbol": bot.symbol,
                "market_code": bot.market_code,
                "price_label": f"{setup_label} + {monthly_label}/mo",
                "product_kind": "bot",
                "purchase_type": "subscription",
                "setup_amount": bot.setup_amount,
                "monthly_amount": bot.monthly_amount,
                "tagline": "AI Business Bot — separate from website packages",
                "included_summary": (
                    f"AI bot setup ({setup_label}) + monthly ({monthly_label}/mo); "
                    "channels chosen at order; expandable later"
                ),
                "deliverables": [
                    "Bot setup for selected channels (Telegram / Website Chat when available)",
                    "Company knowledge questionnaire after payment",
                    "Client workspace for bot status",
                    f"Monthly plan: {monthly_label}/mo after setup",
                    "Additional channels can be added later without a new website order",
                ],
            }
            return package, {
                "package_id": bot.package_id,
                "amount": bot.setup_amount,
                "currency": bot.currency,
                "symbol": bot.symbol,
                "market_code": bot.market_code,
                "price_label": package["price_label"],
                "setup_amount": bot.setup_amount,
                "monthly_amount": bot.monthly_amount,
                "product_kind": "bot",
            }

        from app.integration.pricing_engine import normalize_package_id

        resolved = resolve_checkout_market(
            market_code=market_code,
            city=city,
            visitor_id=visitor_id,
            memory_dir=self._memory,
            extra_text=extra_text,
        )
        tier = normalize_package_id(pid)
        # Prefer canonical ladder row (basic/business/premium) over alias stubs
        base = _PACKAGES.get(tier) or _PACKAGES["basic"]
        if base.get("alias_of"):
            base = _PACKAGES.get(str(base["alias_of"]), base)
        offer = resolve_final_offer(tier, resolved)
        package = {
            **base,
            "price_eur": float(offer.amount),
            "currency": offer.currency,
            "symbol": offer.symbol,
            "market_code": offer.market_code,
            "price_label": offer.price_label,
        }
        return package, offer.as_dict()

    def create_order(self, payload: dict) -> dict:
        from app.factory.market_delivery import (
            client_status_label,
            factory_locale_context,
        )
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level
        from app.integration.demo_payment import (
            demo_payment_bridge_enabled,
            matches_demo_company_name,
        )
        from app.integration.locale_service import normalize_order_ui_lang

        wants_demo = bool(payload.get("demo")) or str(
            payload.get("payment_mode") or ""
        ).lower() == "demo"
        if wants_demo and not demo_payment_bridge_enabled():
            raise ValueError("demo_payment_disabled")
        # Auto-demo companies still require bridge enabled (never silent in production)
        if matches_demo_company_name(str(payload.get("business_name") or "")) and not demo_payment_bridge_enabled():
            # Still create order, but do not tag as demo when bridge locked
            pass

        package_id = payload.get("package_id") or self._suggest_package(payload)
        package, _offer = self._package_offer(
            package_id,
            market_code=payload.get("market_code"),
            visitor_id=payload.get("visitor_id"),
            city=payload.get("city"),
            extra_text=payload.get("description"),
        )
        motion = normalize_motion_level(str(payload.get("motion_level") or "none"))
        gate = gate_motion_level(motion)
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        project_ctx = self._resolve_project_context(payload.get("visitor_id"))
        service_id = project_ctx["service_id"]
        launch_mode = bool(project_ctx["launch_mode"])
        project_name = project_ctx.get("project_name")
        order_id = f"ord-{uuid.uuid4().hex[:10]}"
        now = datetime.now(timezone.utc).isoformat()
        market_code = str(package.get("market_code", "DE"))
        ui_lang = normalize_order_ui_lang(
            payload.get("ui_lang") or payload.get("locale") or payload.get("language"),
            market_code=market_code,
        )
        client_message = project_awaiting_payment_message(
            launch_mode=launch_mode, ui_lang=ui_lang
        )
        company_website = self._normalize_company_website(payload.get("company_website"))
        site_analysis = self._analyze_company_website(company_website) if company_website else None

        existing_domain = (payload.get("existing_domain") or "").strip() or None
        domain_status = (payload.get("domain_status") or "").strip().lower()
        if domain_status not in ("none", "have_domain", "need_help"):
            if existing_domain or company_website:
                domain_status = "have_domain"
            elif payload.get("needs_domain"):
                domain_status = "need_help"
            else:
                domain_status = "none"
        domain_help_message = None
        if domain_status in ("none", "need_help"):
            domain_help_message = {
                "de": (
                    "Wir können bei der Auswahl und Anbindung einer Domain helfen — "
                    "ohne sofortigen Kaufzwang."
                ),
                "en": (
                    "We can help choose and connect a domain — "
                    "without forcing an immediate purchase."
                ),
                "ru": (
                    "Мы можем помочь с выбором и подключением домена — "
                    "без обязательной покупки сразу."
                ),
                "uk": (
                    "Ми можемо допомогти з вибором і підключенням домену — "
                    "без обов’язкової покупки одразу."
                ),
            }.get(ui_lang) or (
                "We can help choose and connect a domain — "
                "without forcing an immediate purchase."
            )
        effective_needs_domain = domain_status in ("none", "need_help") and not existing_domain

        social_links = {
            "google_business": (payload.get("google_business") or "").strip() or None,
            "instagram": (payload.get("instagram") or "").strip() or None,
            "facebook": (payload.get("facebook") or "").strip() or None,
            "tiktok": (payload.get("tiktok") or "").strip() or None,
            "linkedin": (payload.get("linkedin") or "").strip() or None,
            "youtube": (payload.get("youtube") or "").strip() or None,
            "telegram": (payload.get("telegram") or "").strip() or None,
            "whatsapp": (payload.get("whatsapp") or "").strip() or None,
            "website": company_website,
            "domain": existing_domain,
        }
        social_links = {k: v for k, v in social_links.items() if v}

        material_ids = [
            str(x).strip()
            for x in (payload.get("material_ids") or [])
            if str(x).strip()
        ][:40]
        materials_bundle: dict = {"files": [], "count": 0}
        buyer_insights: dict | None = None
        try:
            from app.integration.order_materials_service import OrderMaterialsService

            mats = OrderMaterialsService(self._memory)
            if material_ids:
                materials_bundle = mats.attach_to_order(order_id, material_ids)
            buyer_insights = mats.build_buyer_insights(
                company_website=company_website,
                domain=existing_domain,
                domain_status=domain_status,
                social=social_links,
                material_ids=material_ids,
                site_analysis=site_analysis,
                niche=(payload.get("niche") or "").strip() or None,
                city=(payload.get("city") or "").strip() or None,
            )
        except Exception as exc:
            logger.warning("order materials/insights skipped: %s", exc)

        locale_ctx = factory_locale_context(
            {"ui_lang": ui_lang, "market_code": market_code, "currency": package.get("currency")},
            market_code,
        )
        # Prefer explicit buyer language over market default when they diverge.
        locale_ctx["language"] = ui_lang
        locale_ctx["locale"] = locale_ctx.get("locale") or f"{ui_lang}_{market_code}"

        product_kind = str(
            package.get("product_kind")
            or (
                "repair"
                if str(package_id).strip().lower() in _REPAIR_PACKAGE_IDS
                else "website"
            )
        )
        bot_config = None
        price_eur = float(package["price_eur"])
        price_label = package.get("price_label", f"{price_eur} €")
        setup_amount = package.get("setup_amount")
        customer_id = (payload.get("customer_id") or "").strip()[:80] or None
        workspace_id = (payload.get("workspace_id") or "").strip()[:80] or None
        # Architecture lock: one lifetime project — upgrades unlock features on same workspace.
        if customer_id and not workspace_id:
            workspace_id = customer_id
        interest_only = bool(payload.get("interest_only")) or str(
            payload.get("description") or ""
        ).lstrip().startswith("[interest]")
        if product_kind == "bot" or str(package_id).startswith("bot_"):
            product_kind = "bot"
            if not customer_id:
                raise ValueError("customer_id_required_for_bot")
            workspace_id = workspace_id or customer_id
            bot_config = _normalize_bot_config(payload.get("bot_config"))
            addon = int(
                (bot_config.get("channel_pricing") or {}).get("addon_setup_total_eur")
                or 0
            )
            if addon > 0:
                price_eur = float(price_eur) + addon
                setup_amount = float(setup_amount or package["price_eur"]) + addon
                sym = package.get("symbol", "€")
                price_label = f"{price_eur:g} {sym}"
                if package.get("monthly_amount") is not None:
                    price_label = (
                        f"{price_eur:g} {sym} + {package['monthly_amount']} {sym}/mo"
                    )

        shop_brief: dict | None = None
        if str(package_id).strip().lower() == "ecommerce_shop" or product_kind == "shop":
            from app.integration.shop_brief import (
                SHOP_PACKAGE_ID,
                brief_summary_line,
                validate_shop_brief,
            )

            product_kind = "shop"
            package_id = SHOP_PACKAGE_ID
            if not interest_only and not customer_id:
                raise ValueError("customer_id_required_for_shop")
            workspace_id = workspace_id or customer_id
            shop_brief = validate_shop_brief(
                payload.get("shop_brief")
                or {
                    "company_name": payload.get("business_name"),
                    "store_name": payload.get("business_name"),
                    "what_is_sold": payload.get("description"),
                    "wishes": payload.get("extra_wishes"),
                }
            )
            # Prefer store name for display when provided.
            if shop_brief.get("store_name"):
                payload = {**payload, "business_name": shop_brief["store_name"]}
            if not str(payload.get("description") or "").strip():
                payload = {
                    **payload,
                    "description": brief_summary_line(shop_brief),
                }

        if interest_only:
            listed_price_label = price_label
            price_eur = 0.0
            price_label = {
                "de": "Interesse — keine Zahlung",
                "en": "Interest — no payment",
                "ru": "Интерес — без оплаты",
                "uk": "Інтерес — без оплати",
            }.get(ui_lang) or "Interest — no payment"
            status = "interest"
            client_message = {
                "de": (
                    f"Interesse für {package['name']} ist gespeichert "
                    f"(Richtpreis {listed_price_label}). Keine Zahlung — "
                    "wir melden uns, wenn die Leistung live ist."
                ),
                "en": (
                    f"Interest in {package['name']} is saved "
                    f"(guide price {listed_price_label}). No payment — "
                    "we will contact you when the service goes live."
                ),
                "ru": (
                    f"Интерес к {package['name']} сохранён "
                    f"(ориентир {listed_price_label}). Оплаты нет — "
                    "свяжемся, когда услуга станет доступна."
                ),
                "uk": (
                    f"Інтерес до {package['name']} збережено "
                    f"(орієнтир {listed_price_label}). Оплати немає — "
                    "напишемо, коли послуга стане доступною."
                ),
            }.get(ui_lang) or (
                f"Interest in {package['name']} is saved. No payment taken."
            )
        else:
            status = "awaiting_payment"

        order = {
            "order_id": order_id,
            "status": status,
            "status_label": client_status_label(
                status, market_code, ui_lang=ui_lang
            ),
            "package_id": package_id,
            "package_name": package["name"],
            "product_kind": product_kind,
            "purchase_type": str(
                payload.get("purchase_type")
                or package.get("purchase_type")
                or "one_time"
            ),
            "bot_config": bot_config,
            "shop_brief": shop_brief,
            "shop_pipeline": None,
            "factory_hook": None,
            "setup_amount": setup_amount,
            "monthly_amount": package.get("monthly_amount"),
            "analysis_case_id": (payload.get("analysis_case_id") or "").strip() or None,
            "customer_id": customer_id,
            "workspace_id": workspace_id,
            "price_eur": price_eur,
            "currency": package.get("currency", "EUR"),
            "symbol": package.get("symbol", "€"),
            "market_code": market_code,
            "ui_lang": ui_lang,
            "language": ui_lang,
            "locale": locale_ctx["locale"],
            "factory_context": locale_ctx,
            "price_label": price_label,
            "interest_only": interest_only,
            "motion_level": motion,
            "cinematic_enabled": False,
            "cinematic_product_id": None,
            "cinematic_price_eur": 0.0,
            "media_budget_eur": 0.0,
            "media_spent_eur": 0.0,
            "media_remaining_eur": 0.0,
            "media_status": "NOT_REQUESTED",
            "media_provider": None,
            "brand_style": _normalize_order_brand_style(payload.get("brand_style")),
            "commerce_mode": payload.get("commerce_mode")
            or package.get("commerce_mode")
            or None,
            "business_interview": payload.get("business_interview")
            if isinstance(payload.get("business_interview"), dict)
            else None,
            "dialogue": (payload.get("dialogue") or "").strip() or None,
            "dream_vision": (payload.get("dream_vision") or "").strip() or None,
            "clarify_answers": payload.get("clarify_answers")
            if isinstance(payload.get("clarify_answers"), dict)
            else None,
            "business_scale": (payload.get("business_scale") or "").strip() or None,
            "why_choose_us": (payload.get("why_choose_us") or payload.get("differentiator") or "").strip()
            or None,
            "who_is_company": (payload.get("who_is_company") or payload.get("about") or "").strip()
            or None,
            "clients_who": (payload.get("clients_who") or "").strip() or None,
            "site_jobs": self._normalize_services_list(payload.get("site_jobs")),
            "wishes": (payload.get("wishes") or payload.get("dream_wishes") or "").strip()
            or None,
            "deliverables": (
                project_launch_deliverables(service_id)
                if launch_mode
                else package["deliverables"]
            ),
            "business_name": payload["business_name"].strip(),
            "description": payload["description"].strip(),
            "city": (payload.get("city") or "").strip(),
            "phone": (payload.get("phone") or "").strip(),
            "whatsapp": (payload.get("whatsapp") or "").strip(),
            "email": (payload.get("email") or "").strip(),
            "needs_logo": bool(payload.get("needs_logo")),
            "needs_domain": bool(effective_needs_domain),
            "domain_status": domain_status,
            "existing_domain": existing_domain,
            "domain_help_message": domain_help_message,
            "extra_wishes": (payload.get("extra_wishes") or "").strip(),
            "company_website": company_website,
            "niche": (payload.get("niche") or "").strip() or None,
            "specialization": (payload.get("specialization") or "").strip() or None,
            "services_list": self._normalize_services_list(payload.get("services_list")),
            "advantages": self._normalize_services_list(
                payload.get("advantages") or payload.get("benefits")
            ),
            "social_links": social_links,
            "materials": materials_bundle,
            "buyer_insights": buyer_insights,
            "site_analysis": site_analysis,
            "project_workspace": {
                "materials": materials_bundle.get("files") or [],
                "analysis": buyer_insights,
                "documents": [],
                "invoices": [],
                "status": status,
            },
            "client_legal": self._client_legal_payload(payload),
            "visitor_id": (payload.get("visitor_id") or "").strip()[:64] or None,
            "service_id": service_id,
            "launch_mode": launch_mode,
            "project_name": project_name,
            "created_at": now,
            "updated_at": now,
            "product_id": (payload.get("product_id") or "").strip() or None,
            "proposal_text": self._proposal_text(package, payload, project_ctx=project_ctx),
            "paid_at": None,
            "payment_provider": None,
            "payment_external_id": None,
            "payment_mode": None,
            "demo": False,
            "is_demo": False,
            "estimated_delivery_at": None,
            "client_status_message": client_message,
            "deployment_preference": "unset",
            "hosting_provider": None,
            "deployment_preference_at": None,
        }
        # Cinematic: included in Premium website / Premium-style shop; else optional +€.
        pkg_norm = str(package_id or "").strip().lower()
        is_shop_order = product_kind == "shop" or pkg_norm == "ecommerce_shop"
        shop_style = str(
            ((payload.get("shop_brief") or {}) if isinstance(payload.get("shop_brief"), dict) else {}).get(
                "style"
            )
            or ""
        ).strip().lower()
        premium_includes_cinematic = pkg_norm in ("premium", "connected") or (
            is_shop_order and shop_style in ("premium", "cinematic", "luxury")
        )
        cinematic_wanted = bool(
            premium_includes_cinematic
            or payload.get("cinematic_enabled")
            or payload.get("cinematic_ai_experience")
            or str(payload.get("cinematic_product_id") or "").strip()
        )
        if cinematic_wanted:
            from app.integration.cinematic_media.budget import attach_cinematic_to_order

            attach_cinematic_to_order(
                order,
                enabled=True,
                product_id=(payload.get("cinematic_product_id") or None),
                is_shop=is_shop_order,
                included_in_package=premium_includes_cinematic,
            )
            price_eur = float(order["price_eur"])
            price_label = order.get("price_label") or price_label

        from app.integration.demo_payment import should_tag_demo_order

        if should_tag_demo_order(payload):
            order["demo"] = True
            order["is_demo"] = True
            order["payment_mode"] = "demo"
            order["demo_banner"] = (
                "Demo Payment — средства не списываются. / "
                "Demo Payment — es wird kein Geld abgebucht. Nur für interne Tests."
            )
        self._save_order(order)
        from app.integration.demo_payment import demo_public_flags

        out = {
            "ok": True,
            "order_id": order_id,
            "message": project_order_created_message(
                service_id,
                launch_mode=launch_mode,
                project_name=project_name or payload["business_name"].strip(),
                ui_lang=ui_lang,
            ),
            "package_id": package_id,
            "package_name": package["name"],
            "product_kind": order.get("product_kind"),
            "price_eur": order.get("price_eur", package["price_eur"]),
            "currency": package.get("currency", "EUR"),
            "symbol": package.get("symbol", "€"),
            "market_code": market_code,
            "ui_lang": ui_lang,
            "locale": locale_ctx["locale"],
            "price_label": order.get("price_label") or package.get("price_label"),
            "motion_level": motion,
            "cinematic_enabled": bool(order.get("cinematic_enabled")),
            "cinematic_price_eur": float(order.get("cinematic_price_eur") or 0),
            "deliverables": order["deliverables"],
            "buyer_insights": buyer_insights,
            "bot_config": order.get("bot_config"),
            "monthly_amount": order.get("monthly_amount"),
        }
        out.update(demo_public_flags(order, ui_lang=ui_lang))
        return out

    def list_orders(self, limit: int = 50) -> list[dict]:
        orders = self._load_all()
        orders.sort(key=lambda o: o.get("created_at", ""), reverse=True)
        return [self._summary(o) for o in orders[: max(1, min(int(limit or 50), 200))]]

    def attach_customer_by_email(self, *, customer_id: str, email: str) -> int:
        """Link *guest* orders (no customer_id yet) to this account by email.

        Never reassign an order that already belongs to another customer_id —
        that caused cross-tenant cabinet leakage (Client A seeing Client B).
        """
        cid = str(customer_id or "").strip()
        em = str(email or "").strip().lower()
        if not cid or not em or "@" not in em:
            return 0
        linked = 0
        for order in self._load_all():
            order_email = str(order.get("email") or "").strip().lower()
            if order_email != em:
                continue
            existing = str(order.get("customer_id") or "").strip()
            if existing == cid:
                continue
            # Only claim true guest rows. Never steal another tenant's order.
            if existing:
                continue
            order["customer_id"] = cid
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)
            linked += 1
        return linked

    @staticmethod
    def _order_is_cabinet_hidden(order: dict) -> bool:
        """Soft-replaced / archived duplicates stay out of the client cabinet."""
        st = str(order.get("status") or "").strip().lower()
        qs = str(order.get("quality_state") or "").strip().upper()
        if st == "superseded" or qs == "ARCHIVED":
            return True
        # Legacy upgrade scripts set boolean `superseded` without status=superseded.
        if order.get("superseded") is True:
            return True
        return False

    def list_orders_for_customer(
        self, *, customer_id: str, email: str | None = None, limit: int = 50
    ) -> list[dict]:
        """Cabinet orders owned by this customer.

        Ownership rule (hard):
        - Include if order.customer_id == customer_id
        - OR guest order (empty customer_id) with matching email
        - Never include another tenant's order just because emails match
        """
        cid = str(customer_id or "").strip()
        em = str(email or "").strip().lower()
        if not cid and not em:
            return []
        matched: list[dict] = []
        for order in self._load_all():
            oid_cid = str(order.get("customer_id") or "").strip()
            oid_email = str(order.get("email") or "").strip().lower()
            if cid and oid_cid == cid:
                matched.append(order)
            elif em and oid_email == em and not oid_cid:
                # Guest checkout awaiting claim — safe to show after login attach.
                matched.append(order)
            # else: email match but foreign customer_id → isolation: skip
        # de-dupe by order_id
        seen: set[str] = set()
        unique: list[dict] = []
        for o in matched:
            oid = str(o.get("order_id") or "")
            if not oid or oid in seen:
                continue
            seen.add(oid)
            unique.append(o)
        unique.sort(key=lambda o: o.get("created_at", ""), reverse=True)
        out: list[dict] = []
        for order in unique:
            if self._order_is_cabinet_hidden(order):
                continue
            try:
                status = self.public_status(str(order["order_id"]))
            except Exception:
                status = self._summary(order)
            out.append(status)
            if len(out) >= limit:
                break
        return out

    def list_pending(self) -> list[dict]:
        return [o for o in self.list_orders(50) if o["status"] == "pending_confirmation"]

    def get_order(self, order_id: str) -> dict | None:
        want = str(order_id or "").strip()
        if not want:
            return None
        want_l = want.lower()
        for order in self._load_all():
            oid = str(order.get("order_id") or "")
            if oid == want or oid.lower() == want_l:
                return order
        return None

    def _store_factory(self):
        from app.factory.store_factory import StoreFactoryService

        return StoreFactoryService(self._memory)

    def _assert_shop_owner(
        self, order_id: str, *, customer_id: str, email: str | None = None
    ) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
            raise ValueError("not_a_shop_order")
        cid = str(customer_id or "").strip()
        em = str(email or "").strip().lower()
        oid_cid = str(order.get("customer_id") or "").strip()
        oid_email = str(order.get("email") or "").strip().lower()
        owns = False
        if cid and oid_cid and oid_cid == cid:
            owns = True
        elif em and oid_email == em and not oid_cid:
            # Guest shop not yet attached — email claim only.
            owns = True
        if not owns:
            raise ValueError("forbidden")
        return order

    def start_shop_pipeline(self, order_id: str) -> dict:
        """AI Store: accepted → preparing → factory generate → published."""
        from app.integration.shop_brief import (
            SHOP_PIPELINE_ACCEPTED,
            SHOP_PIPELINE_PREPARING,
            brief_summary_line,
            shop_pipeline_label,
            validate_shop_brief,
        )
        from app.factory.market_delivery import client_status_label

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
            raise ValueError("not_a_shop_order")

        market = str(order.get("market_code") or "DE")
        ui_lang = str(order.get("ui_lang") or "en")
        now = datetime.now(timezone.utc).isoformat()

        brief_raw = order.get("shop_brief")
        try:
            brief = validate_shop_brief(
                brief_raw
                if isinstance(brief_raw, dict)
                else {
                    "company_name": order.get("business_name"),
                    "store_name": order.get("business_name"),
                    "what_is_sold": order.get("description"),
                }
            )
        except ValueError as exc:
            raise ValueError("shop_brief_invalid") from exc

        order["product_kind"] = "shop"
        order["shop_brief"] = brief
        order["shop_pipeline"] = SHOP_PIPELINE_ACCEPTED
        order["status"] = "paid"
        order["status_label"] = client_status_label("paid", market, ui_lang=ui_lang)
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_ACCEPTED, ui_lang)}. "
            f"{brief_summary_line(brief)}"
        )
        order["updated_at"] = now
        self._save_order(order)

        order["shop_pipeline"] = SHOP_PIPELINE_PREPARING
        order["status"] = "in_production"
        order["status_label"] = client_status_label(
            "in_production", market, ui_lang=ui_lang
        )
        order["factory_hook"] = {
            "status": "queued",
            "queued_at": now,
            "note": "Factory will build your niche storefront from the brief.",
        }
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_PREPARING, ui_lang)}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)

        return self.enqueue_shop_factory(order_id)

    def enqueue_shop_factory(self, order_id: str) -> dict:
        """Generate storefront → quality gate → auto-publish (R2). Idempotent if published."""
        from app.integration.shop_brief import (
            SHOP_PIPELINE_FACTORY_QUEUE,
            SHOP_PIPELINE_GENERATING,
            SHOP_PIPELINE_PUBLISHED,
            SHOP_PIPELINE_QUALITY,
            SHOP_PIPELINE_READY_PUBLISH,
            shop_pipeline_label,
        )
        from app.factory.market_delivery import client_status_label

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
            raise ValueError("not_a_shop_order")

        market = str(order.get("market_code") or "DE")
        ui_lang = str(order.get("ui_lang") or "en")
        now = datetime.now(timezone.utc).isoformat()
        hook = (
            dict(order.get("factory_hook") or {})
            if isinstance(order.get("factory_hook"), dict)
            else {}
        )
        current = str(order.get("shop_pipeline") or "")
        if (
            current == SHOP_PIPELINE_PUBLISHED
            and order.get("product_id")
            and hook.get("status") == "completed"
        ):
            return {
                "ok": True,
                "order": self._summary(order),
                "product_id": order.get("product_id"),
                "shop_pipeline": SHOP_PIPELINE_PUBLISHED,
                "factory_hook": hook,
                "published_url": order.get("published_url"),
                "message": order.get("client_status_message"),
            }

        factory = self._store_factory()

        order["shop_pipeline"] = SHOP_PIPELINE_FACTORY_QUEUE
        order["product_kind"] = "shop"
        order["status"] = "in_production"
        order["status_label"] = client_status_label(
            "in_production", market, ui_lang=ui_lang
        )
        hook.update(
            {
                "status": "running",
                "queued_at": hook.get("queued_at") or now,
                "updated_at": now,
                "note": "Building niche storefront from brief.",
            }
        )
        order["factory_hook"] = hook
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_FACTORY_QUEUE, ui_lang)}."
        )
        order["updated_at"] = now
        self._save_order(order)

        order["shop_pipeline"] = SHOP_PIPELINE_GENERATING
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_GENERATING, ui_lang)}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)

        gen = factory.generate_from_order(order, product_id=order.get("product_id"))
        product_id = str(gen["product_id"])
        order["product_id"] = product_id

        order["shop_pipeline"] = SHOP_PIPELINE_QUALITY
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_QUALITY, ui_lang)}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)

        if not gen.get("ok"):
            hook.update(
                {
                    "status": "quality_failed",
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "note": "Quality gate failed — brief returned to Factory queue.",
                    "quality": gen.get("quality"),
                }
            )
            order["factory_hook"] = hook
            order["shop_pipeline"] = SHOP_PIPELINE_FACTORY_QUEUE
            order["client_status_message"] = (
                f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_FACTORY_QUEUE, ui_lang)}. "
                "Quality check failed — generation will retry."
            )
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)
            return {
                "ok": False,
                "order": self._summary(order),
                "product_id": product_id,
                "shop_pipeline": SHOP_PIPELINE_FACTORY_QUEUE,
                "factory_hook": hook,
                "quality": gen.get("quality"),
                "message": order["client_status_message"],
            }

        order["shop_pipeline"] = SHOP_PIPELINE_READY_PUBLISH
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_READY_PUBLISH, ui_lang)}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)

        pub = factory.publish(product_id, order_id=order_id)
        published_url = str(pub.get("published_url") or factory.live_url(order_id))
        order["shop_pipeline"] = SHOP_PIPELINE_PUBLISHED
        order["published_url"] = published_url
        order["published_at"] = datetime.now(timezone.utc).isoformat()
        order["status"] = "delivered"
        order["status_label"] = client_status_label(
            "delivered", market, ui_lang=ui_lang
        )
        hook.update(
            {
                "status": "completed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "product_id": product_id,
                "version": gen.get("version"),
                "note": "Storefront generated and published.",
            }
        )
        order["factory_hook"] = hook
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_PUBLISHED, ui_lang)}. "
            "Open your niche storefront from the cabinet."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return {
            "ok": True,
            "order": self._summary(order),
            "product_id": product_id,
            "version": gen.get("version"),
            "shop_pipeline": SHOP_PIPELINE_PUBLISHED,
            "factory_hook": hook,
            "published_url": published_url,
            "message": order["client_status_message"],
        }

    def regenerate_shop_store(
        self, order_id: str, *, customer_id: str, email: str | None = None
    ) -> dict:
        """Rebuild storefront from latest brief as a new version and publish."""
        from app.integration.shop_brief import (
            SHOP_PIPELINE_PUBLISHED,
            shop_pipeline_label,
        )
        from app.factory.market_delivery import client_status_label

        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        market = str(order.get("market_code") or "DE")
        ui_lang = str(order.get("ui_lang") or "en")
        factory = self._store_factory()
        result = factory.regenerate(order)
        if not result.get("ok"):
            raise ValueError("quality_gate_failed")
        product_id = str(result["product_id"])
        published_url = str(
            result.get("published_url") or factory.live_url(order_id)
        )
        order["product_id"] = product_id
        order["shop_pipeline"] = SHOP_PIPELINE_PUBLISHED
        order["published_url"] = published_url
        order["published_at"] = datetime.now(timezone.utc).isoformat()
        order["status"] = "delivered"
        order["status_label"] = client_status_label(
            "delivered", market, ui_lang=ui_lang
        )
        order["factory_hook"] = {
            "status": "completed",
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "product_id": product_id,
            "version": result.get("version"),
            "note": "Regenerated and published.",
        }
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_PUBLISHED, ui_lang)}. "
            f"Version {result.get('version')}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return {
            "ok": True,
            "product_id": product_id,
            "version": result.get("version"),
            "published_url": published_url,
            "shop_pipeline": SHOP_PIPELINE_PUBLISHED,
            "store": self.get_store_for_customer(
                order_id, customer_id=customer_id, email=email
            ),
        }

    def publish_shop_store(
        self, order_id: str, *, customer_id: str, email: str | None = None
    ) -> dict:
        from app.integration.shop_brief import (
            SHOP_PIPELINE_PUBLISHED,
            shop_pipeline_label,
        )
        from app.factory.market_delivery import client_status_label

        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            raise ValueError("product_not_found")
        factory = self._store_factory()
        pub = factory.publish(product_id, order_id=order_id)
        market = str(order.get("market_code") or "DE")
        ui_lang = str(order.get("ui_lang") or "en")
        published_url = str(pub.get("published_url") or factory.live_url(order_id))
        order["shop_pipeline"] = SHOP_PIPELINE_PUBLISHED
        order["published_url"] = published_url
        order["published_at"] = datetime.now(timezone.utc).isoformat()
        order["status"] = "delivered"
        order["status_label"] = client_status_label(
            "delivered", market, ui_lang=ui_lang
        )
        order["client_status_message"] = (
            f"AI Store: {shop_pipeline_label(SHOP_PIPELINE_PUBLISHED, ui_lang)}."
        )
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return {
            "ok": True,
            "product_id": product_id,
            "published_url": published_url,
            "version": pub.get("version"),
            "shop_pipeline": SHOP_PIPELINE_PUBLISHED,
        }

    def rollback_shop_store(
        self,
        order_id: str,
        *,
        version: int,
        customer_id: str,
        email: str | None = None,
    ) -> dict:
        from app.integration.shop_brief import SHOP_PIPELINE_PUBLISHED

        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            raise ValueError("product_not_found")
        factory = self._store_factory()
        result = factory.rollback(product_id, int(version), order_id=order_id)
        published_url = str(result.get("published_url") or factory.live_url(order_id))
        order["shop_pipeline"] = SHOP_PIPELINE_PUBLISHED
        order["published_url"] = published_url
        order["published_at"] = datetime.now(timezone.utc).isoformat()
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        hook = (
            dict(order.get("factory_hook") or {})
            if isinstance(order.get("factory_hook"), dict)
            else {}
        )
        hook.update(
            {
                "status": "completed",
                "version": result.get("version"),
                "note": f"Rolled back to version {result.get('version')}.",
                "updated_at": order["updated_at"],
            }
        )
        order["factory_hook"] = hook
        self._save_order(order)
        return {
            "ok": True,
            "product_id": product_id,
            "version": result.get("version"),
            "published_url": published_url,
            "shop_pipeline": SHOP_PIPELINE_PUBLISHED,
        }

    def get_store_status_for_customer(
        self, order_id: str, *, customer_id: str, email: str | None = None
    ) -> dict:
        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        from app.integration.shop_brief import shop_pipeline_label

        ui_lang = str(order.get("ui_lang") or "en")
        pipeline = str(order.get("shop_pipeline") or "")
        factory = self._store_factory()
        product_id = str(order.get("product_id") or "").strip() or None
        extra = factory.status_payload(product_id)
        return {
            "ok": True,
            "order_id": order_id,
            "shop_pipeline": pipeline,
            "shop_pipeline_label": shop_pipeline_label(pipeline, ui_lang),
            "product_id": product_id,
            "published_url": order.get("published_url") or extra.get("published_url"),
            "version": extra.get("version"),
            "versions": extra.get("versions") or [],
            "published": pipeline == "published" or bool(extra.get("published")),
            "factory_hook": order.get("factory_hook"),
        }

    def get_store_log_for_customer(
        self,
        order_id: str,
        *,
        customer_id: str,
        email: str | None = None,
        limit: int = 80,
    ) -> dict:
        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        product_id = str(order.get("product_id") or "").strip()
        lines = (
            self._store_factory().generation_log(product_id, limit=limit)
            if product_id
            else []
        )
        return {"ok": True, "order_id": order_id, "product_id": product_id, "log": lines}

    def get_store_live_html(
        self, order_id: str, *, page: str = "index.html"
    ) -> tuple[str, dict]:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if str(order.get("package_id") or "").strip().lower() != "ecommerce_shop":
            raise ValueError("not_a_shop_order")
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            raise ValueError("product_not_found")
        html = self._store_factory().read_live_html(product_id, page=page)
        return html, order

    def get_store_for_customer(
        self, order_id: str, *, customer_id: str, email: str | None = None
    ) -> dict:
        """Cabinet AI Store shell payload — ownership by customer_id or email."""
        from app.integration.shop_brief import brief_summary_line, shop_pipeline_label

        order = self._assert_shop_owner(
            order_id, customer_id=customer_id, email=email
        )
        status = self.public_status(order_id)
        brief = order.get("shop_brief") if isinstance(order.get("shop_brief"), dict) else {}
        pipeline = str(order.get("shop_pipeline") or status.get("shop_pipeline") or "")
        ui_lang = str(order.get("ui_lang") or "en")
        product_id = str(order.get("product_id") or "").strip() or None
        factory = self._store_factory()
        extra = factory.status_payload(product_id)
        log_tail = (
            factory.generation_log(product_id, limit=20) if product_id else []
        )
        published_url = order.get("published_url") or extra.get("published_url")
        return {
            "ok": True,
            "order_id": order_id,
            "product_kind": "shop",
            "package_id": "ecommerce_shop",
            "package_name": order.get("package_name") or "AI Store by Virtus Core",
            "store_name": (brief.get("store_name") if brief else None)
            or order.get("business_name"),
            "shop_pipeline": pipeline,
            "shop_pipeline_label": shop_pipeline_label(pipeline, ui_lang),
            "factory_hook": order.get("factory_hook"),
            "shop_brief": brief,
            "brief_summary": brief_summary_line(brief) if brief else "",
            "paid": bool(status.get("paid")),
            "status": status.get("status"),
            "product_id": product_id,
            "version": extra.get("version"),
            "versions": extra.get("versions") or [],
            "published_url": published_url,
            "preview_url": factory.preview_url(product_id) if product_id else None,
            "live_url": factory.live_url(order_id),
            "generation_log": log_tail,
            "pipeline_stages": [
                "accepted",
                "preparing",
                "factory_queue",
                "generating",
                "quality_check",
                "ready_to_publish",
                "published",
            ],
            "r3_sections": [
                {"id": "catalog", "label": "Catalog", "available": True},
                {"id": "pages", "label": "Pages", "available": False},
                {"id": "design", "label": "Design", "available": False},
                {"id": "seo", "label": "SEO", "available": False},
                {"id": "orders", "label": "Orders", "available": False},
                {"id": "settings", "label": "Settings", "available": False},
            ],
        }

    def confirm_order(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order["status"] not in ("pending_confirmation", "awaiting_payment"):
            raise ValueError("invalid_status")
        order["status"] = "confirmed"
        order["status_label"] = "Подтверждено · отправьте КП клиенту"
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return self._summary(order)

    def start_production(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        # ready/in_production allowed to rebuild when ZIP is not packable (legacy gate drift).
        if order["status"] not in (
            "pending_confirmation",
            "confirmed",
            "awaiting_payment",
            "paid",
            "ready",
            "in_production",
        ):
            raise ValueError("invalid_status")

        package_id = str(order.get("package_id") or "basic").strip().lower()
        if package_id in _REPAIR_PACKAGE_IDS or order.get("product_kind") == "repair":
            from app.factory.market_delivery import client_status_label

            market = str(order.get("market_code") or "DE")
            order["status"] = "in_production"
            order["product_kind"] = "repair"
            order["delivery_mode"] = "operator"
            order["status_label"] = client_status_label("in_production", market)
            order["client_status_message"] = (
                "Zahlung erhalten. Virtus Core führt die Reparatur manuell nach Ihrem "
                "Analysebericht aus — kein automatischer CMS-Eingriff."
            )
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)
            return {
                "ok": True,
                "order": self._summary(order),
                "product_id": None,
                "message": order["client_status_message"],
            }

        if package_id == "ecommerce_shop" or order.get("product_kind") == "shop":
            return self.start_shop_pipeline(order_id)

        if (
            str(order.get("product_kind") or "") == "bot"
            or package_id.startswith("bot_")
            or package_id == "ai_chatbot"
        ):
            from app.factory.market_delivery import client_status_label

            market = str(order.get("market_code") or "DE")
            ui_lang = str(order.get("ui_lang") or "en")
            order["product_kind"] = "bot"
            order["status"] = "ready"
            order["delivery_mode"] = "workspace_bot"
            order["status_label"] = client_status_label("ready", market, ui_lang=ui_lang)
            order["client_status_message"] = (
                "Payment received. Connect Telegram in Client Workspace — "
                "your digital employee answers from your bot brief (FAQ/instructions)."
            )
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)
            if order.get("customer_id"):
                try:
                    from app.integration.workspace_ai_bots import provision_from_paid_order

                    provision_from_paid_order(
                        self._memory, str(order["customer_id"]), order
                    )
                except Exception:
                    pass
            return {
                "ok": True,
                "order": self._summary(order),
                "product_id": None,
                "message": order["client_status_message"],
            }

        existing_product_id = (order.get("product_id") or "").strip()
        if existing_product_id:
            product = self._factory_intent._factory.get_product(existing_product_id)
            if not product:
                raise ValueError("product_not_found")
            # Reuse draft only when it can actually become a client ZIP.
            if self._product_packable(existing_product_id):
                from app.factory.market_delivery import client_status_label

                market = str(order.get("market_code") or "DE")
                order["status"] = "ready"
                order["status_label"] = client_status_label("ready", market)
                order["product_id"] = existing_product_id
                order["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_order(order)
                return {
                    "ok": True,
                    "order": self._summary(order),
                    "product_id": existing_product_id,
                    "message": "Zahlung erhalten. Download ist bereit.",
                }
            # Legacy / non-compliant artifact → rebuild Path A landing.
            order["product_id"] = ""
            existing_product_id = ""

        brief = self._factory_brief(order)
        legal = order.get("client_legal") if isinstance(order.get("client_legal"), dict) else {}
        legal = dict(legal)
        package_id = str(order.get("package_id") or "basic")
        street = str(legal.get("street") or "").strip()
        market = str(order.get("market_code") or legal.get("country") or "DE")
        from app.factory.motion_brief import gate_motion_level, normalize_motion_level

        motion = normalize_motion_level(str(order.get("motion_level") or "none"))
        gate = gate_motion_level(motion)
        if not gate["ok"]:
            raise ValueError("WAITLIST_REQUIRED")
        contacts = {
            "business_name": order.get("business_name"),
            "phone": order.get("phone"),
            "whatsapp": order.get("whatsapp") or order.get("phone"),
            "email": order.get("email") or legal.get("email"),
            "city": order.get("city") or legal.get("city"),
            "street": street,
            "package_id": package_id,
            "commerce_mode": order.get("commerce_mode")
            or (_PACKAGES.get(package_id.lower()) or {}).get("commerce_mode"),
            "needs_logo": bool(order.get("needs_logo")),
            "market_code": market,
            "motion_level": motion,
            "brand_style": order.get("brand_style") or "auto",
            "ui_lang": order.get("ui_lang") or order.get("language"),
            "language": order.get("language") or order.get("ui_lang"),
            "locale": order.get("locale"),
            "currency": order.get("currency"),
            "price_label": order.get("price_label"),
            "price_eur": order.get("price_eur"),
            "amount": order.get("price_eur"),
            "niche": order.get("niche"),
            "services_list": order.get("services_list") or [],
            "advantages": order.get("advantages") or [],
            "site_jobs": order.get("site_jobs") or [],
            "why_choose_us": order.get("why_choose_us") or order.get("differentiator") or "",
            "who_is_company": order.get("who_is_company") or order.get("about") or "",
            "clients_who": order.get("clients_who") or "",
            "dream_wishes": order.get("wishes") or order.get("dream_wishes") or "",
            "dialogue": order.get("dialogue") or "",
            "dream_vision": order.get("dream_vision") or "",
            "business_scale": order.get("business_scale") or "",
            "clarify_answers": order.get("clarify_answers")
            if isinstance(order.get("clarify_answers"), dict)
            else {},
        }
        if isinstance(order.get("business_interview"), dict):
            contacts["business_interview"] = order["business_interview"]
        mats = order.get("materials")
        if isinstance(mats, dict) and isinstance(mats.get("files"), list):
            contacts["materials"] = mats["files"]
        elif isinstance(mats, list):
            contacts["materials"] = mats
        if not legal.get("country"):
            legal["country"] = market
        from app.factory.commerce_model import normalize_commerce_mode

        _cm = normalize_commerce_mode(
            package_id,
            commerce_mode=str(contacts.get("commerce_mode") or "") or None,
        )
        factory_pkg = _cm.factory_package_id
        # FactoryIntentRequest still accepts legacy patterns in some builds —
        # map connected→premium, standalone→business for gate compatibility.
        intent_pkg = {
            "standalone": "business",
            "connected": "premium",
            "basic": "business",
            "business": "business",
            "premium": "premium",
        }.get(factory_pkg, "business")
        intent = FactoryIntentRequest(
            product_type="landing-page",
            description=brief,
            audience=f"Kunden in {order.get('city') or 'der Region'}",
            goal="Anfragen und Termine über die Website",
            price_eur=float(order["price_eur"]),
            deadline=None,
            client_legal=legal or None,
            package_id=intent_pkg,
            contacts={**contacts, "package_id": factory_pkg, "commerce_mode": _cm.commerce_mode},
            motion_level=motion,
        )
        result = self._factory_intent.submit(intent)
        from app.factory.market_delivery import client_status_label

        product_id = result.get("product_id")
        order["product_id"] = product_id
        # Factory submit is sync — promote to ready when product exists.
        ready = bool(product_id) and self._client_download_ready(
            {**order, "status": "in_production", "product_id": product_id}
        )
        order["status"] = "ready" if ready else "in_production"
        order["status_label"] = client_status_label(order["status"], market)
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        if ready:
            from app.factory.market_delivery import client_post_pay_message

            order["client_status_message"] = client_post_pay_message(
                "ready", market, download_ready=True
            )
            # Warm ZIP cache at Ready — GET /download should be near-instant.
            factory = getattr(self._factory_intent, "_factory", None)
            if factory is not None and hasattr(factory, "prebuild_client_delivery_zip"):
                try:
                    pre = factory.prebuild_client_delivery_zip(str(product_id))
                    order["download_bytes"] = pre.get("bytes")
                    order["client_zip_prebuilt_at"] = datetime.now(timezone.utc).isoformat()
                    if pre.get("sha256"):
                        order["delivery_sha256"] = pre.get("sha256")
                    order["delivery_immutable"] = bool(pre.get("immutable"))
                except Exception:
                    pass
        self._save_order(order)
        return {
            "ok": True,
            "order": self._summary(order),
            "product_id": result.get("product_id"),
            "message": "Produktion gestartet. Landing Page wird vorbereitet.",
        }

    def _suggest_package(self, payload: dict) -> str:
        if payload.get("needs_domain"):
            return "premium"
        if payload.get("needs_logo"):
            return "business"
        if len((payload.get("extra_wishes") or "").strip()) > 120:
            return "business"
        return "basic"

    def _factory_brief(self, order: dict) -> str:
        lines = [
            f"Kundenauftrag: {order['business_name']}",
            order["description"],
            f"Stadt: {order.get('city') or 'nicht angegeben'}",
            f"Telefon: {order.get('phone') or '—'}",
            f"WhatsApp: {order.get('whatsapp') or '—'}",
            f"E-Mail: {order.get('email') or '—'}",
            f"Paket: {order['package_name']} ({order.get('price_label') or order['price_eur']})",
            f"Brand Style: {order.get('brand_style') or 'auto'}",
        ]
        niche = (order.get("niche") or "").strip()
        if niche:
            lines.append(f"Branche / Niche: {niche}")
        specialization = (order.get("specialization") or "").strip()
        if specialization:
            lines.append(f"Spezialisierung: {specialization}")
        services = self._normalize_services_list(order.get("services_list"))
        if services:
            lines.append("Leistungen des Kunden: " + ", ".join(services))
        advantages = self._normalize_services_list(order.get("advantages"))
        if advantages:
            lines.append("Vorteile / USPs: " + ", ".join(advantages))
        website = (order.get("company_website") or "").strip()
        if website:
            lines.append(f"Bestehende Website: {website}")
        analysis = order.get("site_analysis")
        if isinstance(analysis, dict) and not analysis.get("error"):
            lines.append("Analyse der bestehenden Website (für den neuen Landing-Neustart):")
            if analysis.get("title"):
                lines.append(f"  Titel: {analysis['title']}")
            if analysis.get("tech_stack"):
                lines.append(f"  Technik: {', '.join(analysis['tech_stack'])}")
            strengths = analysis.get("strengths") or []
            issues = analysis.get("issues") or []
            if strengths:
                lines.append("  Stärken: " + "; ".join(str(s) for s in strengths[:6]))
            if issues:
                lines.append("  Schwächen / Chancen: " + "; ".join(str(i) for i in issues[:8]))
            score = analysis.get("improvement_score")
            if score is not None:
                lines.append(f"  Verbesserungs-Score: {score}")
            lines.append(
                "Bitte nutze diese Analyse zusammen mit den Kundenantworten — "
                "neuer Landing Page Neustart, kein Flickwerk am alten CMS."
            )
        elif website:
            lines.append(
                "Website angegeben, Analyse nicht verfügbar — "
                "Landing trotzdem am Geschäft ausrichten (Path A Neustart)."
            )
        if order.get("needs_logo"):
            lines.append(
                "Kundenlogo einbinden (bestehende Datei nach Bestellung) "
                "und Firmenfarben berücksichtigen — kein neues Logo-Design."
            )
        if order.get("needs_domain"):
            lines.append(
                "Hilfe bei Domain-Auswahl, Kauf und Einrichtung "
                "(laufende Gebühren zahlt der Kunde beim Registrar)."
            )
        if order.get("extra_wishes"):
            lines.append(f"Wünsche: {order['extra_wishes']}")
        legal = order.get("client_legal") if isinstance(order.get("client_legal"), dict) else {}
        if legal:
            lines.append("Impressum-Daten (für DE Go-live, Kunde muss prüfen):")
            for key in (
                "owner_name",
                "legal_form",
                "street",
                "zip",
                "city",
                "managing_director",
                "vat_id",
            ):
                val = str(legal.get(key) or "").strip()
                if val:
                    lines.append(f"  {key}: {val}")
        return "\n".join(lines)

    @staticmethod
    def _normalize_services_list(raw: object) -> list[str]:
        items: list[str] = []
        if isinstance(raw, list):
            items = [str(x).strip() for x in raw]
        elif isinstance(raw, str):
            text = raw.replace(";", "\n").replace("|", "\n")
            items = [ln.strip(" •-\t") for ln in text.splitlines()]
        out: list[str] = []
        for item in items:
            if not item or len(item) > 80:
                continue
            if item not in out:
                out.append(item)
            if len(out) >= 12:
                break
        return out

    @staticmethod
    def _client_legal_payload(payload: dict) -> dict:
        raw = payload.get("client_legal")
        if isinstance(raw, dict):
            return {k: v for k, v in raw.items() if v not in (None, "")}
        # Flattened optional fields from older clients
        keys = (
            "owner_name",
            "legal_form",
            "street",
            "zip",
            "city",
            "country",
            "email",
            "phone",
            "managing_director",
            "vat_id",
            "handelsregister",
            "register_court",
            "uses_maps",
            "uses_analytics",
        )
        out = {k: payload.get(k) for k in keys if payload.get(k) not in (None, "")}
        return out

    @staticmethod
    def _normalize_company_website(raw: object) -> str | None:
        text = str(raw or "").strip()
        if not text:
            return None
        if not re.match(r"^https?://", text, flags=re.I):
            text = f"https://{text}"
        if len(text) > 400:
            return None
        return text

    def _analyze_company_website(self, url: str) -> dict | None:
        """Best-effort Path A analysis — never blocks order creation."""
        try:
            from app.integration.site_analysis_service import SiteAnalysisService

            result = SiteAnalysisService(self._memory).analyze(url, use_cache=True)
            if not isinstance(result, dict):
                return {"url": url, "error": "invalid_analysis"}
            # Persist a compact snapshot for Factory / CEO review
            return {
                "url": result.get("url") or url,
                "final_url": result.get("final_url"),
                "title": result.get("title"),
                "has_https": result.get("has_https"),
                "has_viewport": result.get("has_viewport"),
                "load_ms": result.get("load_ms"),
                "issues": list(result.get("issues") or [])[:12],
                "strengths": list(result.get("strengths") or [])[:8],
                "tech_stack": list(result.get("tech_stack") or [])[:6],
                "improvement_score": result.get("improvement_score"),
                "detected_lang": result.get("detected_lang"),
                "error": result.get("error"),
                "analyzed_at": result.get("analyzed_at"),
                "from_cache": bool(result.get("from_cache")),
            }
        except Exception as exc:
            return {"url": url, "error": f"analysis_failed:{type(exc).__name__}"}

    def _proposal_text(self, package: dict, payload: dict, *, project_ctx: dict | None = None) -> str:
        ctx = project_ctx or {}
        service_id = ctx.get("service_id") or SERVICE_WEBSITE
        label = service_label_ru(service_id, fallback="проект")
        name = payload["business_name"].strip()
        deliverables = "\n".join(f"✔ {d}" for d in package["deliverables"])
        if ctx.get("launch_mode"):
            deliverables = "\n".join(
                f"✔ {d}" for d in project_launch_deliverables(service_id)
            )
        price_line = package.get("price_label") or f"{package['price_eur']} {package.get('symbol', '€')}"
        return (
            f"Guten Tag,\n\n"
            f"vielen Dank für Ihre Anfrage zu {label} «{name}».\n\n"
            f"Startpreis: {price_line}\n\n"
            f"Nach der Zahlung:\n{deliverables}\n\n"
            f"Lieferzeit: oft ca. 15 Minuten nach Bestätigung und Zahlung.\n\n"
            f"Wenn Sie starten möchten, schreiben Sie uns — wir senden Rechnung / Zahlungslink.\n\n"
            f"Mit freundlichen Grüßen\n{BRAND_NAME}"
        )

    def _resolve_project_context(self, visitor_id: str | None) -> dict:
        vid = (visitor_id or "").strip()[:64]
        if not vid:
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        try:
            from app.integration.project_platform.service import ProjectPlatformService

            state = ProjectPlatformService(self._memory).get_for_visitor(vid)
        except Exception:
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        if not state.get("has_project") or not state.get("project"):
            return {
                "service_id": SERVICE_WEBSITE,
                "project_name": None,
                "launch_mode": False,
            }
        project = state["project"]
        service_id = str(project.get("service_id") or SERVICE_WEBSITE)
        company = ""
        for item in project.get("journey", {}).get("items", []):
            if item.get("id") == "company" and item.get("status") == "done":
                company = str(item.get("value") or "").strip()
                break
        if not company:
            title = str(project.get("identity", {}).get("title") or "").strip()
            if title and title not in ("Мой проект", "Хочу создать сайт для своей компании."):
                company = title
        has_preview = any(
            art.get("kind") == "preview" and art.get("href")
            for ver in project.get("versions", [])
            for art in ver.get("artifacts", [])
        )
        launch_mode = bool(has_preview and company)
        return {
            "service_id": service_id,
            "project_name": company or None,
            "launch_mode": launch_mode,
        }

    def mark_delivered_by_product(self, product_id: str) -> dict | None:
        """Factory handoff → sales order delivered + review token (Path A trust)."""
        pid = (product_id or "").strip()
        if not pid:
            return None
        order = next(
            (o for o in self._load_all() if str(o.get("product_id") or "").strip() == pid),
            None,
        )
        if not order:
            return None
        return self.mark_order_delivered(str(order["order_id"]))

    def mark_order_delivered(self, order_id: str) -> dict:
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") not in ("paid", "in_production", "ready", "delivered"):
            raise ValueError("not_paid")
        now = datetime.now(timezone.utc).isoformat()
        order["status"] = "delivered"
        order["status_label"] = "An den Kunden übergeben"
        order["delivered_at"] = order.get("delivered_at") or now
        order["review_eligible"] = True
        if not order.get("review_token"):
            order["review_token"] = new_review_token()
        order["updated_at"] = now
        self._save_order(order)
        return order

    def public_status(self, order_id: str) -> dict:
        from app.factory.market_delivery import (
            PATH_A_ETA_MINUTES,
            client_current_step,
            client_next_step,
            client_post_pay_message,
            client_status_label,
            client_timeline,
            delivery_ready_headline,
            delivery_value_items,
            factory_locale_context,
            next_product_offers,
            normalize_market,
            order_ui_lang,
            publish_status_payload,
            render_client_receipt_text,
        )
        from app.integration.market_registry import format_amount, get_market

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        market = normalize_market(str(order.get("market_code") or "DE"))
        ui_lang = order_ui_lang(order, market)
        locale_ctx = factory_locale_context(order, market)
        currency = str(order.get("currency") or get_market(market).currency or "EUR")
        symbol = str(order.get("symbol") or get_market(market).symbol or "€")
        amount = float(order.get("price_eur") or 0)
        price_label = str(order.get("price_label") or "").strip() or format_amount(
            int(round(amount)), symbol
        )
        service_id = str(order.get("service_id") or SERVICE_WEBSITE)
        launch_mode = bool(order.get("launch_mode"))
        download_ready = self._client_download_ready(order)
        status = str(order.get("status") or "")
        product_kind_early = str(order.get("product_kind") or "website")
        if str(order.get("package_id") or "") == "ecommerce_shop":
            product_kind_early = "shop"
        # Promote to ready as soon as ZIP can be served (honest cabinet UX).
        # AI Store uses shop_pipeline — never fake Ready via ZIP.
        if product_kind_early != "shop":
            if download_ready and status in ("paid", "in_production"):
                status = "ready"
                order["status"] = "ready"
                order["status_label"] = client_status_label("ready", market, ui_lang=ui_lang)
                order["updated_at"] = datetime.now(timezone.utc).isoformat()
                self._save_order(order)
            # Never expose Ready when ZIP cannot be packed (blocks Ready → 404).
            elif status == "ready" and not download_ready:
                status = "in_production"
                order["status"] = "in_production"
                order["status_label"] = client_status_label(
                    "in_production", market, ui_lang=ui_lang
                )
                order["updated_at"] = datetime.now(timezone.utc).isoformat()
                order["client_status_message"] = client_post_pay_message(
                    "in_production", market, download_ready=False, ui_lang=ui_lang
                )
                self._save_order(order)
        download_bytes, generated_at = self._client_download_meta(
            order, download_ready=download_ready
        )
        product_kind = str(order.get("product_kind") or "website")
        if str(order.get("package_id") or "") in _REPAIR_PACKAGE_IDS:
            product_kind = "repair"
        if str(order.get("package_id") or "") == "ecommerce_shop":
            product_kind = "shop"
        submitted = bool(order.get("review_submitted"))
        eligible = (
            bool(order.get("review_eligible"))
            and status == "delivered"
            and not submitted
        )
        token = str(order.get("review_token") or "") if eligible else ""
        eta_minutes = order.get("estimated_minutes")
        if eta_minutes is None:
            eta_minutes = PATH_A_ETA_MINUTES if status != "awaiting_payment" else None
        client_message = (
            order.get("client_status_message")
            or client_post_pay_message(
                status, market, download_ready=download_ready, ui_lang=ui_lang
            )
            or self._default_client_message(order)
        )
        shop_pipeline = (
            (str(order.get("shop_pipeline") or "") or None)
            if product_kind == "shop"
            else None
        )
        shop_pipeline_label = None
        if product_kind == "shop" and shop_pipeline:
            from app.integration.shop_brief import shop_pipeline_label as _spl

            shop_pipeline_label = _spl(shop_pipeline, ui_lang)
        download_label = None
        if download_ready:
            download_label = "Ready for download"
        elif product_kind == "shop" and shop_pipeline_label:
            download_label = shop_pipeline_label
        elif status in ("paid", "in_production", "ready") and product_kind in (
            "addon",
            "repair",
            "shop",
        ):
            download_label = "In progress"
        elif status in ("paid", "in_production") and product_kind not in ("repair", "shop"):
            download_label = "generating..."

        from app.integration.demo_payment import demo_public_flags

        paid_flag = status in ("paid", "in_production", "ready", "delivered")
        status_path = f"/order/status/{order_id}"
        existing_receipt = str(order.get("client_receipt_text") or "")
        thin_receipt = (not existing_receipt) or (
            (ui_lang == "de" or market == "DE")
            and (
                "Rechnungsnummer" not in existing_receipt
                or "Leistungsbeschreibung" not in existing_receipt
            )
        )
        if paid_flag and thin_receipt:
            order["client_receipt_text"] = render_client_receipt_text(
                order=order, status_path=status_path, paid=amount
            )
            order["updated_at"] = datetime.now(timezone.utc).isoformat()
            self._save_order(order)

        legal = order.get("client_legal") if isinstance(order.get("client_legal"), dict) else {}
        seller_block = {
            "name": "Virtus Core",
            "address": "",
            "vat_id": "",
            "email": "hello@virtuscore.com",
        }
        try:
            from pathlib import Path

            from app.legal.service import LegalFoundationService

            mem = Path(__file__).resolve().parents[1] / "memory"
            preview = LegalFoundationService(mem).operator_preview()
            seller_block = {
                "name": str(
                    preview.get("trade_name") or preview.get("full_name") or "Virtus Core"
                ),
                "address": ", ".join(
                    p
                    for p in [
                        str(preview.get("address_street") or "").strip(),
                        f"{str(preview.get('address_zip') or '').strip()} {str(preview.get('address_city') or '').strip()}".strip(),
                        str(preview.get("address_country") or "DE").strip(),
                    ]
                    if p
                ),
                "vat_id": str(preview.get("vat_id") or "").strip(),
                "email": str(preview.get("email") or "hello@virtuscore.com"),
            }
        except Exception:
            pass
        buyer_block = {
            "name": str(legal.get("owner_name") or order.get("business_name") or "").strip(),
            "street": str(legal.get("street") or "").strip(),
            "zip_city": f"{str(legal.get('zip') or '').strip()} {str(legal.get('city') or order.get('city') or '').strip()}".strip(),
            "country": str(legal.get("country") or market or "").strip(),
            "email": str(legal.get("email") or order.get("email") or "").strip(),
        }

        return {
            "order_id": order["order_id"],
            "business_name": order["business_name"],
            "package_id": order.get("package_id"),
            "package_name": order["package_name"],
            "product_kind": product_kind,
            "price_eur": amount,
            "price_label": price_label,
            "currency": currency,
            "symbol": symbol,
            "market_code": market,
            "ui_lang": ui_lang,
            "language": ui_lang,
            "locale": locale_ctx.get("locale"),
            "factory_context": locale_ctx,
            "motion_level": str(order.get("motion_level") or "none"),
            "status": status,
            "status_label": client_status_label(status, market, ui_lang=ui_lang),
            "current_step": client_current_step(status, market, ui_lang=ui_lang),
            "next_step": client_next_step(status, market, ui_lang=ui_lang),
            "timeline": client_timeline(
                status,
                market,
                download_ready=download_ready,
                paid_at=str(order.get("paid_at") or "") or None,
                ui_lang=ui_lang,
            ),
            "estimated_delivery_at": order.get("estimated_delivery_at"),
            "estimated_hours": order.get("estimated_hours"),
            "estimated_minutes": eta_minutes,
            "client_message": client_message,
            "client_receipt_text": order.get("client_receipt_text", ""),
            "product_id": order.get("product_id"),
            "paid": status in ("paid", "in_production", "ready", "delivered"),
            "paid_at": order.get("paid_at"),
            "created_at": order.get("created_at"),
            "updated_at": order.get("updated_at"),
            **demo_public_flags(order, ui_lang=ui_lang),
            "download_ready": download_ready,
            "download_url": f"/api/sales/orders/{order_id}/download" if download_ready else None,
            "download_bytes": download_bytes,
            "generated_at": generated_at,
            "download_label": download_label,
            "service_id": service_id,
            "service_name": order.get("package_name") or package_display_name(order.get("package_id")),
            "eta_label": (
                str((_PACKAGES.get(str(order.get("package_id") or "").strip().lower()) or {}).get("eta_days") or "")
                or None
            ),
            "billing": str(
                (_PACKAGES.get(str(order.get("package_id") or "").strip().lower()) or {}).get(
                    "billing"
                )
                or "one_time"
            ),
            "shop_pipeline": shop_pipeline,
            "shop_pipeline_label": shop_pipeline_label,
            "factory_hook": order.get("factory_hook") if product_kind == "shop" else None,
            "store_url": (
                f"/client/stores/{order_id}" if product_kind == "shop" else None
            ),
            "launch_mode": launch_mode,
            "review_eligible": eligible,
            "review_submitted": submitted,
            "review_url": f"/order/review/{order_id}?token={token}" if token else None,
            "deployment_preference": str(order.get("deployment_preference") or "unset"),
            "hosting_provider": order.get("hosting_provider"),
            "assisted_guide": self._assisted_guide_payload(order),
            "receipt": {
                "brand": "Virtus Core",
                "document_title": (
                    "Rechnung / Zahlungsbeleg (§ 14 UStG)"
                    if (ui_lang == "de" or market == "DE")
                    else "Receipt"
                ),
                "order_id": order["order_id"],
                "customer": order["business_name"],
                "package": order["package_name"],
                "package_id": order.get("package_id"),
                "amount": price_label,
                "currency": currency,
                "status": client_status_label(
                    "paid" if status != "awaiting_payment" else status,
                    market,
                    ui_lang=ui_lang,
                ),
                "date": order.get("paid_at") or order.get("created_at"),
                "service_date": order.get("paid_at") or order.get("created_at"),
                "leistung": f"Website-Paket: {order.get('package_name') or ''} — digitales Lieferprodukt (ZIP)",
                "seller": seller_block,
                "buyer": buyer_block,
                "vat_note": (
                    f"USt-IdNr.: {seller_block['vat_id']}"
                    if seller_block.get("vat_id")
                    else (
                        "§ 19 UStG: Keine Umsatzsteuer ausgewiesen (Kleinunternehmer / Demo)."
                        if (ui_lang == "de" or market == "DE")
                        else None
                    )
                ),
                "payment_mode": str(
                    order.get("payment_mode") or order.get("payment_provider") or ""
                )
                or None,
                "download_available": download_ready,
                "market_code": market,
                "ui_lang": ui_lang,
            },
            "delivery_headline": (
                delivery_ready_headline(market, ui_lang=ui_lang) if download_ready else None
            ),
            "delivery_items": (
                delivery_value_items(order.get("package_id"), market, ui_lang=ui_lang)
                if download_ready
                else []
            ),
            "publish": publish_status_payload(
                market_code=market,
                downloaded=bool(order.get("client_downloaded_at")),
                online=bool(order.get("published_url")),
                published_url=str(order.get("published_url") or "") or None,
                downloaded_at=str(order.get("client_downloaded_at") or "") or None,
                online_at=str(order.get("published_at") or "") or None,
            ),
            "next_offers": (
                next_product_offers(
                    market,
                    interest=order.get("next_offer_interest")
                    if isinstance(order.get("next_offer_interest"), dict)
                    else {},
                )
                if download_ready
                else []
            ),
        }

    def set_deployment_preference(
        self,
        order_id: str,
        preference: str,
        hosting_provider: str | None = None,
    ) -> dict:
        """Client chooses ZIP Only vs Assisted after ZIP is ready. No credentials stored."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if not self._client_download_ready(order):
            raise ValueError("download_not_ready")

        pref = str(preference or "").strip().lower()
        if pref not in ("zip_only", "assisted"):
            raise ValueError("invalid_preference")

        provider: str | None = None
        raw_provider = (hosting_provider or "").strip().lower() or None
        if raw_provider:
            if raw_provider not in HOSTING_PROVIDERS:
                raise ValueError("invalid_provider")
            provider = raw_provider

        now = datetime.now(timezone.utc).isoformat()
        order["deployment_preference"] = pref
        order["hosting_provider"] = provider
        order["deployment_preference_at"] = now
        for banned in (
            "hosting_password",
            "ftp_password",
            "password",
            "credentials",
            "api_token",
        ):
            order.pop(banned, None)
        order["updated_at"] = now
        self._save_order(order)

        if pref == "assisted":
            try:
                from app.integration.owner_notification_service import (
                    OwnerNotificationService,
                )

                provider_label = provider or "not_selected"
                OwnerNotificationService(self._memory).notify(
                    title="Assisted Deployment angefragt",
                    message=(
                        f"{order.get('business_name')} · {order_id} · "
                        f"Anbieter: {provider_label}. "
                        "Keine Hosting-Passwörter in Virtus — Variante A/B mit dem Kunden."
                    ),
                    order_id=order_id,
                )
            except Exception as exc:
                logger.warning("assisted deployment notify failed: %s", exc)

        return self.public_status(order_id)

    def set_publish_status(
        self,
        order_id: str,
        *,
        state: str,
        published_url: str | None = None,
    ) -> dict:
        """Client marks ZIP downloaded or site live (psychological completion)."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if not self._client_download_ready(order):
            raise ValueError("download_not_ready")

        now = datetime.now(timezone.utc).isoformat()
        st = str(state or "").strip().lower()
        if st == "downloaded":
            if not order.get("client_downloaded_at"):
                order["client_downloaded_at"] = now
        elif st == "online":
            url = (published_url or "").strip()
            if not url:
                raise ValueError("url_required")
            if not re.match(r"^https?://", url, re.I):
                url = "https://" + url
            if len(url) > 500 or " " in url:
                raise ValueError("invalid_url")
            order["published_url"] = url
            order["published_at"] = now
            if not order.get("client_downloaded_at"):
                order["client_downloaded_at"] = now
        else:
            raise ValueError("invalid_state")

        order["updated_at"] = now
        self._save_order(order)
        return self.public_status(order_id)

    def log_next_offer_interest(
        self,
        order_id: str,
        *,
        offer_id: str,
        note: str | None = None,
    ) -> dict:
        """Soft interest for LTV ladder (AI Assistant etc.) — notifies owner."""
        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if order.get("status") not in ("paid", "in_production", "ready", "delivered"):
            raise ValueError("not_paid")

        oid = str(offer_id or "").strip().lower()
        allowed = {"ai_business_assistant", "whatsapp_business", "seo_growth"}
        if oid not in allowed:
            raise ValueError("invalid_offer")

        now = datetime.now(timezone.utc).isoformat()
        bag = order.get("next_offer_interest")
        if not isinstance(bag, dict):
            bag = {}
        bag[oid] = {
            "at": now,
            "note": (note or "").strip()[:500] or None,
        }
        order["next_offer_interest"] = bag
        order["updated_at"] = now
        self._save_order(order)

        try:
            from app.integration.owner_notification_service import OwnerNotificationService

            OwnerNotificationService(self._memory).notify(
                title="Next offer interest",
                message=(
                    f"{order.get('business_name')} · {order_id} · {oid}"
                    + (f" · {(note or '')[:120]}" if note else "")
                ),
                order_id=order_id,
            )
        except Exception as exc:
            logger.warning("next offer notify failed: %s", exc)

        return self.public_status(order_id)

    @staticmethod
    def _assisted_guide_payload(order: dict) -> dict | None:
        pref = str(order.get("deployment_preference") or "unset")
        if pref != "assisted":
            return None
        return {
            "headline": "Wir können helfen, die Website zu veröffentlichen.",
            "trust": [
                "Website läuft auf Ihrem Hosting",
                "Domain gehört Ihnen",
                "Hosting-Konto gehört Ihnen",
                "SSL und DNS gehören Ihnen",
                "Alle Anbieter-Rechnungen gehen an Sie",
            ],
            "never_stores": [
                "Hosting-Passwort",
                "Domain-Passwort",
                "Bankkarten",
                "Dauerhaften Zugang",
            ],
            "variant_a": (
                "Bevorzugt: Sie legen einen temporären Benutzer an oder laden uns "
                "als Helfer ein. Nach Go-live entfernen Sie den Zugang — Sie bleiben "
                "alleiniger Eigentümer."
            ),
            "variant_b": (
                "Falls kein temporärer Zugang möglich ist: Sie bleiben eingeloggt und "
                "folgen der Anleitung; Hilfe per Chat oder Anruf."
            ),
            "providers": sorted(HOSTING_PROVIDERS),
            "hosting_provider": order.get("hosting_provider"),
        }

    def build_client_download(self, order_id: str) -> tuple[bytes, str]:
        """Paid Path A order → ZIP with landing + legal pages (no CEO gate)."""
        from app.factory.market_delivery import client_status_label, normalize_market

        order = self.get_order(order_id)
        if not order:
            raise ValueError("order_not_found")
        if not self._client_download_ready(order):
            raise ValueError("download_not_ready")
        product_id = str(order.get("product_id") or "").strip()
        factory = getattr(self._factory_intent, "_factory", None)
        if factory is None or not hasattr(factory, "build_client_delivery_zip"):
            raise ValueError("factory_unavailable")
        market = normalize_market(str(order.get("market_code") or "DE"))
        # Ensure product meta carries market + frozen Path A price before ZIP.
        try:
            meta = factory._load_meta(product_id)  # type: ignore[attr-defined]
            if isinstance(meta, dict):
                dirty = False
                if meta.get("market_code") != market:
                    meta["market_code"] = market
                    dirty = True
                pricing = {
                    "package_id": str(order.get("package_id") or "basic"),
                    "amount": order.get("price_eur"),
                    "currency": order.get("currency"),
                    "price_label": order.get("price_label"),
                }
                if meta.get("path_a_pricing") != pricing:
                    meta["path_a_pricing"] = pricing
                    dirty = True
                demo = bool(order.get("demo") or order.get("is_demo")) or str(
                    order.get("payment_mode") or ""
                ).lower() == "demo"
                if demo and not meta.get("demo_order"):
                    meta["demo_order"] = True
                    meta["allow_demo_pack"] = True
                    dirty = True
                if dirty:
                    product_dir = factory._sandbox / product_id  # type: ignore[attr-defined]
                    (product_dir / "meta.json").write_text(
                        __import__("json").dumps(meta, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
        except Exception:
            pass
        data, filename = factory.build_client_delivery_zip(product_id)
        order["client_downloaded_at"] = datetime.now(timezone.utc).isoformat()
        order["download_bytes"] = len(data)
        if order.get("status") == "in_production":
            order["status"] = "ready"
            order["status_label"] = client_status_label("ready", market)
        order["updated_at"] = datetime.now(timezone.utc).isoformat()
        self._save_order(order)
        return data, filename

    def _product_has_client_html(self, product_id: str) -> bool:
        """Minimal deliverable check — index.html present and non-trivial."""
        factory = getattr(self._factory_intent, "_factory", None)
        if factory is None or not hasattr(factory, "get_product"):
            return False
        if not factory.get_product(product_id):
            return False
        try:
            product_dir = factory._sandbox / product_id  # type: ignore[attr-defined]
            html_path = product_dir / "index.html"
            if not html_path.is_file():
                return False
            return html_path.stat().st_size >= 4000
        except Exception:
            return False

    def _product_packable(self, product_id: str, *, demo: bool = False) -> bool:
        """True only when index.html exists and passes Compliance (ZIP packable).

        Demo orders: deliver if HTML exists — owner eyes still decide PASS.
        Gates that self-fail on «Demo» / platform words must not strand Path A.
        """
        import hashlib

        from app.factory.compliance_engine import assert_compliance

        if demo and self._product_has_client_html(product_id):
            return True

        factory = getattr(self._factory_intent, "_factory", None)
        if factory is None or not hasattr(factory, "get_product"):
            return False
        if not factory.get_product(product_id):
            return False
        try:
            product_dir = factory._sandbox / product_id  # type: ignore[attr-defined]
            html_path = product_dir / "index.html"
            if not html_path.is_file():
                return False
            meta = factory._load_meta(product_id)  # type: ignore[attr-defined]
            if not isinstance(meta, dict):
                meta = {}
            cg = meta.get("commercial_gate") if isinstance(meta.get("commercial_gate"), dict) else {}
            # Hard Gate FAIL → never pack. Score FAIL after Hard Gate also blocks ZIP.
            if cg:
                if cg.get("hard_passed") is False:
                    return False
                if cg.get("score_passed") is False:
                    return False
            html_bytes = html_path.read_bytes()
            html_hash = hashlib.sha256(html_bytes).hexdigest()[:20]
            prior = meta.get("compliance") if isinstance(meta.get("compliance"), dict) else {}
            # Fast path only while HTML unchanged since last green compliance.
            if (
                cg.get("passed") is True
                and prior.get("passed") is True
                and meta.get("validation_passed") is True
                and meta.get("packable_html_hash") == html_hash
            ):
                return True
            assert_compliance(
                html_bytes.decode("utf-8"),
                meta=meta,
                assets_dir=product_dir / "assets",
            )
            if meta.get("packable_html_hash") != html_hash:
                meta["packable_html_hash"] = html_hash
                (product_dir / "meta.json").write_text(
                    __import__("json").dumps(meta, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            return True
        except Exception:
            return False

    def _client_download_ready(self, order: dict) -> bool:
        # AI Store uses published_url / Open Store — not Path A ZIP download.
        if str(order.get("package_id") or "").strip().lower() == "ecommerce_shop":
            return False
        if str(order.get("product_kind") or "") == "shop":
            return False
        if order.get("status") not in ("paid", "in_production", "ready", "delivered"):
            return False
        product_id = str(order.get("product_id") or "").strip()
        if not product_id:
            return False
        demo = bool(order.get("demo") or order.get("is_demo")) or str(
            order.get("payment_mode") or ""
        ).lower() == "demo"
        return self._product_packable(product_id, demo=demo)

    def _client_download_meta(
        self, order: dict, *, download_ready: bool
    ) -> tuple[int | None, str | None]:
        """Approx archive size (product folder) + generation timestamp for cabinet UX."""
        generated = (
            str(order.get("updated_at") or order.get("paid_at") or order.get("created_at") or "")
            or None
        )
        if not download_ready:
            return None, generated if order.get("status") in (
                "paid",
                "in_production",
                "ready",
                "delivered",
            ) else None
        cached = order.get("download_bytes")
        if isinstance(cached, int) and cached > 0:
            return cached, generated
        product_id = str(order.get("product_id") or "").strip()
        factory = getattr(self._factory_intent, "_factory", None)
        if not product_id or factory is None:
            return None, generated
        try:
            sandbox = getattr(factory, "_sandbox", None)
            if sandbox is None:
                return None, generated
            root = Path(sandbox) / product_id
            if not root.is_dir():
                return None, generated
            total = 0
            for p in root.rglob("*"):
                if p.is_file():
                    try:
                        total += p.stat().st_size
                    except OSError:
                        pass
            # ZIP is typically close to folder payload; show folder bytes as estimate
            return total if total > 0 else None, generated
        except Exception:
            return None, generated

    def _client_timeline(self, order: dict) -> list[dict]:
        from app.factory.market_delivery import client_timeline

        return client_timeline(str(order.get("status", "")), order.get("market_code"))

    def _client_next_step(self, order: dict) -> str:
        from app.factory.market_delivery import client_next_step

        return client_next_step(str(order.get("status", "")), order.get("market_code"))

    def _client_status_label(self, order: dict) -> str:
        from app.factory.market_delivery import client_status_label

        return client_status_label(str(order.get("status", "")), order.get("market_code"))

    def _client_current_step(self, order: dict) -> str:
        return project_client_current_step(
            str(order.get("service_id") or SERVICE_WEBSITE),
            str(order.get("status", "")),
        )

    def _default_client_message(self, order: dict) -> str:
        if order.get("status") == "awaiting_payment":
            return project_awaiting_payment_message(
                launch_mode=bool(order.get("launch_mode")),
            )
        return ""

    def _summary(self, order: dict) -> dict:
        return {
            "order_id": order["order_id"],
            "status": order["status"],
            "status_label": order["status_label"],
            "business_name": order["business_name"],
            "city": order.get("city", ""),
            "phone": order.get("phone", ""),
            "whatsapp": order.get("whatsapp", ""),
            "email": str(order.get("email") or ""),
            "customer_id": order.get("customer_id") or None,
            "package_name": order["package_name"],
            "package_id": order.get("package_id"),
            "product_kind": order.get("product_kind"),
            "price_eur": order["price_eur"],
            "created_at": order["created_at"],
            "product_id": order.get("product_id"),
            "proposal_text": order.get("proposal_text", ""),
            "motion_level": str(order.get("motion_level") or "none"),
            "market_code": order.get("market_code"),
            "paid": order.get("status") in ("paid", "in_production", "ready", "delivered"),
            "paid_at": order.get("paid_at"),
            "estimated_delivery_at": order.get("estimated_delivery_at"),
            "download_ready": bool(self._client_download_ready(order)),
        }

    def _orders_path(self) -> Path:
        return self._memory / "sales_orders.json"

    def _load_all(self) -> list[dict]:
        path = self._orders_path()
        if not path.is_file():
            return []
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except (json.JSONDecodeError, OSError):
            return []

    def _save_order(self, order: dict) -> None:
        orders = [o for o in self._load_all() if o.get("order_id") != order.get("order_id")]
        orders.append(order)
        self._orders_path().write_text(
            json.dumps(orders, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
