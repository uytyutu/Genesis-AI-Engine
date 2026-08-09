# Premium Acceptance (human eyes only)

Не AI Score. Не Overall. Не `data-luxury`. Не тесты.

## Freeze

Пока CEO лично не скажет: **«Да, я без стыда покажу это первому клиенту.»**

- ❌ Horizon · новые Directors · новые AI-модули · новые фермы
- ✅ Только глаза + улучшение Hero / фото / композиции / карточек / motion / типографики
- ✅ Чинить память Skip / архив возможностей (существующий UX) — не «ещё одну систему»

Минимум для глаз: Dental · Restaurant · Law · Auto · Fashion Store · Electronics Store.

## Главный KPI

> **«Показал бы я этот сайт своему первому клиенту без стыда?»**

Если ответ «нет» — Directors, тесты и оценки не имеют значения.

Коммерческие вопросы рядом:

- Premium: **«Да, за 699 € это выглядит достойно.»**
- Store: **«Да, я бы доверил этому магазину продавать товары.»**

## Процесс после каждого изменения Visual Studio

```text
Написали код
↓
Пересобрали Commercial Gallery (обязательно)
↓
Открыли Starter / Business / Premium / Store
↓
Проверили глазами
↓
Только потом следующая задача
```

Правило Factory:

> **Любое изменение Visual Studio автоматически пересобирает Commercial Gallery.**

Скрипт: `py -3.12 scripts/visual_reality_rebuild.py` (`--ceo-only` / `--full`).

## Gate: CEO Visual Review

После пересборки обязательно смотреть:

| Websites | Stores |
|----------|--------|
| Starter Dental | Starter Store |
| Business Dental | Business Store |
| Premium Dental | Premium Store |

Если хотя бы один выглядит как старый шаблон → **CEO Visual Review FAIL** → релиз не проходит.

**Premium Character / Design DNA (обязательно):** не cream-paper scroll, не пустые плитки, не один skin на все тиры. За 3–5 секунд — «дорого и профессионально», без чтения текста. Starter тоже без стыда. Business ≥ качество Virtus Core (`/site` principles). Premium > Virtus. Никогда не клон Virtus UI. Psychology — proof-ниша (`docs/psychology-experience.md`, `docs/design-dna.md`).

Авто-часть: `app.integration.ceo_visual_review` (файлы не тонкие, tier/luxury маркеры, UX без пустоты, store chrome).  
Человек всё равно открывает URL и отвечает на KPI.

## Checklist (глаза) — Premium Store

Три вопроса (телефон):

1. Я доверил бы этому магазину свои деньги?
2. За 5 секунд понятно, что это Premium?
3. Уровень современных e-commerce, не шаблонная витрина?

Если хоть один «нет» — только визуал/UX магазина, не новые модули.

Минимум на витрине:

- [ ] Hero: что продаём / почему здесь / преимущества / CTA
- [ ] Trust: доставка, возврат, оплата, контакты, гарантия
- [ ] Карточки: фото, цена, бейджи, покупка, hover
- [ ] PDP: галерея, zoom, описание, характеристики, варианты, related, recently viewed
- [ ] Mobile: меню, поиск, карточки, кнопки покупки

После деплоя — телефон и компьютер:

- [ ] За 5 секунд видно разницу Starter < Business < Premium?
- [ ] Premium: показал бы первому клиенту без стыда?
- [ ] Store: доверил бы продавать товары?
- [ ] Нет пустых блоков / placeholder
- [ ] Ощущение студии, не шаблона
- [ ] Mobile на уровне desktop
- [ ] Premium Store ощущается не хуже Premium Website

### Store (обязательный чек-лист)

- [ ] Hero / баннер
- [ ] Категории
- [ ] Карточки товаров
- [ ] Поиск
- [ ] Фильтры
- [ ] Login / Register
- [ ] Кабинет покупателя
- [ ] Checkout
- [ ] Рекомендации
- [ ] Premium Motion (где уместно)

## Разнообразие Premium (не один сайт)

Factory должна уметь разные ниши высокого уровня — не форсировать 3D везде.
Сама выбирает медиа (фото / видео / Lottie / Canvas / 3D) по нише.

**Websites:** стоматология, юрист, ресторан, автосервис, недвижимость, солнечная энергетика.  
**Stores:** обувь, косметика, электроника, мебель, аксессуары.

Цикл: **сгенерировал → посмотрел → улучшил → пересобрал.**  
Новые модули / Directors — только после human PASS.

## Farm (отдельно)

Доказано только после:

```text
Approve → Clone → Patch → Tests → Draft PR
```

`Started > 0` — ещё не доказательство.
