# Virtus Core — Product Definition v1

**Status:** Product Definition v1 — **ACCEPTED · FINAL** (CEO PASS, 2026-07-11)  
**Purpose:** Describe what a **person sees and feels** — not code, not internal architecture.

**This document is the product foundation for M3–M7 (Platform Separation).**

**Related (frozen philosophy — do not rewrite):**
- `docs/VIRTUS_CORE_NORTH_STAR_DIRECTIVE.md` — Co-Creation, Vector as partner
- `docs/VIRTUS_COMMERCE_DELIVERY_DIRECTIVE.md` — ownership, payment after value
- `docs/VIRTUS_WORKSPACE_ARCHITECTURE_DIRECTIVE.md` — Platform / Workspace / Project
- `docs/DIGITAL_EMPLOYEE_STRATEGY.md` — Vector as digital employee

**Rule for every future feature:** *На каком этапе жизненного цикла клиента она помогает?*

**Change policy:** v1 changes only when CEO approves — not because a sprint needs a shortcut.

---

## What this document is

| Is | Is not |
|----|--------|
| Paths a human walks | Screen wireframes |
| Feelings and outcomes | API design |
| Words users hear | Module names |
| Foundation for M3–M7 | Implementation tasks |

---

# Главная цель продукта

**Virtus Core — это не AI-чат. Не генератор сайтов. Не CRM.**

Virtus Core — **операционная система цифровой компании**, где **Vector** является главным интерфейсом между человеком и системой.

```
Человек
   ↓
Vector (главный интерфейс)
   ↓
Проекты · Документы · Память · Услуги · (CRM, Marketplace — позже)
```

Все остальные модули существуют **только потому, что помогают Vector выполнять работу**.

Модули не конкурируют с Vector за внимание пользователя.

---

# North Star — главный критерий качества

Через год пользователь открывает Virtus Core **не потому, что ему нужен очередной AI**, а потому что он хочет **продолжить работу именно со своим Vector**.

Это главный ориентир для всех следующих решений — Product Reality, Platform Separation, Commerce.

**Success phrase:** *«Это мой Vector»* — not *«это хороший ИИ»*.

**Relationship goal:** не продажа подписки — **многолетние отношения** с цифровой компанией.

---

# 1. Public Website — витрина

**Role:** Вызвать желание **скачать приложение**. Сайт **не конкурирует** с приложением.

После просмотра сайта человек думает:

> **«Хочу установить Virtus Core.»**

**Separation test:** если человек может **полноценно работать** прямо на сайте — Platform Separation выполнена неправильно.

A visitor must **never** land in Mission Control, Factory, or a working company environment from the public site.

## New visitor path

```
Увидел ссылку / рекламу / рекомендацию
        ↓
Главная страница
        ↓
Понял: Virtus Core — операционная система цифровой компании (не чат, не генератор)
        ↓
Увидел: чем отличается от ChatGPT (Vector работает, не только отвечает)
        ↓
Примеры работ / кейсы
        ↓
Что умеет (услуги простым языком)
        ↓
Попробовал Lite Vector (вкус, не замена приложению)
        ↓
Тарифы
        ↓
FAQ · Поддержка
        ↓
«Скачать приложение» → Client Application
```

## Pages (content, not layout)

| Страница | Человек должен уйти с мыслью |
|----------|------------------------------|
| **Главная** | «Хочу установить — там моя компания» |
| **Что такое Virtus Core** | ОС цифровой компании; Vector — главный интерфейс |
| **vs ChatGPT** | ChatGPT отвечает. Virtus Core **работает** вместе со мной |
| **Что умеет** | Конкретные услуги простым языком |
| **Кейсы** | Разговор → результат → ценность |
| **Lite Vector** | Попробовать Vector — мост к приложению |
| **Тарифы** | Понятные уровни; оплата после ценности |
| **FAQ** | Без жаргона |
| **Скачать** | Одна главная цель страницы |

## Lite Vector (on website)

- Короткий разговор — **демо**, не полноценная работа
- Память минимальная; полная жизнь компании — только в приложении
- Всегда ведёт к установке: «Продолжим в приложении — там ваша компания»

## What must NOT be on Public Website

- Полноценный workspace · проекты · документы · CRM
- Mission Control · Factory · Finance · Growth
- Всё, из-за чего человек **не скачивает** приложение

---

# 2. Client Application — настоящий продукт

**Role:** Здесь человек **живёт каждый день**.

После установки пользователь чувствует:

> **«Я только что открыл свою компанию.»**

Не приложение. Не аккаунт. Не рабочее пространство. **Свою цифровую компанию.**

**Psychological bar:** *«Я открыл программу Virtus Core»* — not *«открыл сайт в браузере»*.

## First-time user path

```
Скачал / установил
        ↓
Открыл — нативное приложение
        ↓
Регистрация — одна цифровая компания
        ↓
Vector приветствует: «Добро пожаловать в вашу компанию»
        ↓
Разговор — свободный старт
        ↓
Проект рождается из диалога
        ↓
Совместная работа → видимый результат
        ↓
«Ваш проект готов»
        ↓
Купить проект · или · Продолжить развивать компанию
```

## Returning user path

```
Открыл приложение
        ↓
Vector: помнит, где остановились (естественно, без «откуда знает»)
        ↓
Любое действие — через ощущение, что Vector ведёт процесс
        ↓
Результат или следующий шаг компании
```

## What lives in Client Application

