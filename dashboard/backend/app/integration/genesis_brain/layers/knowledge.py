"""
Genesis Knowledge Layer — factual product catalog for Virtus Core.

Products, prices, capabilities, limitations — no tone, selling, or personality instructions.
Behavior lives in Core Prompt and Journey; this layer is facts only.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME
from app.integration.public_truth_catalog import (
    MISSION1_LANDING_TIMELINE,
    load_public_pricing_display,
    min_landing_price_eur,
)

_DEFAULT_MEMORY = Path(__file__).resolve().parents[3] / "memory"


class GenesisKnowledgeLayer:
    """Structured Virtus Core product facts (not provider docs, not behavior)."""

    def __init__(
        self,
        packages: list[dict[str, Any]] | None = None,
        *,
        memory_dir: Path | None = None,
    ) -> None:
        self._packages = packages or []
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._pricing = load_public_pricing_display(self._memory)

    def _format_service_catalog(self) -> str:
        categories = self._pricing.get("service_categories") or []
        if not categories:
            return ""
        lines: list[str] = []
        for cat in categories:
            lines.append(f"### {cat.get('name', '')}")
            desc = cat.get("description") or ""
            if desc:
                lines.append(desc)
            for item in cat.get("items") or []:
                timeline = item.get("timeline") or ""
                tl = f", срок {timeline}" if timeline else ""
                avail = " — заказ онлайн" if item.get("available") else " — по запросу"
                lines.append(
                    f"- **{item.get('name')}** ({item.get('price_label', '')}{tl}){avail}: "
                    f"{item.get('description', '')}"
                )
        return "\n".join(lines)

    def _format_subscriptions(self) -> str:
        subs = self._pricing.get("subscriptions") or []
        if not subs:
            return ""
        lines: list[str] = []
        for s in subs:
            tag = s.get("tagline") or ""
            tag_part = f" — {tag}" if tag else ""
            lines.append(
                f"- **{s.get('name')}** {s.get('price_label', '')}{s.get('period', '')}"
                f"{tag_part}: {s.get('audience', '')}"
            )
        return "\n".join(lines)

    def _format_capabilities(self) -> str:
        caps = self._pricing.get("capabilities") or {}
        groups = caps.get("groups") or []
        if not groups:
            return ""
        lines = [caps.get("subheadline", ""), caps.get("value_anchor", "")]
        for g in groups:
            items = ", ".join(g.get("items") or [])
            lines.append(f"- {g.get('title')}: {items}")
        return "\n".join(x for x in lines if x)

    def build_block(self) -> str:
        """Factual catalog block — injected as reference, not as hidden behavior prompt."""
        pkg_lines = []
        for p in self._packages:
            deliverables = p.get("deliverables") or []
            d = "; ".join(deliverables[:4]) if deliverables else ""
            pkg_lines.append(f"- {p['name']} ({p['id']}): {p['price_eur']} € — {d}")
        packages_block = "\n".join(pkg_lines) if pkg_lines else "- Landing (basic): 199 € — онлайн-заказ"

        svp = self._pricing.get("service_vs_product") or {}
        anti = self._pricing.get("anti_cannibalization") or {}
        min_p = min_landing_price_eur(self._packages)
        service_when = svp.get(
            "service_when",
            "Один готовый лендинг → услуга на /order.",
        )
        product_when = svp.get(
            "product_when",
            f"{STUDIO_NAME} — в разработке, онлайн-покупка недоступна.",
        )
        anti_example = anti.get(
            "example_one_site",
            f"Один лендинг → пакеты от {min_p} € на /order. Подписка Studio недоступна.",
        )

        catalog = self._format_service_catalog()
        subs = self._format_subscriptions()
        capabilities = self._format_capabilities()

        catalog_section = catalog or (
            f"- Landing Page от {min_p} € (заказ онлайн на /order)\n"
            f"- Срок ориентир: {MISSION1_LANDING_TIMELINE}"
        )
        subs_section = subs or (
            f"- Free — работа с {ASSISTANT_NAME} в цифровой компании\n"
            f"- {STUDIO_NAME} — в разработке, купить нельзя"
        )
        caps_section = capabilities or (
            "Mission 1: лендинг под ключ, AI Bot (Telegram + website chat), "
            "анализ/ремонт/SEO/speed/security/Google Business/миграция — онлайн-заказ."
        )

        return f"""## Каталог {BRAND_NAME} (факты)

### Услуги
{catalog_section}

### Пакеты лендинга (/order)
{packages_block}
Срок ориентир: {MISSION1_LANDING_TIMELINE}

### AI Bot (отдельно от сайта)
- AI Bot Starter — от 499 € setup + 99 €/мес (Website chat + Telegram)
- AI Bot Business — от 999 € setup + 199 €/мес
- AI Bot Professional — от 1499 € setup + 349 €/мес
- WhatsApp / Instagram каналы — в разработке, не продавать как готовые
- Заказ: /order/bot или /site?service=bots

### Подписки и платформа
{subs_section}

### Возможности (каталог)
{caps_section}

### Ограничения и доступность
- Путь покупки всегда: карточка → форма заказа (данные) → оплата (если услуга live).
- Live checkout: лендинг (/order), AI Digital Employee (/order/bot), анализ (/order/service/ai_website_analysis),
  ремонт Website Repair (/order/service/website_repair).
- Coming Soon (форма интереса, без оплаты): SEO, Speed, Security, Google Business, миграция —
  ссылки /order/service/<id>. Не обещай мгновенную доставку этих услуг.
- CRM / глубокая Automation как подписка — Coming Soon (не продавать checkout)
- WhatsApp / Instagram bot channels — Coming Soon
- {STUDIO_NAME}: в разработке, купить нельзя
- Гостевой заказ без регистрации разрешён; кабинет — опционально
- {service_when}
- {product_when}
- {anti_example}

### Поведение консультанта
- На вопросы о продуктах отвечай как консультант {BRAND_NAME}: тарифы, отличия, процесс заказа
- Веди на форму услуги: /order, /order/bot или /order/service/<id> — не на главную «искать самому»
- Сначала форма (что нужно клиенту), потом оплата — никогда сразу в Stripe без данных
"""
