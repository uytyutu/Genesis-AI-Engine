# Mission 1 — Dogfooding Guide (Cursor as Test Manager)

**Type:** Product / QA · **NOT** governance  
**Status:** Active — CEO executes, Cursor guides step-by-step  
**Date:** 2026-07-05  
**Results file:** `Mission1_Release_Readiness_Results.md`

---

## How this works

Cursor (or any guide) reads **one step at a time**. CEO performs the action, marks **PASS / FAIL**, then moves on.

**Do not skip ahead on FAIL** — fix or document BLOCKED, then retry the step.

**Scenario A (primary):** New client orders a **café website** via Concierge → order → status.

**Scenario B (optional):** Visitor wants **Genesis Studio** — no forced service path.

---

## Stage 2 — Scenario A: Café website

### Welcome

> **Добро пожаловать в этап Dogfooding.**
>
> Сегодня проверяем путь **нового клиента**, который хочет сайт для кафе.
>
> Вы — не разработчик. Вы владелец кафе.
>
> Цель: от `/site` до предложения оформить заказ — без путаницы и без преждевременного `/order`.

---

### Step 1 — Открыть сайт

**Действие:** Открой `http://localhost:3000/site` (или production URL).

**Ожидаемый результат:**

- [ ] Страница загрузилась **менее чем за 5 секунд** (CEO machine)
- [ ] AI Concierge виден **сразу**, не под длинным текстом
- [ ] Заголовок: «Расскажите, что вы хотите создать…»
- [ ] Нет ошибок в интерфейсе (консоль браузера — по желанию)

**Запись:** A1 → PASS / FAIL / BLOCKED  
**Если PASS** → Step 2. **Если FAIL** → опиши что не так, исправь, повтори Step 1.

---

### Step 2 — Первое впечатление (2 минуты)

**Действие:** Не нажимай ничего 30 секунд. Прочитай экран глазами «человека с улицы».

**Ожидаемый результат:**

- [ ] Понятно: можно **написать задачу**, а не только читать прайс
- [ ] Видны быстрые подсказки (🏪🍽️🚗… ✨ Studio)
- [ ] Нет желания «сразу закрыть вкладку»

**Запись:** B1, B7 → PASS / FAIL  
**Если PASS** → Step 3.

---

### Step 3 — Запрос «сайт для кафе»

**Действие:** Нажми **🍽️ Сайт кафе** или введи: `Мне нужен сайт для кафе`

**Ожидаемый результат:**

- [ ] Genesis AI отвечает за **&lt; 5 сек** (не пустой экран, не «думает» бесконечно)
- [ ] Ответ живой: «Конечно…» + **первый вопрос** (тип кафе: кофейня, ресторан…)
- [ ] **Нет** кнопки «Оформить заказ» на первом ответе
- [ ] **Нет** навязывания Genesis Studio
- [ ] В шапке чата: **Genesis AI** (не «Concierge»)
- [ ] Если настроен `GENESIS_LLM_API_KEY` — индикатор «полный ИИ»

**Запись:** C2 → PASS / FAIL  
**Если FAIL «нет ответа»** → Genesis запущен? Backend :8000? `GET /api/public/genesis-ai/status`

---

### Step 4 — Консультация (3–4 ответа)

**Действие:** Ответь на вопросы Genesis, например:

1. Страницы: `3–5 страниц`
2. Оплата: `Нет, не нужна`
3. Логотип: `Да, есть`

**Ожидаемый результат:**

- [ ] Диалог **пошаговый**, один вопрос за раз (или логичная цепочка)
- [ ] После ответов — **предварительная стоимость** в €
- [ ] Указан **срок** (например 5–14 дней)
- [ ] Спрос: «Хотите оформить заказ?» — **без** ссылки на `/order` пока вы не согласились

**Запись:** C11, C12 → PASS / FAIL

---

### Step 5 — Согласие на заказ

**Действие:** Напиши: `Да, оформить`

**Ожидаемый результат:**

- [ ] Появляется кнопка **«Оформить заказ»**
- [ ] Ссылка ведёт на `/order` (желательно с `?package=…`)
- [ ] До этого шага кнопки заказа **не было**

**Запись:** C13 → PASS / FAIL  
**Если PASS** → Step 6.

---

### Step 6 — Форма заказа

**Действие:** Нажми «Оформить заказ». Заполни тестовые данные.

**Ожидаемый результат:**

- [ ] `/order` открывается, форма читаема
- [ ] Цена пакета видна **до** оплаты
- [ ] Валидация пустой формы — понятные ошибки
- [ ] Тестовый заказ создаётся → экран подтверждения + ID

**Запись:** D1, D6, D7, D8 → PASS / FAIL

---

### Step 7 — Статус и Mission Control

**Действие:** Открой статус заказа. Затем Mission Control (`/`).

**Ожидаемый результат:**

- [ ] Статус заказа загружается
- [ ] В Mission Control заказ **виден** (не фейк)
- [ ] Revenue / метрики не врут (0 € если не платили)

**Запись:** D10, E4, E10 → PASS / FAIL

---

### Step 8 — Мобильная ширина (повтор ключевых шагов)

**Действие:** DevTools → 375px. Повтори Step 3–5 кратко.

**Ожидаемый результат:**

- [ ] Concierge usable, нет горизонтального скролла
- [ ] Кнопки и ввод нажимаются пальцем

**Запись:** A7, D11 → PASS / FAIL

---

### Scenario A — Exit

**Stage 2 Scenario A complete when:**

- [ ] Steps 1–8 critical items PASS
- [ ] Critical customer path (Results file) PASS

Then: optional Scenario B, then Stage 3 beta.

---

## Stage 2 — Scenario B: Genesis Studio (optional, 5 min)

### Step B1 — Запрос Studio

**Действие:** Новый диалог на `/site` (обнови страницу). Нажми **✨ Genesis Studio** или напиши: `Хочу пользоваться Genesis Studio`

**Ожидаемый результат:**

- [ ] Ответ про **платформу**, не про «сначала закажите сайт»
- [ ] Упоминание экосистемы / ориентира €299/мес
- [ ] **Нет** принудительного CTA на `/order` для услуги

**Запись:** (новая строка в Notes) Studio intent → PASS / FAIL

---

## When Cursor guides CEO

Cursor should:

1. Paste **only the current step** (not the whole checklist).
2. Ask: «PASS или FAIL?»
3. On PASS → next step automatically.
4. On FAIL → help fix **one** issue, retry same step.
5. Never recommend Gewerbe / public pay until Stage 1 compact checklist + Stage 2 done.

---

## Quick reference — what changed (2026-07-05)

| Old behaviour | New behaviour |
|---------------|---------------|
| Cafe → instant `/order` | Consultation → quote → order after YES |
| Studio only after service | Studio when **intent** is platform |
| Rigid sales script | Intent routing: service **or** Studio |

---

*Full matrix: `Mission1_Release_Readiness_Checklist.md` · Sales rules: `Mission1_Autonomous_Sales_Experience_v1.md`*
