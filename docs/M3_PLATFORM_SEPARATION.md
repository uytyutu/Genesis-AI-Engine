# M3 — Platform Separation

**Status:** **ACTIVE** (CEO START PASS, 2026-07-11)  
**Source of truth:** `docs/PRODUCT_DEFINITION_v1.md` (ACCEPTED FINAL)  
**Registry:** `dashboard/platform/surface_registry.json` (M3.2)

---

## Unity principle (M3.2+)

Три поверхности — **один Virtus Core**. Совпадают: брендинг · язык · стиль · Vector · дизайн · философия.

> На любой поверхности: **«Я работаю с Vector.»**

Навигация **помогает** Vector — не заменяет его.

**M3.2 scope:** только навигация и оболочка. **Не трогаем:** Product Truth · Planner · Memory · Delivery · бизнес-логику.

---

## M3 Principle

> **Во время M3 пользователь не должен потерять ни одной возможности, которой уже пользуется.**

Platform Separation — **перенос продукта**, не переписывание.

---

## Migration rules (until M7 complete)

### Rule 1 — Copy first, delete later

**Forbidden:**
```
Удалить /site → потом написать Client App
```

**Correct:**
```
Рабочий Client App → проверка → только потом убрать с Public Website
```

Пока новая поверхность не работает на 100%, старая остаётся.

### Rule 2 — One logic source

Не копировать бизнес-логику. Переносить только **интерфейс (оболочку)**.

Shared kernel (unchanged):
- Product Truth · Delivery · Memory · Planner · Identity · Kernel

### Rule 3 — Genesis.exe works after every slice

После каждого подэтапа:
- ✅ запускается
- ✅ Vector работает
- ✅ проекты работают
- ✅ сайт работает (пока не slimmed intentionally in M3.3+)

Никаких промежуточных состояний «сломано, потом починим».

### Rule 4 — UX over elegant code

Если перенос технически правильный, но человеку **менее понятно** — перенос **не принят**.

---

## Slice gate (after every slice)

1. Может ли **новый** пользователь начать пользоваться продуктом?
2. Может ли **текущий** клиент продолжить работу **без потерь**?
3. Может ли **CEO** продолжать управлять компанией?

**Любой «нет» → slice незавершён.**

---

## M3 breakdown

| Slice | Name | Deliverable | Verify via Genesis.exe |
|-------|------|-------------|------------------------|
| **M3.1** | Surface Registry | ✅ PASS | `surface_registry.json` + loaders |
| **M3.2** | Navigation Separation | ✅ PASS | Public / Client / CEO nav shells |
| **M3.3** | Public Website Slim | ✅ PASS* | Витрина · funnel · workspace на `/projects` |
| **M3.4** | Client Workspace Primary | **NEXT** | Одна компания · Vector в центре |
| **M3.5** | Verification | Full regression | 3 gate questions = yes |

---

## Three surfaces (target)

| Surface | Role | Test |
|---------|------|------|
| 🌐 **Public** | Витрина → желание установить | Нельзя полноценно работать только на сайте |
| 💻 **Client** | Цифровая компания · Vector главный | «Открыл свою компанию» |
| 👑 **CEO** | Кабинет владельца · MC = решения | Не админ-панель |

---

## M3.1 — Surface Registry ✅

**Done when:**
- Every frontend route classified: `public` | `client` | `ceo`
- Overlaps documented with `migration_note` (no deletion until later slice)
- API prefixes mapped (public vs owner vs shared logic)
- AppShell `MC_PREFIXES` aligned with registry CEO routes

**Not in M3.1:** removing routes, changing navigation, slimming /site.

---

## M3.2 — Navigation Separation ✅

**Done when:**
- `AppShell` resolves `public` | `client` | `ceo` navigation surfaces
- `VirtusSurfaceIdentity` — единый бренд + сценарий на каждой поверхности
- Public nav: Главная → Vector → Услуги → Тарифы → Скачать
- Client nav shell on `/projects` (остальные client routes — по ссылкам, shell в M3.4)
- CEO nav: Пульт → Factory → Финансы → Стратегия (+ студии, система)
- **Ничего не удалено** · kernel не изменён

