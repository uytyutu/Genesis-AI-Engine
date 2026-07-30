"""Path A Pricing Engine — single source of truth for package amounts.

Letter, /order checkout, Stripe, and Factory meta must all resolve through
``resolve_path_a_offer`` / ``list_path_a_packages``. Do not hardcode Path A
tier amounts elsewhere.

Unknown markets fall back to DE EUR anchors scaled by market_registry
(legacy), so Stage-1 markets without a curated row still work.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Stripe zero-decimal currencies used by Path A (unit_amount = major units).
ZERO_DECIMAL_CURRENCIES: frozenset[str] = frozenset({"JPY", "KRW"})

PACKAGE_IDS: tuple[str, ...] = (
    "basic",
    "business",
    "premium",
    "repair_lite",
    "repair_standard",
    "repair_complete",
)

WEBSITE_PACKAGE_IDS: tuple[str, ...] = ("basic", "business", "premium")
REPAIR_PACKAGE_IDS: tuple[str, ...] = (
    "repair_lite",
    "repair_standard",
    "repair_complete",
)

# DE anchors — also used as fallback scale base.
_DE_SKUS: dict[str, int] = {
    "basic": 350,
    "business": 650,
    "premium": 1200,
    "repair_lite": 199,
    "repair_standard": 349,
    "repair_complete": 499,
}

# Curated Path A amounts (major units). Currency/symbol from market_registry.
_PATH_A_SKUS: dict[str, dict[str, int]] = {
    # Tier 1
    "DE": dict(_DE_SKUS),
    "AT": dict(_DE_SKUS),
    "CH": {
        "basic": 390,
        "business": 720,
        "premium": 1350,
        "repair_lite": 229,
        "repair_standard": 399,
        "repair_complete": 569,
    },
    "US": {
        "basic": 399,
        "business": 749,
        "premium": 1399,
        "repair_lite": 229,
        "repair_standard": 399,
        "repair_complete": 569,
    },
    "CA": {
        "basic": 399,
        "business": 749,
        "premium": 1399,
        "repair_lite": 229,
        "repair_standard": 399,
        "repair_complete": 569,
    },
    "GB": {
        "basic": 299,
        "business": 549,
        "premium": 999,
        "repair_lite": 179,
        "repair_standard": 299,
        "repair_complete": 429,
    },
    # APAC
    "AU": {
        "basic": 549,
        "business": 999,
        "premium": 1899,
        "repair_lite": 299,
        "repair_standard": 549,
        "repair_complete": 799,
    },
    "NZ": {
        "basic": 549,
        "business": 999,
        "premium": 1899,
        "repair_lite": 299,
        "repair_standard": 549,
        "repair_complete": 799,
    },
    "JP": {
        "basic": 55000,
        "business": 98000,
        "premium": 180000,
        "repair_lite": 35000,
        "repair_standard": 55000,
        "repair_complete": 78000,
    },
    "KR": {
        "basic": 490000,
        "business": 890000,
        "premium": 1600000,
        "repair_lite": 290000,
        "repair_standard": 490000,
        "repair_complete": 690000,
    },
    "SG": {
        "basic": 499,
        "business": 899,
        "premium": 1699,
        "repair_lite": 279,
        "repair_standard": 479,
        "repair_complete": 699,
    },
    # Active EU / CIS desk — Basic anchors from Country Desk; tiers from DE ratio.
    "PL": {
        "basic": 1200,
        "business": 2200,
        "premium": 4100,
        "repair_lite": 700,
        "repair_standard": 1200,
        "repair_complete": 1700,
    },
    "CZ": {
        "basic": 15000,
        "business": 28000,
        "premium": 51000,
        "repair_lite": 8500,
        "repair_standard": 15000,
        "repair_complete": 21000,
    },
    # Active EU / CIS desk — Basic anchors from Country Desk; tiers from DE ratio.
    "FR": {
        "basic": 330,
        "business": 610,
        "premium": 1130,
        "repair_lite": 189,
        "repair_standard": 329,
        "repair_complete": 469,
    },
    "IT": {
        "basic": 320,
        "business": 595,
        "premium": 1100,
        "repair_lite": 182,
        "repair_standard": 319,
        "repair_complete": 456,
    },
    "ES": {
        "basic": 300,
        "business": 560,
        "premium": 1030,
        "repair_lite": 170,
        "repair_standard": 299,
        "repair_complete": 428,
    },
    "NL": {
        "basic": 370,
        "business": 685,
        "premium": 1270,
        "repair_lite": 210,
        "repair_standard": 369,
        "repair_complete": 528,
    },
    "BE": dict(_DE_SKUS),
    "PT": {
        "basic": 270,
        "business": 500,
        "premium": 925,
        "repair_lite": 154,
        "repair_standard": 269,
        "repair_complete": 385,
    },
    "RO": {
        "basic": 200,
        "business": 370,
        "premium": 685,
        "repair_lite": 114,
        "repair_standard": 199,
        "repair_complete": 285,
    },
    "SK": {
        "basic": 220,
        "business": 410,
        "premium": 755,
        "repair_lite": 125,
        "repair_standard": 219,
        "repair_complete": 314,
    },
    "UA": {
        "basic": 8000,
        "business": 14900,
        "premium": 27400,
        "repair_lite": 4550,
        "repair_standard": 8000,
        "repair_complete": 11400,
    },
    "RU": {
        "basic": 180,
        "business": 335,
        "premium": 615,
        "repair_lite": 102,
        "repair_standard": 179,
        "repair_complete": 257,
    },
}


@dataclass(frozen=True)
class FinalOffer:
    package_id: str
    amount: int
    currency: str
    symbol: str
    market_code: str
    price_label: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "amount": self.amount,
            "currency": self.currency,
            "symbol": self.symbol,
            "market_code": self.market_code,
            "price_label": self.price_label,
        }


def normalize_package_id(package_id: str | None) -> str:
    pid = str(package_id or "basic").strip().lower()
    if pid in PACKAGE_IDS:
        return pid
    return "basic"


def is_zero_decimal_currency(currency: str | None) -> bool:
    return str(currency or "").strip().upper() in ZERO_DECIMAL_CURRENCIES


def stripe_unit_amount(amount: float | int, currency: str | None) -> int:
    """Major units → Stripe ``unit_amount`` (respects zero-decimal currencies)."""
    major = float(amount)
    if is_zero_decimal_currency(currency):
        return max(1, int(round(major)))
    return max(1, int(round(major * 100)))


def stripe_major_from_total(amount_total: int | float, currency: str | None) -> float:
    """Stripe ``amount_total`` → major units."""
    total = float(amount_total or 0)
    if is_zero_decimal_currency(currency):
        return total
    return total / 100.0


def format_path_a_price(amount: int, symbol: str) -> str:
    from app.integration.market_registry import format_amount

    return format_amount(int(amount), symbol)


def format_path_a_range(lo: int, hi: int, symbol: str) -> str:
    """Single-symbol range for hub cards (e.g. ``350–1200 €``, ``15 000–… Kč``)."""
    lo_s = f"{int(lo):,}".replace(",", " ")
    hi_s = f"{int(hi):,}".replace(",", " ")
    return f"{lo_s}–{hi_s} {symbol}"


def resolve_hub_catalog_prices(market_code: str) -> dict[str, Any]:
    """Market Resolver for /site hub product cards.

    Currency, symbol, and formatted amounts come only from Path A + bot offers.
    UI composes localized ``from`` / ``monthly`` / ``Free`` prefixes around these.
    """
    from app.integration.market_registry import get_market

    market = get_market(market_code)
    basic = resolve_path_a_offer("basic", market.code)
    premium = resolve_path_a_offer("premium", market.code)
    repair = resolve_path_a_offer("repair_lite", market.code)
    bot = resolve_bot_offer("bot_starter", market.code)
    return {
        "market_code": market.code,
        "currency": market.currency,
        "symbol": market.symbol,
        "landing_website": {
            "range_label": format_path_a_range(
                basic.amount, premium.amount, market.symbol
            ),
            "basic_label": basic.price_label,
            "premium_label": premium.price_label,
            "basic_amount": basic.amount,
            "premium_amount": premium.amount,
        },
        "ai_business_bot": {
            "setup_label": bot.setup_label,
            "monthly_label": bot.monthly_label,
            "setup_amount": bot.setup_amount,
            "monthly_amount": bot.monthly_amount,
        },
        "website_repair": {
            "from_label": repair.price_label,
            "amount": repair.amount,
        },
        "website_check": {
            "free": True,
        },
    }


def _sku_amount(market_code: str, package_id: str) -> int:
    """Resolve curated amount; unknown market → DE × checkout_price_scale."""
    code = (market_code or "DE").strip().upper() or "DE"
    pid = normalize_package_id(package_id)
    row = _PATH_A_SKUS.get(code)
    if row and pid in row:
        return max(1, int(row[pid]))

    from app.integration.market_registry import checkout_price_scale

    scale = checkout_price_scale(code)
    return max(1, int(round(_DE_SKUS[pid] * scale)))


def resolve_path_a_offer(package_id: str, market_code: str) -> FinalOffer:
    """Localized Path A offer — website + repair packages."""
    from app.integration.market_registry import get_market

    pid = normalize_package_id(package_id)
    market = get_market(market_code)
    amount = _sku_amount(market.code, pid)
    label = format_path_a_price(amount, market.symbol)
    return FinalOffer(
        package_id=pid,
        amount=amount,
        currency=market.currency,
        symbol=market.symbol,
        market_code=market.code,
        price_label=label,
    )


def list_path_a_packages(
    market_code: str,
    *,
    package_ids: tuple[str, ...] | None = None,
    deliverables_by_id: dict[str, list[str]] | None = None,
    names_by_id: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Checkout grid rows for a market (default: website tiers only)."""
    from app.integration.market_registry import get_market

    market = get_market(market_code)
    tiers = package_ids or WEBSITE_PACKAGE_IDS
    packages: list[dict[str, Any]] = []
    for tier in tiers:
        offer = resolve_path_a_offer(tier, market.code)
        packages.append(
            {
                "id": tier,
                "name": (names_by_id or {}).get(tier, _default_name(tier)),
                "price_eur": float(offer.amount),
                "currency": offer.currency,
                "symbol": offer.symbol,
                "market_code": offer.market_code,
                "price_label": offer.price_label,
                "deliverables": list((deliverables_by_id or {}).get(tier, [])),
            }
        )
    return {
        "packages": packages,
        "market_code": market.code,
        "currency": market.currency,
        "symbol": market.symbol,
    }


