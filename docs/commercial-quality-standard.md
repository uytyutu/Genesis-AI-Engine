# Virtus Core — Commercial Quality Standard (SSOT)

## Product

Не **Website Builder**. Не **Website Generator**. Не «AI создаёт сайты».

> **Virtus Core Studio Era** — **Digital Experience Generation**.  
> Virtus Core проектирует впечатление о бизнесе — цифровой опыт, а не страницу.

> **«Создай лучший цифровой опыт для этой ниши и этого бюджета.»**

---

## Freeze: Product Review Week

Пока CEO лично не скажет:

> **«Да, я без стыда покажу это первому клиенту.»**

запрещено:

- Horizon
- новые Directors
- новые AI-модули
- новые фермы / источники

Разрешено только:

- смотреть готовые демо глазами
- улучшать Hero / фото / композицию / карточки / motion / типографику
- чинить существующий UX (память Skip, архив возможностей) — не добавлять «ещё одну систему»

Минимум для глаз: Dental · Restaurant · Law · Auto · Fashion Store · Electronics Store.

---

## Совет директоров

```text
Client Brief
↓
AI Creative Director
↓
Industry · Experience · Luxury · Typography · Motion · Store
Conversion · Trust · Performance · Accessibility · Localization
↓
Experience Replay
↓
CEO Blind Test
↓
Factory
↓
Commercial Ready  (только при CRS ≥ 90)
```

**Правило:** каждое решение меняет HTML / CSS / ассеты / поведение — не только `meta`.

Код: `dashboard/backend/app/factory/visual_intelligence/studio/`

---

## Главный KPI

Не Overall. Не тесты. Не количество Directors.

> **«Показал бы я этот сайт своему первому клиенту без стыда?»**

Для магазина отдельно:

> **«Купил бы я здесь товар?»**

Если «нет» — CRS и Blind Test не спасают релиз.

Коммерческие якоря:

- Premium: «За 699 € это выглядит достойно.»
- Store: «Я бы доверил этому магазину продавать товары.»

**CRS ≥ 90** — автоматический proxy; финальный вердикт — глаза CEO после **Commercial Gallery** (не «демо кода»).

Процесс:

```text
Код → пересборка Commercial Gallery → CEO Visual Review → глазами → следующая задача
```

Любое изменение Visual Studio → `scripts/visual_reality_rebuild.py`.

Код: `studio/commercial_readiness.py`, `integration/ceo_visual_review.py`

### Sprint order (Product Review Week)

1. **Premium Store** — фото товаров, Hero, баннер, витрина («Купил бы я здесь товар?»)
2. **Website ladder** — Starter / Business / Premium читаются за 5 секунд без текста
3. **Niches** — разные Digital Experience profiles (не один шаблон)

### Future (не сейчас)

- **Luxury Merch Director** — после PASS Premium Store: композиция витрины под нишу.

### Psychology Experience (профильная ниша)

Отдельный Digital Experience profile — см. `docs/psychology-experience.md`.  
Не копия medical: Calm Clinical / Therapy Trust, портрет специалиста, спокойная витрина цифровых услуг.

---

## Business Directors

### Conversion Director
Переставляет CTA / форму / trust / FAQ ради конверсии. Может вставить второй CTA после услуг.

### Trust Director
Особенно dental / law / auto / handwerk: сертификаты у Hero, гарантии, отзывы, карта + контакты.

### Performance Director
Video Hero с Mobile Score FAIL → статичный Hero + лёгкая анимация.

### Accessibility Director
Контраст, focus-visible, alt, skip-link, reduced-motion.

### Localization Director
DE: Impressum/Datenschutz, строгий стиль · FR: больше портфолио · ES: social proof · US: прямой CTA.

---

## CEO Blind Test

5 секунд без ценников: Starter / Business / Premium. FAIL → Premium Luxury rebuild.

---

## Experience Replay

`experience_replay.json` — почему такой сайт (включая CRS и Conversion recommendations).

---

## Order of work

```text
Business Directors → HTML
        ↓
Commercial Readiness ≥ 90
        ↓
CEO Blind Test PASS
        ↓
Production DNS / OVH
        ↓
Horizon
```