**Code:** `surfaceNavConfig.ts` · `components/navigation/*` · `AppShell.tsx`

---

## Three user flows (gate before M3.3)

### Public Flow
```
Главная (/site)
        ↓
Lite Vector (/site?view=vector)
        ↓
Услуги (/services)
        ↓
Скачать приложение (/site#download)
```

### Client Flow
```
Компания (/site)
        ↓
Vector (/site?view=vector)
        ↓
Проекты (/projects)  ← client shell
        ↓
Результат (проект готов)
```

### CEO Flow
```
Mission Control (/)
        ↓
Factory (/create)
        ↓
Finance (/finance)
        ↓
Стратегия (/company)
```

**Переход к M3.3** — CEO PASS на M3.2 ✅

---

## M3.3 — Public Website Slim (principles)

1. **Public — не урезанное приложение**, а законченный продукт знакомства. Lite Vector остаётся полезным.
2. **Каждая кнопка ведёт к следующему шагу** — человек не спрашивает «что дальше?»
3. **Public знакомит · Client работает** — новая фича: *должна жить в Public или в Client?*
4. **Без ощущения редиректа** — сначала демо, примеры, Lite Vector; установка — естественный следующий шаг.
5. **Gate (4 вопроса)** — см. `m3_3_gate` в registry; CEO PASS + **скриншоты глазами нового пользователя**.

### M3.3 gate

1. Понять продукт без установки?
2. Желание установить приложение?
3. Понятно Public vs Client?
4. Public не ощущается «сломанной» версией?

**После M3.3:** скриншоты Public Website — не как разработчик, а как новый посетитель.

---

## M3.3 — Public Website Slim ✅

**Done when:**
- `/site` — витрина знакомства (`PublicIntroTeaser`), не полный workspace
- Полный `ProjectPlatformShell` перенесён на `/projects` (client) — **без потери возможности**
- Funnel: Главная → Vector → Услуги → Установить
- `PublicFunnelFooter` — следующий шаг на каждом экране
- Download — позитивное «создайте компанию», не «здесь нет»

**Code:** `PublicIntroTeaser.tsx` · `publicFunnel.ts` · `SitePage.tsx` · `projects/page.tsx`

**\*M3.3 окончательный PASS** — только после **живого просмотра** витрины CEO (впечатление, не архитектура). Архитектурный PASS — принят.

---

## M3.4 — Client Workspace Primary (principles) — **самый важный этап Migration**

### Продуктовые принципы

1. **Public продаёт мечту**, не функции — уходит с мыслью *«Я могу построить свою цифровую компанию вместе с Vector»*, не *«ИИ для сайтов»*.
2. **Lite Vector удивляет** — за 2–3 сообщения: дружелюбие, понимание, естественность, желание продолжить. Не «обрезанный GPT».
3. **Все новые user-фичи → Client first.** Public: демо, описание, приглашение — не рабочая среда.
4. **Один Virtus Core** — Public → Client = *«перешёл на следующий уровень»*, не другое приложение (цвета, язык, Vector, стиль).
5. **Цель M3.4:** Vector в центре; проекты · файлы · результаты — **часть разговора с Vector**, не четыре отдельных раздела.

### Gate перед M3.5 (не технический аудит — сценарий нового клиента)

```
1. Скачать Virtus Core
2. Создать цифровую компанию
3. Познакомиться с Vector
4. Создать первый проект
5. Получить первый результат
```

Путь должен быть **естественным и приятным** — иначе M3.4 незавершён.

**CEO UI gate:** пройти каждый экран client app вместе; убрать «по-программистски».

---

## Current overlaps (intentional until M3.4 complete)

| Path | Now | Target |
|------|-----|--------|
| `/site` | Public + full Vector chat | Public = Lite; Client = full |
| `/projects` | CEO shell + client data | Client primary |
| `/order` | Public funnel | Public start → Client complete |
| `/create` | CEO Factory | Client co-create + CEO oversight |

---

*M3 Platform Separation · Virtus Core · 2026-07-11*
