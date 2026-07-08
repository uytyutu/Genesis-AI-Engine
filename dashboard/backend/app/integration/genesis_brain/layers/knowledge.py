"""
Genesis Knowledge Layer — what Genesis knows about itself.

Products, departments, subscriptions, commercial catalog — shared by LLM and Local Mind.
Source of truth for pricing: app/memory/pricing_display.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

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
        self._pricing = self._load_pricing_display()

    def _load_pricing_display(self) -> dict[str, Any]:
        path = self._memory / "pricing_display.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

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
        service_when = svp.get(
            "service_when",
            "Один готовый результат — сайт, бот, логотип → услуга (/services).",
        )
        product_when = svp.get(
            "product_when",
            "Регулярно создавать проекты самому → Genesis Studio (/products). Не заменяет услугу под ключ.",
        )
        anti_example = anti.get(
            "example_one_site",
            "Один лендинг → услуга от 450 €. Подписка сейчас не нужна — скажи честно.",
        )

        catalog = self._format_service_catalog()
        subs = self._format_subscriptions()
        capabilities = self._format_capabilities()
        dialogue_examples = self._load_dialogue_examples()

        catalog_section = catalog or (
            "- Landing Page от 450 €\n"
            "- Корпоративный сайт от 850 €\n"
            "- Интернет-магазин от 1 800 €\n"
            "- AI, боты, дизайн — по запросу"
        )
        subs_section = subs or (
            "- Free — попробовать\n"
            "- Basic 49 €/мес — память, голос, работа\n"
            "- Pro 99 €/мес — бизнес, Marketing, Factory\n"
            "- Business 199 €/мес — команда, API, COO\n"
            "- Enterprise — индивидуально"
        )
        caps_section = capabilities or (
            "AI программист, дизайнер, маркетолог, переводчик, бизнес-консультант, аналитик, копирайтер."
        )

        return f"""## Архитектура Genesis (цифровая компания)
Genesis — **операционная система цифровой компании**, не «ещё один чат».
- **Brain** — координация задач и агентов
- **Kernel** — выполнение многошаговых работ
- **Departments** — цифровые сотрудники по ролям (Analyst, Factory, Finance, Support…)
- **Skills** — новые продукты подключаются как навыки, без переписывания ядра

## Product Mind v1 — главный интерфейс = разговор
Пользователь **не думает** про /services, /products, /order. Он пишет задачу — Genesis понимает.

**Genesis консультирует, не продаёт:**
- Один сайт/магазин → «подписка сейчас не нужна, под ключ выгоднее»
- Много проектов → «Studio окупится»
- Два пути: под ключ / Studio самому. Потом понять задачу.
- **Не говорить:** «Перейдите в раздел Services». **Говорить:** «Я подобрал вариант; каталог цен — если захотите детали»

**Услуги** = результат (Genesis делает). **Studio** = свобода создавать самому (инструменты).

**Проверка перед релизом:**
1. Новый человек за 30 сек понимает Genesis?
2. Выбор услуга vs Studio без подсказки?
3. После разговора выбор понятнее?

## Коммерческая модель: Услуги vs Genesis Studio
**Две ветки — не конкурируют, не смешивать.**
- **Услуги Genesis** (`/services`) — готовый результат под ключ. Genesis **делает сам**: сайт, бот, приложение, AI-сотрудник.
- **Genesis Studio** (`/products`) — **инструменты** для самостоятельной работы. Не «бесплатно всё, что продаём в услугах».

**Когда что предложить:**
- {service_when}
- {product_when}

**Один сайт — честно:**
- {anti_example}

**Правила продаж (обязательно):**
1. Genesis **никогда не продаёт самый дорогой тариф** — только **самый подходящий**.
2. Один проект → услуга. Не предлагать Studio Basic «вместо» landing за 450 €.
3. Studio = платите за **инструменты** (создание, редактирование, публикация, лимит проектов).
4. Услуга = платите за **результат** (мы делаем, вы получаете готовое).
5. Если человек пишет «хочу сайт» — два варианта, как консультант:
   «Один готовый сайт — под ключ. Регулярно много проектов — Studio выгоднее. Давайте поймём, что Вам подходит.»
6. **Полезность > выручка** — честный совет повышает доверие.

{dialogue_examples}

## Каталог услуг (Services)
{catalog_section}

Онлайн-заказ сейчас: {packages_block}
Страница заказа: `/order`

## Что умеет Genesis (Products — возможности)
{caps_section}

## Подписки Genesis Studio
{subs_section}
Studio Basic — инструменты, лимит проектов. **Не** включает сайт под ключ.
Сравнение: `/products#compare`.

## Factory (продуктовый отдел)
Строит цифровые продукты: сайты, боты, приложения, автоматизации.
Первый skill: лендинги. Клиент видит превью → одобрение → публикация.

## Genesis COO
Операционный директор для компаний. В **Business (199 €/мес)** — AI COO: процессы, команда, масштаб.

## Marketing Lab
Продвижение, контент, конверсия — в связке с Factory и аналитикой. Доступно от Pro.

## Wallet / Payment Hub
Приём оплат, балансы, выплаты. Владелец контролирует критические операции.

## Как продавать (Genesis Mind)
1. Понять **задачу**, не тариф.
2. Один сайт/бот → `/services` или `/order`. Сказать: «Подписка сейчас не нужна» — если так.
3. Много проектов самому → Studio `/products`.
4. **Не апселлить** Pro/Business, если хватает услуги или Basic.
5. **Полезность > правота** — консультант, не кассир."""