def _default_name(tier: str) -> str:
    return {
        "basic": "Landing Basic",
        "business": "Landing Business",
        "premium": "Landing Premium",
        "repair_lite": "Website Repair Lite",
        "repair_standard": "Website Repair Standard",
        "repair_complete": "Website Repair Complete",
    }.get(tier, tier)


# --- AI Business Bots (separate product; not Path A website) ---------------------

BOT_PACKAGE_IDS: tuple[str, ...] = ("bot_starter", "bot_business", "bot_professional")

# DE anchors — setup one-time + monthly (major units). Market rows override.
_DE_BOT_SKUS: dict[str, dict[str, int]] = {
    "bot_starter": {"setup": 499, "monthly": 99},
    "bot_business": {"setup": 999, "monthly": 199},
    "bot_professional": {"setup": 1499, "monthly": 349},
}

# Curated local-market bot prices (SMB AI chatbot / Telegram+web widget).
_BOT_SKUS: dict[str, dict[str, dict[str, int]]] = {
    "DE": dict(_DE_BOT_SKUS),
    "AT": dict(_DE_BOT_SKUS),
    "CH": {
        "bot_starter": {"setup": 549, "monthly": 119},
        "bot_business": {"setup": 1090, "monthly": 229},
        "bot_professional": {"setup": 1690, "monthly": 399},
    },
    "US": {
        "bot_starter": {"setup": 599, "monthly": 129},
        "bot_business": {"setup": 1199, "monthly": 249},
        "bot_professional": {"setup": 1799, "monthly": 399},
    },
    "CA": {
        "bot_starter": {"setup": 599, "monthly": 129},
        "bot_business": {"setup": 1199, "monthly": 249},
        "bot_professional": {"setup": 1799, "monthly": 399},
    },
    "GB": {
        "bot_starter": {"setup": 449, "monthly": 89},
        "bot_business": {"setup": 899, "monthly": 179},
        "bot_professional": {"setup": 1299, "monthly": 299},
    },
    "AU": {
        "bot_starter": {"setup": 799, "monthly": 149},
        "bot_business": {"setup": 1499, "monthly": 299},
        "bot_professional": {"setup": 2299, "monthly": 449},
    },
    "NZ": {
        "bot_starter": {"setup": 799, "monthly": 149},
        "bot_business": {"setup": 1499, "monthly": 299},
        "bot_professional": {"setup": 2299, "monthly": 449},
    },
    "JP": {
        "bot_starter": {"setup": 88000, "monthly": 16000},
        "bot_business": {"setup": 168000, "monthly": 32000},
        "bot_professional": {"setup": 268000, "monthly": 54000},
    },
    "KR": {
        "bot_starter": {"setup": 790000, "monthly": 140000},
        "bot_business": {"setup": 1490000, "monthly": 280000},
        "bot_professional": {"setup": 2390000, "monthly": 480000},
    },
    "SG": {
        "bot_starter": {"setup": 699, "monthly": 129},
        "bot_business": {"setup": 1299, "monthly": 249},
        "bot_professional": {"setup": 1999, "monthly": 399},
    },
    "NL": {
        "bot_starter": {"setup": 499, "monthly": 99},
        "bot_business": {"setup": 999, "monthly": 199},
        "bot_professional": {"setup": 1499, "monthly": 349},
    },
    "BE": {
        "bot_starter": {"setup": 499, "monthly": 99},
        "bot_business": {"setup": 999, "monthly": 199},
        "bot_professional": {"setup": 1499, "monthly": 349},
    },
    "FR": {
        "bot_starter": {"setup": 499, "monthly": 99},
        "bot_business": {"setup": 999, "monthly": 199},
        "bot_professional": {"setup": 1499, "monthly": 349},
    },
    "IE": {
        "bot_starter": {"setup": 499, "monthly": 99},
        "bot_business": {"setup": 999, "monthly": 199},
        "bot_professional": {"setup": 1499, "monthly": 349},
    },
    "ES": {
        "bot_starter": {"setup": 399, "monthly": 79},
        "bot_business": {"setup": 799, "monthly": 149},
        "bot_professional": {"setup": 1199, "monthly": 279},
    },
    "IT": {
        "bot_starter": {"setup": 399, "monthly": 79},
        "bot_business": {"setup": 799, "monthly": 149},
        "bot_professional": {"setup": 1199, "monthly": 279},
    },
    "PL": {
        "bot_starter": {"setup": 1999, "monthly": 399},
        "bot_business": {"setup": 3999, "monthly": 799},
        "bot_professional": {"setup": 5999, "monthly": 1299},
    },
    "CZ": {
        "bot_starter": {"setup": 12000, "monthly": 2490},
        "bot_business": {"setup": 24900, "monthly": 4990},
        "bot_professional": {"setup": 36900, "monthly": 8490},
    },
    "SE": {
        "bot_starter": {"setup": 5499, "monthly": 1099},
        "bot_business": {"setup": 10999, "monthly": 2199},
        "bot_professional": {"setup": 16499, "monthly": 3799},
    },
    "NO": {
        "bot_starter": {"setup": 5990, "monthly": 1190},
        "bot_business": {"setup": 11990, "monthly": 2390},
        "bot_professional": {"setup": 17990, "monthly": 4190},
    },
    "DK": {
        "bot_starter": {"setup": 3990, "monthly": 799},
        "bot_business": {"setup": 7990, "monthly": 1590},
        "bot_professional": {"setup": 11990, "monthly": 2790},
    },
    "FI": {
        "bot_starter": {"setup": 499, "monthly": 99},
        "bot_business": {"setup": 999, "monthly": 199},
        "bot_professional": {"setup": 1499, "monthly": 349},
    },
    "UA": {
        "bot_starter": {"setup": 18900, "monthly": 3900},
        "bot_business": {"setup": 37900, "monthly": 7900},
        "bot_professional": {"setup": 56900, "monthly": 13900},
    },
    "RU": {
        "bot_starter": {"setup": 49000, "monthly": 9900},
        "bot_business": {"setup": 99000, "monthly": 19900},
        "bot_professional": {"setup": 149000, "monthly": 34900},
    },
    "KZ": {
        "bot_starter": {"setup": 249000, "monthly": 49000},
        "bot_business": {"setup": 499000, "monthly": 99000},
        "bot_professional": {"setup": 749000, "monthly": 179000},
    },
}