| Область | Ощущение |
|---------|----------|
| **Vector** | Главное лицо; всё начинается здесь |
| **Компания** | Моя цифровая компания |
| **Проекты** | Дела компании, не «модули системы» |
| **Память** | Vector помнит меня |
| **Документы** | Vector понял и использует |
| **Голос · Чат** | Разговор с сотрудником |

**Later:** CRM · Marketplace · автоматизация — Vector по-прежнему ведёт процесс.

## CEO UI gate (before M5 ship)

Пройти **каждый экран** с CEO. Убрать всё «по-программистски».

---

# 3. CEO Workspace — кабинет владельца

**Role:** Отдельное пространство **только для владельца** Virtus Core как компании.

CEO Workspace **не админ-панель**. Это **кабинет владельца компании**.

**Mission Control** — место **принятия решений**, не список технических страниц.

**Target (M7):** внутри приложения, без внешнего браузера.

## CEO daily path

```
Запустил программу (режим владельца)
        ↓
Mission Control — что важно сегодня, какие решения
        ↓
Компания — направление, не org-chart ради org-chart
        ↓
Финансы — честные цифры
        ↓
Factory — продукт для клиентов
        ↓
Vector — тот же Vector, контекст владельца
        ↓
Релизы · Стратегия
```

## Separation rule

| CEO | Customer never sees |
|-----|---------------------|
| Кабинет владельца, MC, Factory, Growth | ✓ |
| Customer's digital company | — | ✓ |

---

# 4. Vector — главное лицо продукта

Vector остаётся **главным лицом** Virtus Core на всех этапах.

**Любое действие пользователь начинает через Vector** — или ощущает, что Vector ведёт процесс.

Даже при открытии разделов **Проекты**, **Файлы**, **Маркетплейс**, **CRM**:

- пользователь не чувствует «отдельное приложение внутри приложения»;
- Vector присутствует в контексте: кто ведёт, что дальше, куда смотреть.

**Anti-pattern:** набор несвязанных модулей с разными «голосами» и логикой.

**Pattern:** одна компания · один Vector · модули — инструменты Vector для работы.

---

# 5. Universal Identity — один человек, все устройства

```
Windows → Android → iPhone → Mac → (Web — лёгкий доступ)
        ↓
Везде: одна цифровая компания · один Vector · одна память
```

- Один аккаунт — одна цифровая компания
- Без ручной синхронизации и вторых аккаунтов
- Устройство = способ доступа

**After M7**, before Commerce expansion.

---

# 6. Product Philosophy — правила продукта

| # | Rule |
|---|------|
| 1 | Virtus Core — **ОС цифровой компании**; Vector — главный интерфейс |
| 2 | Модули существуют, чтобы **Vector мог работать** |
| 3 | Vector — **цифровой сотрудник**, не чат-бот |
| 4 | Проект рождается из **разговора** |
| 5 | Платёж — **после ценности** |
| 6 | Один аккаунт — **одна цифровая компания** |
| 7 | Пользователь **не видит** внутренние модели ИИ |
| 8 | **Простые слова**, не технические термины |
| 9 | **Нативное приложение**, не сайт |
| 10 | Новая функция — только если **реальному пользователю лучше** |
| 11 | Цель — **многолетние отношения**, не продажа подписки |

---

# 7. Customer Lifecycle — полный путь клиента

**Feature gate:** *На каком этапе жизненного цикла клиента она помогает?*

## Full journey

```
Увидел рекламу / рекомендацию
        ↓
Зашёл на сайт → «Хочу установить»
        ↓
Попробовал Lite Vector
        ↓
Скачал приложение
        ↓
Создал цифровую компанию
        ↓
Первый разговор с Vector
        ↓
Первый проект → первый результат
        ↓
Получил результат
        ↓
Доверяет Vector
        ↓
Возвращается регулярно
        ↓
Professional → Business (когда готово)
        ↓
Рекомендует Virtus Core другим
        ↓
Строит бизнес вместе с Virtus Core годами
```

## Lifecycle stages

| Stage | Human state | Product job |
|-------|-------------|-------------|
| **Discover** | «Что это?» | Витрина → желание установить |
| **Try** | «Попробую» | Lite Vector → мост к приложению |
| **Adopt** | «Открыл свою компанию» | Первый диалог с Vector |
| **First value** | «Получил результат» | Видимый итог проекта |
| **Trust** | «Доверяю Vector» | Память, естественность, без «бота» |
| **Habit** | «Возвращаюсь регулярно» | Продолжение без объяснений заново |
| **Grow** | «Компания растёт» | Новые услуги через Vector |
| **Advocate** | «Рассказываю другим» | Кейсы, рекомендации |
| **Partnership** | «Годы вместе» | Многолетние отношения, не churn |

**North Star stage:** через год открывает, чтобы **продолжить со своим Vector**.

---

# Development order

```
Product Reality (live use)              ← параллельно, фоном
        ↓
Product Definition v1 — ACCEPTED        ← THIS DOCUMENT
        ↓
M3  Public / Client / CEO separation
M4  Website = showcase only (download desire)
M5  Client Application = company home
M6  Client API + sync
M7  CEO Workspace inside app (owner's office)
        ↓
Universal Identity
        ↓
Commerce layer
```

**M3–M7 implement this document — not screen moves.**

---

*Product Definition v1 · ACCEPTED FINAL · Virtus Core · 2026-07-11*
