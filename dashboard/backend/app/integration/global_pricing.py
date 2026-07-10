"""Global pricing — preliminary project estimates (after concept approval).

Orientational ranges from market_registry; project type + complexity shape final quote.
Price is NOT shown at dialog start — only after concept is approved.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.integration.market_localization import resolve_localized_commerce
from app.integration.market_registry import (
    MARKET_DEFAULT,
    PROJECT_BUSINESS_WEBSITE,
    format_amount,
    get_market,
    project_type_label,
    registry_summary_for_vector,
)
from app.integration.market_context import ProjectMarketContext
from app.integration.product_line import ASSISTANT_NAME, BRAND_NAME, SERVICE_WEBSITE

COMPLEXITY_LINE_ITEMS: tuple[tuple[str, str, int], ...] = (
    ("pages_extra", "Дополнительные страницы (свыше 1)", 80),
    ("ecommerce", "Интернет-магазин / каталог", 250),
    ("forms_advanced", "Расширенные формы и интеграции", 120),
    ("seo_extended", "Расширенное SEO", 100),
    ("multilingual", "Многоязычность (каждый доп. язык)", 150),
    ("legal_pages", "Юридические страницы по требованиям страны", 80),
    ("gdpr_setup", "GDPR / Datenschutz настройка", 60),
)

ADD_ON_SERVICES: tuple[dict[str, Any], ...] = (
    {"id": "domain", "name_ru": "Регистрация домена", "pricing": "отдельно"},
    {"id": "hosting", "name_ru": "Хостинг", "pricing": "отдельно"},
    {"id": "publish", "name_ru": "Публикация", "pricing": "отдельно"},
    {"id": "email", "name_ru": "Корпоративная почта", "pricing": "отдельно"},
    {"id": "seo_promo", "name_ru": "SEO-продвижение", "pricing": "отдельно"},
    {"id": "subscription_support", "name_ru": "Сопровождение по подписке", "pricing": "Vector Pro (скоро)"},
)

BASE_ESTIMATE_INCLUDES: tuple[str, ...] = (
    "дизайн",
    "адаптация под мобильные устройства",
    "базовая оптимизация",
    "SEO-основа",
    "исходный код",
    "инструкции",
    "архив проекта",
)


@dataclass
class ProjectComplexity:
    pages: int = 1
    mobile: bool = True
    ecommerce: bool = False
    forms_advanced: bool = False
    seo_extended: bool = False
    multilingual_languages: int = 1
    legal_pages: bool = False
    gdpr_setup: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ProjectComplexity:
        if not data:
            return cls()
        return cls(
            pages=max(1, int(data.get("pages") or 1)),
            mobile=bool(data.get("mobile", True)),
            ecommerce=bool(data.get("ecommerce")),
            forms_advanced=bool(data.get("forms_advanced")),
            seo_extended=bool(data.get("seo_extended")),
            multilingual_languages=max(1, int(data.get("multilingual_languages") or 1)),
            legal_pages=bool(data.get("legal_pages")),
            gdpr_setup=bool(data.get("gdpr_setup")),
        )


@dataclass
class PreliminaryProjectEstimate:
    service_id: str
    project_type: str
    market_code: str
    currency: str
    symbol: str
    amount_min: int
    amount_typical: int
    amount_max: int
    includes: list[str] = field(default_factory=list)
    complexity_notes: list[str] = field(default_factory=list)
    policy_note: str = ""

    def format_range_label(self) -> str:
        lo = format_amount(self.amount_min, self.symbol)
        hi = format_amount(self.amount_max, self.symbol)
        return f"{lo} – {hi}"


def _complexity_notes(cx: ProjectComplexity) -> list[str]:
    notes: list[str] = []
    if cx.pages > 1:
        notes.append(f"страниц: {cx.pages}")
    if cx.ecommerce:
        notes.append("интернет-магазин")
    if cx.forms_advanced:
        notes.append("расширенные формы")
    if cx.seo_extended:
        notes.append("расширенное SEO")
    if cx.multilingual_languages > 1:
        notes.append(f"языков: {cx.multilingual_languages}")
    if cx.legal_pages:
        notes.append("юридические страницы")
    if cx.gdpr_setup:
        notes.append("GDPR / Datenschutz")
    return notes


def build_preliminary_project_estimate(
    market_code: str,
    *,
    project_type: str = PROJECT_BUSINESS_WEBSITE,
    service_id: str = SERVICE_WEBSITE,
    complexity: ProjectComplexity | None = None,
) -> PreliminaryProjectEstimate | None:
    """Market band + project type; complexity noted for final quote."""
    cx = complexity or ProjectComplexity()
    market = get_market(market_code)
    if service_id == SERVICE_WEBSITE:
        band = market.project_range(project_type)
    else:
        band = market.service_range(service_id)
    if not band:
        return None

    includes = list(BASE_ESTIMATE_INCLUDES)
    if market.legal_requirements and (cx.legal_pages or market.requires):
        includes.append(f"юридические страницы ({', '.join(market.legal_requirements[:2])})")

    return PreliminaryProjectEstimate(
        service_id=service_id,
        project_type=project_type,
        market_code=market.code,
        currency=market.currency,
        symbol=market.symbol,
        amount_min=band.from_amount,
        amount_typical=band.average_market,
        amount_max=band.to_amount,
        includes=includes,
        complexity_notes=_complexity_notes(cx),
        policy_note=(
            f"После согласования структуры, функций и содержания — точная смета в {BRAND_NAME}."
        ),
    )


def estimate_for_market(
    service_id: str,
    ctx: ProjectMarketContext,
    complexity: ProjectComplexity | None = None,
    *,
    project_type: str = PROJECT_BUSINESS_WEBSITE,
) -> PreliminaryProjectEstimate | None:
    code = ctx.target_market_code or MARKET_DEFAULT
    return build_preliminary_project_estimate(
        code, project_type=project_type, service_id=service_id, complexity=complexity
    )


def format_preliminary_project_estimate(
    estimate: PreliminaryProjectEstimate,
    *,
    market_name: str | None = None,
    locale: str = "ru",
) -> str:
    """Shown **after concept approval** — not at dialog start."""
    solution = project_type_label(estimate.project_type, locale=locale)
    market_line = market_name or estimate.market_code
    includes = "\n".join(f"✓ {item}" for item in estimate.includes)
    lines = [
        f"**Предварительная смета проекта**",
        f"Решение: **{solution}** · рынок **{market_line}** ({estimate.currency})",
        "",
        "Для подобных проектов на этом рынке обычно:",
        f"**{estimate.format_range_label()}**",
        f"(средний ориентир рынка: {format_amount(estimate.amount_typical, estimate.symbol)})",
        "",
        "Что входит в типовой проект:",
        includes,
    ]
    if estimate.complexity_notes:
        lines.extend([
            "",
            "Уточнения по вашему проекту (влияют на финальную смету):",
            "\n".join(f"• {n}" for n in estimate.complexity_notes),
        ])
    lines.extend([
        "",
        estimate.policy_note,
        "",
        "Далее — разовая покупка с передачей результата или подписка для развития проекта.",
    ])
    return "\n".join(lines)


def format_preliminary_after_approval(
    ctx: ProjectMarketContext,
    *,
    project_type: str = PROJECT_BUSINESS_WEBSITE,
    complexity: ProjectComplexity | None = None,
    locale: str = "ru",
) -> str:
    commerce = resolve_localized_commerce(ctx)
    est = build_preliminary_project_estimate(
        commerce.market_code, project_type=project_type, complexity=complexity
    )
    if not est:
        return (
            "Подготовлю **предварительную смету проекта** после уточнения типа решения и рынка."
        )
    return format_preliminary_project_estimate(
        est, market_name=commerce.market_name, locale=locale
    )


# Backward compat aliases
PriceEstimate = PreliminaryProjectEstimate
estimate_website_price = lambda code, cx=None: build_preliminary_project_estimate(
    code, project_type=PROJECT_BUSINESS_WEBSITE, complexity=cx
)
format_transparent_estimate = format_preliminary_project_estimate


def global_pricing_rules_for_vector() -> str:
    complexity = "\n".join(f"• {label}" for _, label, _ in COMPLEXITY_LINE_ITEMS)
    addons = "\n".join(f"• {a['name_ru']} — {a['pricing']}" for a in ADD_ON_SERVICES)
    project_types = ", ".join(
        project_type_label(pt) for pt in (
            "landing_page", "business_website", "corporate_website", "online_store",
            "restaurant_website", "medical_website",
        )
    )

    return f"""## Глобальная ценовая политика {BRAND_NAME}

Говорите **«предварительная смета проекта»**, не «стоимость сайта».
Продаём **готовое цифровое решение** (Business Website, Online Store, Medical Website…).

### Когда показывать цену
1. Диалог → концепция → итерации → **«Вам нравится? ДА»**
2. **Только после согласования концепции** — предварительная смета проекта.
3. **Не** называть цену в первом сообщении диалога.

### Типы решений (влияют на диапазон)
{project_types}

### Global Market Database v1 (29 рынков)
{registry_summary_for_vector()}

Расширение: только `market_registry_v1.py`. Market Intelligence → CEO → Approve.

### Финальная смета
После согласования структуры, функций и содержания — точная смета с учётом:
{complexity}

### Дополнительно (отдельно)
{addons}

### Mission 1 checkout
`/order` — операционные EUR-пакеты. В диалоге — **предварительная смета** в валюте целевого рынка.
"""