@dataclass(frozen=True)
class BotOffer:
    package_id: str
    setup_amount: int
    monthly_amount: int
    currency: str
    symbol: str
    market_code: str
    setup_label: str
    monthly_label: str
    name: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "package_id": self.package_id,
            "setup_amount": self.setup_amount,
            "monthly_amount": self.monthly_amount,
            "currency": self.currency,
            "symbol": self.symbol,
            "market_code": self.market_code,
            "setup_label": self.setup_label,
            "monthly_label": self.monthly_label,
            "price_label": f"{self.setup_label} + {self.monthly_label}/mo",
            "name": self.name,
        }


def normalize_bot_package_id(package_id: str | None) -> str:
    pid = str(package_id or "bot_business").strip().lower()
    if pid in BOT_PACKAGE_IDS:
        return pid
    aliases = {
        "starter": "bot_starter",
        "business": "bot_business",
        "professional": "bot_professional",
        "pro": "bot_professional",
    }
    return aliases.get(pid, "bot_business")


def _bot_sku_amounts(market_code: str, package_id: str) -> tuple[int, int]:
    code = (market_code or "DE").strip().upper() or "DE"
    pid = normalize_bot_package_id(package_id)
    row = (_BOT_SKUS.get(code) or {}).get(pid)
    if row:
        return max(1, int(row["setup"])), max(1, int(row["monthly"]))
    from app.integration.market_registry import checkout_price_scale

    scale = checkout_price_scale(code)
    de = _DE_BOT_SKUS[pid]
    return (
        max(1, int(round(de["setup"] * scale))),
        max(1, int(round(de["monthly"] * scale))),
    )


