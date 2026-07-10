"""
Genesis Knowledge Layer — what Genesis knows about itself.

Products, departments, subscriptions, commercial catalog — shared by LLM and Local Mind.
Source of truth for pricing: app/memory/pricing_display.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.integration.genesis_brain.public_brand import ASSISTANT_NAME, BRAND_NAME, STUDIO_NAME
from app.integration.public_truth_catalog import (
    MISSION1_LANDING_TIMELINE,
    build_mission1_vector_commerce_rules,
    load_public_pricing_display,
    min_landing_price_eur,
    studio_unavailable_message,
)

_DEFAULT_MEMORY = Path(__file__).resolve().parents[3] / "memory"


class GenesisKnowledgeLayer:
    """Structured Genesis product & company knowledge (not provider docs)."""

    def __init__(
        self,
        packages: list[dict[str, Any]] | None = None,
        *,
        memory_dir: Path | None = None,
    ) -> None:
        self._packages = packages or []
        self._memory = memory_dir or _DEFAULT_MEMORY
        self._pricing = load_public_pricing_display(self._memory)

    def _load_pricing_display(self) -> dict[str, Any]:
        return load_public_pricing_display(self._memory)

    def _load_dialogue_examples(self, *, limit: int = 12) -> str:
        """Human conversation patterns — few-shot tone for LLM (not training data)."""
        path = self._memory / "dialogue_examples" / "human_patterns.jsonl"
        if not path.is_file():
            return ""
        lines: list[str] = []
        try:
            for raw in path.read_text(encoding="utf-8").splitlines():
                raw = raw.strip()
                if not raw:
                    continue
                try:
                    row = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if row.get("_readme"):
                    continue
                user = (row.get("user") or "").strip()
                feeling = (row.get("feeling") or "").strip()
                if user and feeling:
                    lines.append(
                        f"Пользователь: {user}\n"
                        f"Нужный тон: {feeling}. "
                        f"Ответь своими словами — не повторяй заготовки."
                    )
                elif user:
                    lines.append(f"Пользователь: {user}\nОтветь живо, без шаблонов.")
                if len(lines) >= limit:
                    break
        except OSError:
            return ""
        if not lines:
            return ""
        return (
            "## Примеры тона (только направление — не копируй готовые фразы)\n"
            + "\n\n---\n\n".join(lines)
        )

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
        pkg_lines = []
        for p in self._packages:
            deliverables = p.get("deliverables") or []
            d = "; ".join(deliverables[:4]) if deliverables else ""
            pkg_lines.append(f"- {p['name']} ({p['id']}): {p['price_eur']} € — {d}")
        packages_block = "\n".join(pkg_lines) if pkg_lines else "- Landing (basic): 350 € — онлайн-заказ"

        svp = self._pricing.get("service_vs_product") or {}
        anti = self._pricing.get("anti_cannibalization") or {}
        min_p = min_landing_price_eur(self._packages)
        service_when = svp.get(
            "service_when",
            "Один готовый лендинг → услуга на /order.",
        )
        product_when = svp.get(
            "product_when",
            f"{STUDIO_NAME} пока в разработке — не предлагать покупку. Сейчас: цифровая компания и заказ лендинга.",
        )
        anti_example = anti.get(
            "example_one_site",
            f"Один лендинг → пакеты от {min_p} € на /order. Подписка Studio сейчас недоступна.",
        )

        catalog = self._format_service_catalog()
        subs = self._format_subscriptions()
        capabilities = self._format_capabilities()
        dialogue_examples = self._load_dialogue_examples()

        catalog_section = catalog or (
            f"- Landing Page от {min_p} € (заказ онлайн на /order)\n"
            f"- Срок ориентир: {MISSION1_LANDING_TIMELINE}"
        )
        subs_section = subs or (
            f"- Free — работа с {ASSISTANT_NAME} в цифровой компании\n"
            f"- {STUDIO_NAME} — в разработке, купить нельзя"
        )
        caps_section = capabilities or (
            f"Mission 1: лендинг под ключ и консультация {ASSISTANT_NAME}. "
            "Магазин, боты, приложения — пока не в онлайн-каталоге."
        )
        mission1_rules = build_mission1_vector_commerce_rules(self._packages)

        return f"""## Mission 1 — публичная правда ({BRAND_NAME})
{mission1_rules}

## Product Mind — разговор, не каталог
**{ASSISTANT_NAME} консультирует, не продаёт:**
- Один лендинг → /order (350 / 650 / 1200 €)
- Studio / подписки → честно «в разработке»
- Магазин, бот, приложение → «пока нельзя оформить онлайн»
- **Не говорить:** «Перейдите в раздел Services» без контекста

**Когда что предложить:**
- {service_when}
- {product_when}

**Один сайт — честно:**
- {anti_example}

{dialogue_examples}

## Каталог услуг (только доступное онлайн)
{catalog_section}

Онлайн-заказ: {packages_block}
Страница заказа: `/order`

## Подписки и платформа
{subs_section}

## Возможности (не обещать как готовый продукт)
{caps_section}

## Как продавать ({ASSISTANT_NAME})
1. Понять **задачу**, не тариф.
2. Лендинг → `/order`. Сказать цену из пакетов выше.
3. Studio → {studio_unavailable_message().split(chr(10))[0]}
4. **Полезность > выручка** — консультант, не кассир."""