def _bot_default_name(package_id: str) -> str:
    return {
        "bot_starter": "AI Digital Employee Starter",
        "bot_business": "AI Digital Employee Business",
        "bot_professional": "AI Digital Employee Professional",
    }.get(package_id, package_id)


# Package limit = number of independent AI-bots (not channel count).
BOT_PACKAGE_MAX_BOTS: dict[str, int | None] = {
    "bot_starter": 1,
    "bot_business": 3,
    "bot_professional": None,  # Fair Use
}


def bot_package_max_bots(package_id: str) -> int | None:
    pid = normalize_bot_package_id(package_id)
    return BOT_PACKAGE_MAX_BOTS.get(pid, 1)


_BOT_PACKAGE_FEATURES: dict[str, dict[str, Any]] = {
    "bot_starter": {
        "tagline_ru": "Один цифровой сотрудник — отвечает на вопросы и принимает заявки.",
        "max_bots": 1,
        "max_bots_label": "1 AI-бот",
        "knowledge_sources": "До 1 источника",
        "languages": "1 язык",
        "scenarios": "Базовые",
        "dialog_history": "Базовая",
        "ai_analysis": False,
        "training": "Базовое",
        "extra_channels": "Любой канал",
        "support": "Стандарт",
        "includes_ru": [
            "1 AI-бот (цифровой сотрудник)",
            "Любой канал: Website Chat, Telegram, WhatsApp, Instagram, Messenger",
            "Knowledge Base: до 1 источника",
            "1 язык",
            "Базовые сценарии + передача оператору",
        ],
    },
    "bot_business": {
        "tagline_ru": "До трёх цифровых сотрудников — для разных каналов и задач.",
        "max_bots": 3,
        "max_bots_label": "До 3 AI-ботов",
        "knowledge_sources": "До 5 источников",
        "languages": "До 3 языков",
        "scenarios": "Расширенные",
        "dialog_history": "Расширенная",
        "ai_analysis": True,
        "training": "Регулярное",
        "extra_channels": "Любой канал",
        "support": "Стандарт",
        "includes_ru": [
            "До 3 независимых AI-ботов",
            "Каждый бот — любой поддерживаемый канал",
            "Knowledge Base: до 5 источников",
            "До 3 языков",
            "Расширенные сценарии + AI-анализ обращений",
            "Регулярное обучение",
        ],
    },
    "bot_professional": {
        "tagline_ru": "Команда цифровых сотрудников — Fair Use, полная аналитика, VIP-поддержка.",
        "max_bots": None,
        "max_bots_label": "Fair Use (без жёсткого лимита)",
        "knowledge_sources": "Неограниченно",
        "languages": "Неограниченно",
        "scenarios": "Индивидуальные",
        "dialog_history": "Полная аналитика",
        "ai_analysis": True,
        "training": "Приоритетное",
        "extra_channels": "Любой канал",
        "support": "VIP",
        "includes_ru": [
            "Неограниченное число AI-ботов (Fair Use)",
            "Все каналы по мере появления",
            "Knowledge Base без лимита источников",
            "Неограниченно языков",
            "Индивидуальные сценарии + полная аналитика",
            "VIP-поддержка",
        ],
    },
}


def bot_package_features(package_id: str) -> dict[str, Any]:
    pid = normalize_bot_package_id(package_id)
    return dict(_BOT_PACKAGE_FEATURES.get(pid) or _BOT_PACKAGE_FEATURES["bot_business"])


def resolve_bot_offer(package_id: str, market_code: str) -> BotOffer:
    """Localized AI bot package — setup + monthly in market currency."""
    from app.integration.market_registry import get_market

    pid = normalize_bot_package_id(package_id)
    market = get_market(market_code)
    setup, monthly = _bot_sku_amounts(market.code, pid)
    return BotOffer(
        package_id=pid,
        setup_amount=setup,
        monthly_amount=monthly,
        currency=market.currency,
        symbol=market.symbol,
        market_code=market.code,
        setup_label=format_path_a_price(setup, market.symbol),
        monthly_label=format_path_a_price(monthly, market.symbol),
        name=_bot_default_name(pid),
    )


def list_bot_packages(market_code: str) -> dict[str, Any]:
    """Catalog grid for Virtus Core Bots tab."""
    from app.integration.market_registry import get_market

    market = get_market(market_code)
    packages = []
    for pid in BOT_PACKAGE_IDS:
        offer = resolve_bot_offer(pid, market.code).as_dict()
        feat = bot_package_features(pid)
        offer["tagline_ru"] = feat["tagline_ru"]
        offer["includes_ru"] = feat["includes_ru"]
        offer["features"] = {
            "max_bots": feat.get("max_bots"),
            "max_bots_label": feat.get("max_bots_label"),
            "knowledge_sources": feat["knowledge_sources"],
            "languages": feat["languages"],
            "scenarios": feat["scenarios"],
            "dialog_history": feat["dialog_history"],
            "ai_analysis": feat["ai_analysis"],
            "training": feat["training"],
            "extra_channels": feat["extra_channels"],
            "support": feat["support"],
        }
        packages.append(offer)
    return {
        "product_id": "prod_ai_business_bot",
        "product_name": "AI Digital Employee",
        "packages": packages,
        "market_code": market.code,
        "currency": market.currency,
        "symbol": market.symbol,
        "channels_available": ["Website Chat", "Telegram"],
        "channels_coming_soon": ["WhatsApp", "Instagram", "Facebook Messenger"],
        "channels_note_ru": (
            "Один продукт — AI Digital Employee (AI Sales Assistant). "
            "Каналы не ограничивают тариф: лимит — число независимых AI-сотрудников. "
            "Сейчас подключение: Website Chat, Telegram. "
            "WhatsApp, Instagram, Messenger — после OAuth Meta."
        ),
        "comparison_note_ru": (
            "Разница тарифов — в числе AI-сотрудников (1 / до 3 / Fair Use) и уровне AI: "
            "база знаний, языки, сценарии, аналитика, поддержка. Не в количестве мессенджеров."
        ),
        "note": "Digital employee product — not included in Landing Website packages.",
    }
